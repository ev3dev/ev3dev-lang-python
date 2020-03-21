# -----------------------------------------------------------------------------
# Copyright (c) 2015 Ralph Hempel <rhempel@hempeldesigngroup.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -----------------------------------------------------------------------------

import sys
import math
import select
import time
import _thread

# python3 uses collections
# micropython uses ucollections
try:
    from collections import OrderedDict
except ImportError:
    from ucollections import OrderedDict

from logging import getLogger
from os.path import abspath
from ev3dev2 import get_current_platform, Device, list_device_names, DeviceNotDefined, ThreadNotRunning
from ev3dev2.stopwatch import StopWatch

# OUTPUT ports have platform specific values that we must import
platform = get_current_platform()

if platform == 'ev3':
    from ev3dev2._platform.ev3 import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D  # noqa: F401

elif platform == 'evb':
    from ev3dev2._platform.evb import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D  # noqa: F401

elif platform == 'pistorms':
    from ev3dev2._platform.pistorms import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D  # noqa: F401

elif platform == 'brickpi':
    from ev3dev2._platform.brickpi import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D  # noqa: F401

elif platform == 'brickpi3':
    from ev3dev2._platform.brickpi3 import (  # noqa: F401
        OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D, OUTPUT_E, OUTPUT_F, OUTPUT_G, OUTPUT_H, OUTPUT_I, OUTPUT_J, OUTPUT_K,
        OUTPUT_L, OUTPUT_M, OUTPUT_N, OUTPUT_O, OUTPUT_P)

elif platform == 'fake':
    from ev3dev2._platform.fake import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D  # noqa: F401

else:
    raise Exception("Unsupported platform '%s'" % platform)

if sys.version_info < (3, 4):
    raise SystemError('Must be using Python 3.4 or higher')

log = getLogger(__name__)

# The number of milliseconds we wait for the state of a motor to
# update to 'running' in the "on_for_XYZ" methods of the Motor class
WAIT_RUNNING_TIMEOUT = 100


class SpeedInvalid(ValueError):
    pass


class SpeedValue(object):
    """
    A base class for other unit types. Don't use this directly; instead, see
    :class:`SpeedPercent`, :class:`SpeedRPS`, :class:`SpeedRPM`,
    :class:`SpeedDPS`, and :class:`SpeedDPM`.
    """
    def __eq__(self, other):
        return self.to_native_units() == other.to_native_units()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.to_native_units() < other.to_native_units()

    def __le__(self, other):
        return self.to_native_units() <= other.to_native_units()

    def __gt__(self, other):
        return self.to_native_units() > other.to_native_units()

    def __ge__(self, other):
        return self.to_native_units() >= other.to_native_units()

    def __rmul__(self, other):
        return self.__mul__(other)


class SpeedPercent(SpeedValue):
    """
    Speed as a percentage of the motor's maximum rated speed.
    """
    def __init__(self, percent, desc=None):
        if percent < -100 or percent > 100:
            raise SpeedInvalid("invalid percentage {}, must be between -100 and 100 (inclusive)".format(percent))
        self.percent = percent
        self.desc = desc

    def __str__(self):
        return "{} ".format(self.desc) if self.desc else "" + str(self.percent) + "%"

    def __mul__(self, other):
        assert isinstance(other, (float, int)), "{} can only be multiplied by an int or float".format(self)
        return SpeedPercent(self.percent * other)

    def to_native_units(self, motor):
        """
        Return this SpeedPercent in native motor units
        """
        return self.percent / 100 * motor.max_speed


class SpeedNativeUnits(SpeedValue):
    """
    Speed in tacho counts per second.
    """
    def __init__(self, native_counts, desc=None):
        self.native_counts = native_counts
        self.desc = desc

    def __str__(self):
        return "{} ".format(self.desc) if self.desc else "" + "{:.2f}".format(self.native_counts) + " counts/sec"

    def __mul__(self, other):
        assert isinstance(other, (float, int)), "{} can only be multiplied by an int or float".format(self)
        return SpeedNativeUnits(self.native_counts * other)

    def to_native_units(self, motor=None):
        """
        Return this SpeedNativeUnits as a number
        """
        if self.native_counts > motor.max_speed:
            raise SpeedInvalid("invalid native-units: {} max speed {}, {} was requested".format(
                motor, motor.max_speed, self.native_counts))
        return self.native_counts


class SpeedRPS(SpeedValue):
    """
    Speed in rotations-per-second.
    """
    def __init__(self, rotations_per_second, desc=None):
        self.rotations_per_second = rotations_per_second
        self.desc = desc

    def __str__(self):
        return "{} ".format(self.desc) if self.desc else "" + str(self.rotations_per_second) + " rot/sec"

    def __mul__(self, other):
        assert isinstance(other, (float, int)), "{} can only be multiplied by an int or float".format(self)
        return SpeedRPS(self.rotations_per_second * other)

    def to_native_units(self, motor):
        """
        Return the native speed measurement required to achieve desired rotations-per-second
        """
        if abs(self.rotations_per_second) > motor.max_rps:
            raise SpeedInvalid("invalid rotations-per-second: {} max RPS is {}, {} was requested".format(
                motor, motor.max_rps, self.rotations_per_second))
        return self.rotations_per_second / motor.max_rps * motor.max_speed


class SpeedRPM(SpeedValue):
    """
    Speed in rotations-per-minute.
    """
    def __init__(self, rotations_per_minute, desc=None):
        self.rotations_per_minute = rotations_per_minute
        self.desc = desc

    def __str__(self):
        return "{} ".format(self.desc) if self.desc else "" + str(self.rotations_per_minute) + " rot/min"

    def __mul__(self, other):
        assert isinstance(other, (float, int)), "{} can only be multiplied by an int or float".format(self)
        return SpeedRPM(self.rotations_per_minute * other)

    def to_native_units(self, motor):
        """
        Return the native speed measurement required to achieve desired rotations-per-minute
        """
        if abs(self.rotations_per_minute) > motor.max_rpm:
            raise SpeedInvalid("invalid rotations-per-minute: {} max RPM is {}, {} was requested".format(
                motor, motor.max_rpm, self.rotations_per_minute))
        return self.rotations_per_minute / motor.max_rpm * motor.max_speed


class SpeedDPS(SpeedValue):
    """
    Speed in degrees-per-second.
    """
    def __init__(self, degrees_per_second, desc=None):
        self.degrees_per_second = degrees_per_second
        self.desc = desc

    def __str__(self):
        return "{} ".format(self.desc) if self.desc else "" + str(self.degrees_per_second) + " deg/sec"

    def __mul__(self, other):
        assert isinstance(other, (float, int)), "{} can only be multiplied by an int or float".format(self)
        return SpeedDPS(self.degrees_per_second * other)

    def to_native_units(self, motor):
        """
        Return the native speed measurement required to achieve desired degrees-per-second
        """
        if abs(self.degrees_per_second) > motor.max_dps:
            raise SpeedInvalid("invalid degrees-per-second: {} max DPS is {}, {} was requested".format(
                motor, motor.max_dps, self.degrees_per_second))
        return self.degrees_per_second / motor.max_dps * motor.max_speed


class SpeedDPM(SpeedValue):
    """
    Speed in degrees-per-minute.
    """
    def __init__(self, degrees_per_minute, desc=None):
        self.degrees_per_minute = degrees_per_minute
        self.desc = desc

    def __str__(self):
        return "{} ".format(self.desc) if self.desc else "" + str(self.degrees_per_minute) + " deg/min"

    def __mul__(self, other):
        assert isinstance(other, (float, int)), "{} can only be multiplied by an int or float".format(self)
        return SpeedDPM(self.degrees_per_minute * other)

    def to_native_units(self, motor):
        """
        Return the native speed measurement required to achieve desired degrees-per-minute
        """
        if abs(self.degrees_per_minute) > motor.max_dpm:
            raise SpeedInvalid("invalid degrees-per-minute: {} max DPM is {}, {} was requested".format(
                motor, motor.max_dpm, self.degrees_per_minute))
        return self.degrees_per_minute / motor.max_dpm * motor.max_speed


def speed_to_speedvalue(speed, desc=None):
    """
    If ``speed`` is not a ``SpeedValue`` object, treat it as a percentage.
    Returns a ``SpeedValue`` object.
    """
    if isinstance(speed, SpeedValue):
        return speed
    else:
        return SpeedPercent(speed, desc)


class Motor(Device):
    """
    The motor class provides a uniform interface for using motors with
    positional and directional feedback such as the EV3 and NXT motors.
    This feedback allows for precise control of the motors. This is the
    most common type of motor, so we just call it ``motor``.
    """

    SYSTEM_CLASS_NAME = 'tacho-motor'
    SYSTEM_DEVICE_NAME_CONVENTION = '*'

    __slots__ = [
        '_address',
        '_command',
        '_commands',
        '_count_per_rot',
        '_count_per_m',
        '_driver_name',
        '_duty_cycle',
        '_duty_cycle_sp',
        '_full_travel_count',
        '_polarity',
        '_position',
        '_position_p',
        '_position_i',
        '_position_d',
        '_position_sp',
        '_max_speed',
        '_speed',
        '_speed_sp',
        '_ramp_up_sp',
        '_ramp_down_sp',
        '_speed_p',
        '_speed_i',
        '_speed_d',
        '_state',
        '_stop_action',
        '_stop_actions',
        '_time_sp',
        '_poll',
        'max_rps',
        'max_rpm',
        'max_dps',
        'max_dpm',
    ]

    #: Run the motor until another command is sent.
    COMMAND_RUN_FOREVER = 'run-forever'

    #: Run to an absolute position specified by ``position_sp`` and then
    #: stop using the action specified in ``stop_action``.
    COMMAND_RUN_TO_ABS_POS = 'run-to-abs-pos'

    #: Run to a position relative to the current ``position`` value.
    #: The new position will be current ``position`` + ``position_sp``.
    #: When the new position is reached, the motor will stop using
    #: the action specified by ``stop_action``.
    COMMAND_RUN_TO_REL_POS = 'run-to-rel-pos'

    #: Run the motor for the amount of time specified in ``time_sp``
    #: and then stop the motor using the action specified by ``stop_action``.
    COMMAND_RUN_TIMED = 'run-timed'

    #: Run the motor at the duty cycle specified by ``duty_cycle_sp``.
    #: Unlike other run commands, changing ``duty_cycle_sp`` while running *will*
    #: take effect immediately.
    COMMAND_RUN_DIRECT = 'run-direct'

    #: Stop any of the run commands before they are complete using the
    #: action specified by ``stop_action``.
    COMMAND_STOP = 'stop'

    #: Reset all of the motor parameter attributes to their default value.
    #: This will also have the effect of stopping the motor.
    COMMAND_RESET = 'reset'

    #: Sets the normal polarity of the rotary encoder.
    ENCODER_POLARITY_NORMAL = 'normal'

    #: Sets the inversed polarity of the rotary encoder.
    ENCODER_POLARITY_INVERSED = 'inversed'

    #: With ``normal`` polarity, a positive duty cycle will
    #: cause the motor to rotate clockwise.
    POLARITY_NORMAL = 'normal'

    #: With ``inversed`` polarity, a positive duty cycle will
    #: cause the motor to rotate counter-clockwise.
    POLARITY_INVERSED = 'inversed'

    #: Power is being sent to the motor.
    STATE_RUNNING = 'running'

    #: The motor is ramping up or down and has not yet reached a constant output level.
    STATE_RAMPING = 'ramping'

    #: The motor is not turning, but rather attempting to hold a fixed position.
    STATE_HOLDING = 'holding'

    #: The motor is turning, but cannot reach its ``speed_sp``.
    STATE_OVERLOADED = 'overloaded'

    #: The motor is not turning when it should be.
    STATE_STALLED = 'stalled'

    #: Power will be removed from the motor and it will freely coast to a stop.
    STOP_ACTION_COAST = 'coast'

    #: Power will be removed from the motor and a passive electrical load will
    #: be placed on the motor. This is usually done by shorting the motor terminals
    #: together. This load will absorb the energy from the rotation of the motors and
    #: cause the motor to stop more quickly than coasting.
    STOP_ACTION_BRAKE = 'brake'

    #: Does not remove power from the motor. Instead it actively try to hold the motor
    #: at the current position. If an external force tries to turn the motor, the motor
    #: will ``push back`` to maintain its position.
    STOP_ACTION_HOLD = 'hold'

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        if platform in ('brickpi', 'brickpi3') and type(self).__name__ != 'Motor' and not isinstance(self, LargeMotor):
            raise Exception("{} is unaware of different motor types, use LargeMotor instead".format(platform))

        if address is not None:
            kwargs['address'] = address
        super(Motor, self).__init__(self.SYSTEM_CLASS_NAME, name_pattern, name_exact, **kwargs)

        self._address = None
        self._command = None
        self._commands = None
        self._count_per_rot = None
        self._count_per_m = None
        self._driver_name = None
        self._duty_cycle = None
        self._duty_cycle_sp = None
        self._full_travel_count = None
        self._polarity = None
        self._position = None
        self._position_p = None
        self._position_i = None
        self._position_d = None
        self._position_sp = None
        self._max_speed = None
        self._speed = None
        self._speed_sp = None
        self._ramp_up_sp = None
        self._ramp_down_sp = None
        self._speed_p = None
        self._speed_i = None
        self._speed_d = None
        self._state = None
        self._stop_action = None
        self._stop_actions = None
        self._time_sp = None
        self._poll = None
        self.max_rps = float(self.max_speed / self.count_per_rot)
        self.max_rpm = self.max_rps * 60
        self.max_dps = self.max_rps * 360
        self.max_dpm = self.max_rpm * 360

    @property
    def address(self):
        """
        Returns the name of the port that this motor is connected to.
        """
        self._address, value = self.get_attr_string(self._address, 'address')
        return value

    @property
    def command(self):
        """
        Sends a command to the motor controller. See ``commands`` for a list of
        possible values.
        """
        raise Exception("command is a write-only property!")

    @command.setter
    def command(self, value):
        self._command = self.set_attr_string(self._command, 'command', value)

    @property
    def commands(self):
        """
        Returns a list of commands that are supported by the motor
        controller. Possible values are ``run-forever``, ``run-to-abs-pos``, ``run-to-rel-pos``,
        ``run-timed``, ``run-direct``, ``stop`` and ``reset``. Not all commands may be supported.

        - ``run-forever`` will cause the motor to run until another command is sent.
        - ``run-to-abs-pos`` will run to an absolute position specified by ``position_sp``
          and then stop using the action specified in ``stop_action``.
        - ``run-to-rel-pos`` will run to a position relative to the current ``position`` value.
          The new position will be current ``position`` + ``position_sp``. When the new
          position is reached, the motor will stop using the action specified by ``stop_action``.
        - ``run-timed`` will run the motor for the amount of time specified in ``time_sp``
          and then stop the motor using the action specified by ``stop_action``.
        - ``run-direct`` will run the motor at the duty cycle specified by ``duty_cycle_sp``.
          Unlike other run commands, changing ``duty_cycle_sp`` while running *will*
          take effect immediately.
        - ``stop`` will stop any of the run commands before they are complete using the
          action specified by ``stop_action``.
        - ``reset`` will reset all of the motor parameter attributes to their default value.
          This will also have the effect of stopping the motor.
        """
        (self._commands, value) = self.get_cached_attr_set(self._commands, 'commands')
        return value

    @property
    def count_per_rot(self):
        """
        Returns the number of tacho counts in one rotation of the motor. Tacho counts
        are used by the position and speed attributes, so you can use this value
        to convert rotations or degrees to tacho counts. (rotation motors only)
        """
        (self._count_per_rot, value) = self.get_cached_attr_int(self._count_per_rot, 'count_per_rot')
        return value

    @property
    def count_per_m(self):
        """
        Returns the number of tacho counts in one meter of travel of the motor. Tacho
        counts are used by the position and speed attributes, so you can use this
        value to convert from distance to tacho counts. (linear motors only)
        """
        (self._count_per_m, value) = self.get_cached_attr_int(self._count_per_m, 'count_per_m')
        return value

    @property
    def driver_name(self):
        """
        Returns the name of the driver that provides this tacho motor device.
        """
        (self._driver_name, value) = self.get_cached_attr_string(self._driver_name, 'driver_name')
        return value

    @property
    def duty_cycle(self):
        """
        Returns the current duty cycle of the motor. Units are percent. Values
        are -100 to 100.
        """
        self._duty_cycle, value = self.get_attr_int(self._duty_cycle, 'duty_cycle')
        return value

    @property
    def duty_cycle_sp(self):
        """
        Writing sets the duty cycle setpoint. Reading returns the current value.
        Units are in percent. Valid values are -100 to 100. A negative value causes
        the motor to rotate in reverse.
        """
        self._duty_cycle_sp, value = self.get_attr_int(self._duty_cycle_sp, 'duty_cycle_sp')
        return value

    @duty_cycle_sp.setter
    def duty_cycle_sp(self, value):
        self._duty_cycle_sp = self.set_attr_int(self._duty_cycle_sp, 'duty_cycle_sp', value)

    @property
    def full_travel_count(self):
        """
        Returns the number of tacho counts in the full travel of the motor. When
        combined with the ``count_per_m`` atribute, you can use this value to
        calculate the maximum travel distance of the motor. (linear motors only)
        """
        (self._full_travel_count, value) = self.get_cached_attr_int(self._full_travel_count, 'full_travel_count')
        return value

    @property
    def polarity(self):
        """
        Sets the polarity of the motor. With ``normal`` polarity, a positive duty
        cycle will cause the motor to rotate clockwise. With ``inversed`` polarity,
        a positive duty cycle will cause the motor to rotate counter-clockwise.
        Valid values are ``normal`` and ``inversed``.
        """
        self._polarity, value = self.get_attr_string(self._polarity, 'polarity')
        return value

    @polarity.setter
    def polarity(self, value):
        self._polarity = self.set_attr_string(self._polarity, 'polarity', value)

    @property
    def position(self):
        """
        Returns the current position of the motor in pulses of the rotary
        encoder. When the motor rotates clockwise, the position will increase.
        Likewise, rotating counter-clockwise causes the position to decrease.
        Writing will set the position to that value.
        """
        self._position, value = self.get_attr_int(self._position, 'position')
        return value

    @position.setter
    def position(self, value):
        self._position = self.set_attr_int(self._position, 'position', value)

    @property
    def position_p(self):
        """
        The proportional constant for the position PID.
        """
        self._position_p, value = self.get_attr_int(self._position_p, 'hold_pid/Kp')
        return value

    @position_p.setter
    def position_p(self, value):
        self._position_p = self.set_attr_int(self._position_p, 'hold_pid/Kp', value)

    @property
    def position_i(self):
        """
        The integral constant for the position PID.
        """
        self._position_i, value = self.get_attr_int(self._position_i, 'hold_pid/Ki')
        return value

    @position_i.setter
    def position_i(self, value):
        self._position_i = self.set_attr_int(self._position_i, 'hold_pid/Ki', value)

    @property
    def position_d(self):
        """
        The derivative constant for the position PID.
        """
        self._position_d, value = self.get_attr_int(self._position_d, 'hold_pid/Kd')
        return value

    @position_d.setter
    def position_d(self, value):
        self._position_d = self.set_attr_int(self._position_d, 'hold_pid/Kd', value)

    @property
    def position_sp(self):
        """
        Writing specifies the target position for the ``run-to-abs-pos`` and ``run-to-rel-pos``
        commands. Reading returns the current value. Units are in tacho counts. You
        can use the value returned by ``count_per_rot`` to convert tacho counts to/from
        rotations or degrees.
        """
        self._position_sp, value = self.get_attr_int(self._position_sp, 'position_sp')
        return value

    @position_sp.setter
    def position_sp(self, value):
        self._position_sp = self.set_attr_int(self._position_sp, 'position_sp', value)

    @property
    def max_speed(self):
        """
        Returns the maximum value that is accepted by the ``speed_sp`` attribute. This
        may be slightly different than the maximum speed that a particular motor can
        reach - it's the maximum theoretical speed.
        """
        (self._max_speed, value) = self.get_cached_attr_int(self._max_speed, 'max_speed')
        return value

    @property
    def speed(self):
        """
        Returns the current motor speed in tacho counts per second. Note, this is
        not necessarily degrees (although it is for LEGO motors). Use the ``count_per_rot``
        attribute to convert this value to RPM or deg/sec.
        """
        self._speed, value = self.get_attr_int(self._speed, 'speed')
        return value

    @property
    def speed_sp(self):
        """
        Writing sets the target speed in tacho counts per second used for all ``run-*``
        commands except ``run-direct``. Reading returns the current value. A negative
        value causes the motor to rotate in reverse with the exception of ``run-to-*-pos``
        commands where the sign is ignored. Use the ``count_per_rot`` attribute to convert
        RPM or deg/sec to tacho counts per second. Use the ``count_per_m`` attribute to
        convert m/s to tacho counts per second.
        """
        self._speed_sp, value = self.get_attr_int(self._speed_sp, 'speed_sp')
        return value

    @speed_sp.setter
    def speed_sp(self, value):
        self._speed_sp = self.set_attr_int(self._speed_sp, 'speed_sp', value)

    @property
    def ramp_up_sp(self):
        """
        Writing sets the ramp up setpoint. Reading returns the current value. Units
        are in milliseconds and must be positive. When set to a non-zero value, the
        motor speed will increase from 0 to 100% of ``max_speed`` over the span of this
        setpoint. The actual ramp time is the ratio of the difference between the
        ``speed_sp`` and the current ``speed`` and max_speed multiplied by ``ramp_up_sp``.
        """
        self._ramp_up_sp, value = self.get_attr_int(self._ramp_up_sp, 'ramp_up_sp')
        return value

    @ramp_up_sp.setter
    def ramp_up_sp(self, value):
        self._ramp_up_sp = self.set_attr_int(self._ramp_up_sp, 'ramp_up_sp', value)

    @property
    def ramp_down_sp(self):
        """
        Writing sets the ramp down setpoint. Reading returns the current value. Units
        are in milliseconds and must be positive. When set to a non-zero value, the
        motor speed will decrease from 0 to 100% of ``max_speed`` over the span of this
        setpoint. The actual ramp time is the ratio of the difference between the
        ``speed_sp`` and the current ``speed`` and max_speed multiplied by ``ramp_down_sp``.
        """
        self._ramp_down_sp, value = self.get_attr_int(self._ramp_down_sp, 'ramp_down_sp')
        return value

    @ramp_down_sp.setter
    def ramp_down_sp(self, value):
        self._ramp_down_sp = self.set_attr_int(self._ramp_down_sp, 'ramp_down_sp', value)

    @property
    def speed_p(self):
        """
        The proportional constant for the speed regulation PID.
        """
        self._speed_p, value = self.get_attr_int(self._speed_p, 'speed_pid/Kp')
        return value

    @speed_p.setter
    def speed_p(self, value):
        self._speed_p = self.set_attr_int(self._speed_p, 'speed_pid/Kp', value)

    @property
    def speed_i(self):
        """
        The integral constant for the speed regulation PID.
        """
        self._speed_i, value = self.get_attr_int(self._speed_i, 'speed_pid/Ki')
        return value

    @speed_i.setter
    def speed_i(self, value):
        self._speed_i = self.set_attr_int(self._speed_i, 'speed_pid/Ki', value)

    @property
    def speed_d(self):
        """
        The derivative constant for the speed regulation PID.
        """
        self._speed_d, value = self.get_attr_int(self._speed_d, 'speed_pid/Kd')
        return value

    @speed_d.setter
    def speed_d(self, value):
        self._speed_d = self.set_attr_int(self._speed_d, 'speed_pid/Kd', value)

    @property
    def state(self):
        """
        Reading returns a list of state flags. Possible flags are
        ``running``, ``ramping``, ``holding``, ``overloaded`` and ``stalled``.
        """
        self._state, value = self.get_attr_set(self._state, 'state')
        return value

    @property
    def stop_action(self):
        """
        Reading returns the current stop action. Writing sets the stop action.
        The value determines the motors behavior when ``command`` is set to ``stop``.
        Also, it determines the motors behavior when a run command completes. See
        ``stop_actions`` for a list of possible values.
        """
        self._stop_action, value = self.get_attr_string(self._stop_action, 'stop_action')
        return value

    @stop_action.setter
    def stop_action(self, value):
        self._stop_action = self.set_attr_string(self._stop_action, 'stop_action', value)

    @property
    def stop_actions(self):
        """
        Returns a list of stop actions supported by the motor controller.
        Possible values are ``coast``, ``brake`` and ``hold``. ``coast`` means that power will
        be removed from the motor and it will freely coast to a stop. ``brake`` means
        that power will be removed from the motor and a passive electrical load will
        be placed on the motor. This is usually done by shorting the motor terminals
        together. This load will absorb the energy from the rotation of the motors and
        cause the motor to stop more quickly than coasting. ``hold`` does not remove
        power from the motor. Instead it actively tries to hold the motor at the current
        position. If an external force tries to turn the motor, the motor will 'push
        back' to maintain its position.
        """
        (self._stop_actions, value) = self.get_cached_attr_set(self._stop_actions, 'stop_actions')
        return value

    @property
    def time_sp(self):
        """
        Writing specifies the amount of time the motor will run when using the
        ``run-timed`` command. Reading returns the current value. Units are in
        milliseconds.
        """
        self._time_sp, value = self.get_attr_int(self._time_sp, 'time_sp')
        return value

    @time_sp.setter
    def time_sp(self, value):
        self._time_sp = self.set_attr_int(self._time_sp, 'time_sp', value)

    def run_forever(self, **kwargs):
        """
        Run the motor until another command is sent.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_FOREVER

    def run_to_abs_pos(self, **kwargs):
        """
        Run to an absolute position specified by ``position_sp`` and then
        stop using the action specified in ``stop_action``.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_TO_ABS_POS

    def run_to_rel_pos(self, **kwargs):
        """
        Run to a position relative to the current ``position`` value.
        The new position will be current ``position`` + ``position_sp``.
        When the new position is reached, the motor will stop using
        the action specified by ``stop_action``.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_TO_REL_POS

    def run_timed(self, **kwargs):
        """
        Run the motor for the amount of time specified in ``time_sp``
        and then stop the motor using the action specified by ``stop_action``.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_TIMED

    def run_direct(self, **kwargs):
        """
        Run the motor at the duty cycle specified by ``duty_cycle_sp``.
        Unlike other run commands, changing ``duty_cycle_sp`` while running *will*
        take effect immediately.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_DIRECT

    def stop(self, **kwargs):
        """
        Stop any of the run commands before they are complete using the
        action specified by ``stop_action``.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_STOP

    def reset(self, **kwargs):
        """
        Reset all of the motor parameter attributes to their default value.
        This will also have the effect of stopping the motor.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RESET

    @property
    def is_running(self):
        """
        Power is being sent to the motor.
        """
        return self.STATE_RUNNING in self.state

    @property
    def is_ramping(self):
        """
        The motor is ramping up or down and has not yet reached a constant output level.
        """
        return self.STATE_RAMPING in self.state

    @property
    def is_holding(self):
        """
        The motor is not turning, but rather attempting to hold a fixed position.
        """
        return self.STATE_HOLDING in self.state

    @property
    def is_overloaded(self):
        """
        The motor is turning, but cannot reach its ``speed_sp``.
        """
        return self.STATE_OVERLOADED in self.state

    @property
    def is_stalled(self):
        """
        The motor is not turning when it should be.
        """
        return self.STATE_STALLED in self.state

    def wait(self, cond, timeout=None):
        """
        Blocks until ``cond(self.state)`` is ``True``.  The condition is
        checked when there is an I/O event related to the ``state`` attribute.
        Exits early when ``timeout`` (in milliseconds) is reached.

        Returns ``True`` if the condition is met, and ``False`` if the timeout
        is reached.
        """

        tic = time.time()

        if self._poll is None:
            if self._state is None:
                self._state = self._attribute_file_open('state')
            self._poll = select.poll()
            self._poll.register(self._state, select.POLLPRI)

        # Set poll timeout to something small. For more details, see
        # https://github.com/ev3dev/ev3dev-lang-python/issues/583
        if timeout:
            poll_tm = min(timeout, 100)
        else:
            poll_tm = 100

        while True:
            # This check is now done every poll_tm even if poll has nothing to report:
            if cond(self.state):
                return True

            self._poll.poll(poll_tm)

            if timeout is not None and time.time() >= tic + timeout / 1000:
                # Final check when user timeout is reached
                return cond(self.state)

    def wait_until_not_moving(self, timeout=None):
        """
        Blocks until ``running`` is not in ``self.state`` or ``stalled`` is in
        ``self.state``.  The condition is checked when there is an I/O event
        related to the ``state`` attribute.  Exits early when ``timeout``
        (in milliseconds) is reached.

        Returns ``True`` if the condition is met, and ``False`` if the timeout
        is reached.

        Example::

            m.wait_until_not_moving()
        """
        return self.wait(lambda state: self.STATE_RUNNING not in state or self.STATE_STALLED in state, timeout)

    def wait_until(self, s, timeout=None):
        """
        Blocks until ``s`` is in ``self.state``.  The condition is checked when
        there is an I/O event related to the ``state`` attribute.  Exits early
        when ``timeout`` (in milliseconds) is reached.

        Returns ``True`` if the condition is met, and ``False`` if the timeout
        is reached.

        Example::

            m.wait_until('stalled')
        """
        return self.wait(lambda state: s in state, timeout)

    def wait_while(self, s, timeout=None):
        """
        Blocks until ``s`` is not in ``self.state``.  The condition is checked
        when there is an I/O event related to the ``state`` attribute.  Exits
        early when ``timeout`` (in milliseconds) is reached.

        Returns ``True`` if the condition is met, and ``False`` if the timeout
        is reached.

        Example::

            m.wait_while('running')
        """
        return self.wait(lambda state: s not in state, timeout)

    def _speed_native_units(self, speed, label=None):
        speed = speed_to_speedvalue(speed, label)
        return speed.to_native_units(self)

    def _set_rel_position_degrees_and_speed_sp(self, degrees, speed):
        degrees = degrees if speed >= 0 else -degrees
        speed = abs(speed)

        position_delta = int(round((degrees * self.count_per_rot) / 360))
        speed_sp = int(round(speed))

        self.position_sp = position_delta
        self.speed_sp = speed_sp

    def _set_brake(self, brake):
        if brake:
            self.stop_action = self.STOP_ACTION_HOLD
        else:
            self.stop_action = self.STOP_ACTION_COAST

    def on_for_rotations(self, speed, rotations, brake=True, block=True):
        """
        Rotate the motor at ``speed`` for ``rotations``

        ``speed`` can be a percentage or a :class:`ev3dev2.motor.SpeedValue`
        object, enabling use of other units.
        """
        speed_sp = self._speed_native_units(speed)
        self._set_rel_position_degrees_and_speed_sp(rotations * 360, speed_sp)
        self._set_brake(brake)
        self.run_to_rel_pos()

        if block:
            self.wait_until('running', timeout=WAIT_RUNNING_TIMEOUT)
            self.wait_until_not_moving()

    def on_for_degrees(self, speed, degrees, brake=True, block=True):
        """
        Rotate the motor at ``speed`` for ``degrees``

        ``speed`` can be a percentage or a :class:`ev3dev2.motor.SpeedValue`
        object, enabling use of other units.
        """
        speed_sp = self._speed_native_units(speed)
        self._set_rel_position_degrees_and_speed_sp(degrees, speed_sp)
        self._set_brake(brake)
        self.run_to_rel_pos()

        if block:
            self.wait_until('running', timeout=WAIT_RUNNING_TIMEOUT)
            self.wait_until_not_moving()

    def on_to_position(self, speed, position, brake=True, block=True):
        """
        Rotate the motor at ``speed`` to ``position``

        ``speed`` can be a percentage or a :class:`ev3dev2.motor.SpeedValue`
        object, enabling use of other units.
        """
        speed = self._speed_native_units(speed)
        self.speed_sp = int(round(speed))
        self.position_sp = position
        self._set_brake(brake)
        self.run_to_abs_pos()

        if block:
            self.wait_until('running', timeout=WAIT_RUNNING_TIMEOUT)
            self.wait_until_not_moving()

    def on_for_seconds(self, speed, seconds, brake=True, block=True):
        """
        Rotate the motor at ``speed`` for ``seconds``

        ``speed`` can be a percentage or a :class:`ev3dev2.motor.SpeedValue`
        object, enabling use of other units.
        """

        if seconds < 0:
            raise ValueError("seconds is negative ({})".format(seconds))

        speed = self._speed_native_units(speed)
        self.speed_sp = int(round(speed))
        self.time_sp = int(seconds * 1000)
        self._set_brake(brake)
        self.run_timed()

        if block:
            self.wait_until('running', timeout=WAIT_RUNNING_TIMEOUT)
            self.wait_until_not_moving()

    def on(self, speed, brake=True, block=False):
        """
        Rotate the motor at ``speed`` for forever

        ``speed`` can be a percentage or a :class:`ev3dev2.motor.SpeedValue`
        object, enabling use of other units.

        Note that ``block`` is False by default, this is different from the
        other ``on_for_XYZ`` methods.
        """
        speed = self._speed_native_units(speed)
        self.speed_sp = int(round(speed))
        self._set_brake(brake)
        self.run_forever()

        if block:
            self.wait_until('running', timeout=WAIT_RUNNING_TIMEOUT)
            self.wait_until_not_moving()

    def off(self, brake=True):
        self._set_brake(brake)
        self.stop()

    @property
    def rotations(self):
        return float(self.position / self.count_per_rot)

    @property
    def degrees(self):
        return self.rotations * 360


def list_motors(name_pattern=Motor.SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
    """
    This is a generator function that enumerates all tacho motors that match
    the provided arguments.

    Parameters:
        name_pattern: pattern that device name should match.
            For example, 'motor*'. Default value: '*'.
        keyword arguments: used for matching the corresponding device
            attributes. For example, driver_name='lego-ev3-l-motor', or
            address=['outB', 'outC']. When argument value
            is a list, then a match against any entry of the list is
            enough.
    """
    class_path = abspath(Device.DEVICE_ROOT_PATH + '/' + Motor.SYSTEM_CLASS_NAME)

    return (Motor(name_pattern=name, name_exact=True) for name in list_device_names(class_path, name_pattern, **kwargs))


class LargeMotor(Motor):
    """
    EV3/NXT large servo motor.

    Same as :class:`Motor`, except it will only successfully initialize if it finds a "large" motor.
    """

    SYSTEM_CLASS_NAME = Motor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = '*'
    __slots__ = []

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        super(LargeMotor, self).__init__(address,
                                         name_pattern,
                                         name_exact,
                                         driver_name=['lego-ev3-l-motor', 'lego-nxt-motor'],
                                         **kwargs)


class MediumMotor(Motor):
    """
    EV3 medium servo motor.

    Same as :class:`Motor`, except it will only successfully initialize if it finds a "medium" motor.
    """

    SYSTEM_CLASS_NAME = Motor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = '*'
    __slots__ = []

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        super(MediumMotor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-m-motor'], **kwargs)


class ActuonixL1250Motor(Motor):
    """
    Actuonix L12 50 linear servo motor.

    Same as :class:`Motor`, except it will only successfully initialize if it finds an
    Actuonix L12 50 linear servo motor
    """

    SYSTEM_CLASS_NAME = Motor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = 'linear*'
    __slots__ = []

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        super(ActuonixL1250Motor, self).__init__(address,
                                                 name_pattern,
                                                 name_exact,
                                                 driver_name=['act-l12-ev3-50'],
                                                 **kwargs)


class ActuonixL12100Motor(Motor):
    """
    Actuonix L12 100 linear servo motor.

    Same as :class:`Motor`, except it will only successfully initialize if it finds an
    Actuonix L12 100linear servo motor
    """

    SYSTEM_CLASS_NAME = Motor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = 'linear*'
    __slots__ = []

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        super(ActuonixL12100Motor, self).__init__(address,
                                                  name_pattern,
                                                  name_exact,
                                                  driver_name=['act-l12-ev3-100'],
                                                  **kwargs)


class DcMotor(Device):
    """
    The DC motor class provides a uniform interface for using regular DC motors
    with no fancy controls or feedback. This includes LEGO MINDSTORMS RCX motors
    and LEGO Power Functions motors.
    """

    SYSTEM_CLASS_NAME = 'dc-motor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'motor*'
    __slots__ = [
        '_address',
        '_command',
        '_commands',
        '_driver_name',
        '_duty_cycle',
        '_duty_cycle_sp',
        '_polarity',
        '_ramp_down_sp',
        '_ramp_up_sp',
        '_state',
        '_stop_action',
        '_stop_actions',
        '_time_sp',
    ]

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        if address is not None:
            kwargs['address'] = address
        super(DcMotor, self).__init__(self.SYSTEM_CLASS_NAME, name_pattern, name_exact, **kwargs)

        self._address = None
        self._command = None
        self._commands = None
        self._driver_name = None
        self._duty_cycle = None
        self._duty_cycle_sp = None
        self._polarity = None
        self._ramp_down_sp = None
        self._ramp_up_sp = None
        self._state = None
        self._stop_action = None
        self._stop_actions = None
        self._time_sp = None

    @property
    def address(self):
        """
        Returns the name of the port that this motor is connected to.
        """
        self._address, value = self.get_attr_string(self._address, 'address')
        return value

    @property
    def command(self):
        """
        Sets the command for the motor. Possible values are ``run-forever``, ``run-timed`` and
        ``stop``. Not all commands may be supported, so be sure to check the contents
        of the ``commands`` attribute.
        """
        raise Exception("command is a write-only property!")

    @command.setter
    def command(self, value):
        self._command = self.set_attr_string(self._command, 'command', value)

    @property
    def commands(self):
        """
        Returns a list of commands supported by the motor
        controller.
        """
        self._commands, value = self.get_attr_set(self._commands, 'commands')
        return value

    @property
    def driver_name(self):
        """
        Returns the name of the motor driver that loaded this device. See the list
        of [supported devices] for a list of drivers.
        """
        self._driver_name, value = self.get_attr_string(self._driver_name, 'driver_name')
        return value

    @property
    def duty_cycle(self):
        """
        Shows the current duty cycle of the PWM signal sent to the motor. Values
        are -100 to 100 (-100% to 100%).
        """
        self._duty_cycle, value = self.get_attr_int(self._duty_cycle, 'duty_cycle')
        return value

    @property
    def duty_cycle_sp(self):
        """
        Writing sets the duty cycle setpoint of the PWM signal sent to the motor.
        Valid values are -100 to 100 (-100% to 100%). Reading returns the current
        setpoint.
        """
        self._duty_cycle_sp, value = self.get_attr_int(self._duty_cycle_sp, 'duty_cycle_sp')
        return value

    @duty_cycle_sp.setter
    def duty_cycle_sp(self, value):
        self._duty_cycle_sp = self.set_attr_int(self._duty_cycle_sp, 'duty_cycle_sp', value)

    @property
    def polarity(self):
        """
        Sets the polarity of the motor. Valid values are ``normal`` and ``inversed``.
        """
        self._polarity, value = self.get_attr_string(self._polarity, 'polarity')
        return value

    @polarity.setter
    def polarity(self, value):
        self._polarity = self.set_attr_string(self._polarity, 'polarity', value)

    @property
    def ramp_down_sp(self):
        """
        Sets the time in milliseconds that it take the motor to ramp down from 100%
        to 0%. Valid values are 0 to 10000 (10 seconds). Default is 0.
        """
        self._ramp_down_sp, value = self.get_attr_int(self._ramp_down_sp, 'ramp_down_sp')
        return value

    @ramp_down_sp.setter
    def ramp_down_sp(self, value):
        self._ramp_down_sp = self.set_attr_int(self._ramp_down_sp, 'ramp_down_sp', value)

    @property
    def ramp_up_sp(self):
        """
        Sets the time in milliseconds that it take the motor to up ramp from 0% to
        100%. Valid values are 0 to 10000 (10 seconds). Default is 0.
        """
        self._ramp_up_sp, value = self.get_attr_int(self._ramp_up_sp, 'ramp_up_sp')
        return value

    @ramp_up_sp.setter
    def ramp_up_sp(self, value):
        self._ramp_up_sp = self.set_attr_int(self._ramp_up_sp, 'ramp_up_sp', value)

    @property
    def state(self):
        """
        Gets a list of flags indicating the motor status. Possible
        flags are ``running`` and ``ramping``. ``running`` indicates that the motor is
        powered. ``ramping`` indicates that the motor has not yet reached the
        ``duty_cycle_sp``.
        """
        self._state, value = self.get_attr_set(self._state, 'state')
        return value

    @property
    def stop_action(self):
        """
        Sets the stop action that will be used when the motor stops. Read
        ``stop_actions`` to get the list of valid values.
        """
        raise Exception("stop_action is a write-only property!")

    @stop_action.setter
    def stop_action(self, value):
        self._stop_action = self.set_attr_string(self._stop_action, 'stop_action', value)

    @property
    def stop_actions(self):
        """
        Gets a list of stop actions. Valid values are ``coast``
        and ``brake``.
        """
        self._stop_actions, value = self.get_attr_set(self._stop_actions, 'stop_actions')
        return value

    @property
    def time_sp(self):
        """
        Writing specifies the amount of time the motor will run when using the
        ``run-timed`` command. Reading returns the current value. Units are in
        milliseconds.
        """
        self._time_sp, value = self.get_attr_int(self._time_sp, 'time_sp')
        return value

    @time_sp.setter
    def time_sp(self, value):
        self._time_sp = self.set_attr_int(self._time_sp, 'time_sp', value)

    #: Run the motor until another command is sent.
    COMMAND_RUN_FOREVER = 'run-forever'

    #: Run the motor for the amount of time specified in ``time_sp``
    #: and then stop the motor using the action specified by ``stop_action``.
    COMMAND_RUN_TIMED = 'run-timed'

    #: Run the motor at the duty cycle specified by ``duty_cycle_sp``.
    #: Unlike other run commands, changing ``duty_cycle_sp`` while running *will*
    #: take effect immediately.
    COMMAND_RUN_DIRECT = 'run-direct'

    #: Stop any of the run commands before they are complete using the
    #: action specified by ``stop_action``.
    COMMAND_STOP = 'stop'

    #: With ``normal`` polarity, a positive duty cycle will
    #: cause the motor to rotate clockwise.
    POLARITY_NORMAL = 'normal'

    #: With ``inversed`` polarity, a positive duty cycle will
    #: cause the motor to rotate counter-clockwise.
    POLARITY_INVERSED = 'inversed'

    #: Power will be removed from the motor and it will freely coast to a stop.
    STOP_ACTION_COAST = 'coast'

    #: Power will be removed from the motor and a passive electrical load will
    #: be placed on the motor. This is usually done by shorting the motor terminals
    #: together. This load will absorb the energy from the rotation of the motors and
    #: cause the motor to stop more quickly than coasting.
    STOP_ACTION_BRAKE = 'brake'

    def run_forever(self, **kwargs):
        """
        Run the motor until another command is sent.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_FOREVER

    def run_timed(self, **kwargs):
        """
        Run the motor for the amount of time specified in ``time_sp``
        and then stop the motor using the action specified by ``stop_action``.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_TIMED

    def run_direct(self, **kwargs):
        """
        Run the motor at the duty cycle specified by ``duty_cycle_sp``.
        Unlike other run commands, changing ``duty_cycle_sp`` while running *will*
        take effect immediately.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_DIRECT

    def stop(self, **kwargs):
        """
        Stop any of the run commands before they are complete using the
        action specified by ``stop_action``.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_STOP


class ServoMotor(Device):
    """
    The servo motor class provides a uniform interface for using hobby type
    servo motors.
    """

    SYSTEM_CLASS_NAME = 'servo-motor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'motor*'
    __slots__ = [
        '_address',
        '_command',
        '_driver_name',
        '_max_pulse_sp',
        '_mid_pulse_sp',
        '_min_pulse_sp',
        '_polarity',
        '_position_sp',
        '_rate_sp',
        '_state',
    ]

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        if address is not None:
            kwargs['address'] = address
        super(ServoMotor, self).__init__(self.SYSTEM_CLASS_NAME, name_pattern, name_exact, **kwargs)

        self._address = None
        self._command = None
        self._driver_name = None
        self._max_pulse_sp = None
        self._mid_pulse_sp = None
        self._min_pulse_sp = None
        self._polarity = None
        self._position_sp = None
        self._rate_sp = None
        self._state = None

    @property
    def address(self):
        """
        Returns the name of the port that this motor is connected to.
        """
        self._address, value = self.get_attr_string(self._address, 'address')
        return value

    @property
    def command(self):
        """
        Sets the command for the servo. Valid values are ``run`` and ``float``. Setting
        to ``run`` will cause the servo to be driven to the position_sp set in the
        ``position_sp`` attribute. Setting to ``float`` will remove power from the motor.
        """
        raise Exception("command is a write-only property!")

    @command.setter
    def command(self, value):
        self._command = self.set_attr_string(self._command, 'command', value)

    @property
    def driver_name(self):
        """
        Returns the name of the motor driver that loaded this device. See the list
        of [supported devices] for a list of drivers.
        """
        self._driver_name, value = self.get_attr_string(self._driver_name, 'driver_name')
        return value

    @property
    def max_pulse_sp(self):
        """
        Used to set the pulse size in milliseconds for the signal that tells the
        servo to drive to the maximum (clockwise) position_sp. Default value is 2400.
        Valid values are 2300 to 2700. You must write to the position_sp attribute for
        changes to this attribute to take effect.
        """
        self._max_pulse_sp, value = self.get_attr_int(self._max_pulse_sp, 'max_pulse_sp')
        return value

    @max_pulse_sp.setter
    def max_pulse_sp(self, value):
        self._max_pulse_sp = self.set_attr_int(self._max_pulse_sp, 'max_pulse_sp', value)

    @property
    def mid_pulse_sp(self):
        """
        Used to set the pulse size in milliseconds for the signal that tells the
        servo to drive to the mid position_sp. Default value is 1500. Valid
        values are 1300 to 1700. For example, on a 180 degree servo, this would be
        90 degrees. On continuous rotation servo, this is the 'neutral' position_sp
        where the motor does not turn. You must write to the position_sp attribute for
        changes to this attribute to take effect.
        """
        self._mid_pulse_sp, value = self.get_attr_int(self._mid_pulse_sp, 'mid_pulse_sp')
        return value

    @mid_pulse_sp.setter
    def mid_pulse_sp(self, value):
        self._mid_pulse_sp = self.set_attr_int(self._mid_pulse_sp, 'mid_pulse_sp', value)

    @property
    def min_pulse_sp(self):
        """
        Used to set the pulse size in milliseconds for the signal that tells the
        servo to drive to the miniumum (counter-clockwise) position_sp. Default value
        is 600. Valid values are 300 to 700. You must write to the position_sp
        attribute for changes to this attribute to take effect.
        """
        self._min_pulse_sp, value = self.get_attr_int(self._min_pulse_sp, 'min_pulse_sp')
        return value

    @min_pulse_sp.setter
    def min_pulse_sp(self, value):
        self._min_pulse_sp = self.set_attr_int(self._min_pulse_sp, 'min_pulse_sp', value)

    @property
    def polarity(self):
        """
        Sets the polarity of the servo. Valid values are ``normal`` and ``inversed``.
        Setting the value to ``inversed`` will cause the position_sp value to be
        inversed. i.e ``-100`` will correspond to ``max_pulse_sp``, and ``100`` will
        correspond to ``min_pulse_sp``.
        """
        self._polarity, value = self.get_attr_string(self._polarity, 'polarity')
        return value

    @polarity.setter
    def polarity(self, value):
        self._polarity = self.set_attr_string(self._polarity, 'polarity', value)

    @property
    def position_sp(self):
        """
        Reading returns the current position_sp of the servo. Writing instructs the
        servo to move to the specified position_sp. Units are percent. Valid values
        are -100 to 100 (-100% to 100%) where ``-100`` corresponds to ``min_pulse_sp``,
        ``0`` corresponds to ``mid_pulse_sp`` and ``100`` corresponds to ``max_pulse_sp``.
        """
        self._position_sp, value = self.get_attr_int(self._position_sp, 'position_sp')
        return value

    @position_sp.setter
    def position_sp(self, value):
        self._position_sp = self.set_attr_int(self._position_sp, 'position_sp', value)

    @property
    def rate_sp(self):
        """
        Sets the rate_sp at which the servo travels from 0 to 100.0% (half of the full
        range of the servo). Units are in milliseconds. Example: Setting the rate_sp
        to 1000 means that it will take a 180 degree servo 2 second to move from 0
        to 180 degrees. Note: Some servo controllers may not support this in which
        case reading and writing will fail with ``-EOPNOTSUPP``. In continuous rotation
        servos, this value will affect the rate_sp at which the speed ramps up or down.
        """
        self._rate_sp, value = self.get_attr_int(self._rate_sp, 'rate_sp')
        return value

    @rate_sp.setter
    def rate_sp(self, value):
        self._rate_sp = self.set_attr_int(self._rate_sp, 'rate_sp', value)

    @property
    def state(self):
        """
        Returns a list of flags indicating the state of the servo.
        Possible values are:
        * ``running``: Indicates that the motor is powered.
        """
        self._state, value = self.get_attr_set(self._state, 'state')
        return value

    #: Drive servo to the position set in the ``position_sp`` attribute.
    COMMAND_RUN = 'run'

    #: Remove power from the motor.
    COMMAND_FLOAT = 'float'

    #: With ``normal`` polarity, a positive duty cycle will
    #: cause the motor to rotate clockwise.
    POLARITY_NORMAL = 'normal'

    #: With ``inversed`` polarity, a positive duty cycle will
    #: cause the motor to rotate counter-clockwise.
    POLARITY_INVERSED = 'inversed'

    def run(self, **kwargs):
        """
        Drive servo to the position set in the ``position_sp`` attribute.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN

    def float(self, **kwargs):
        """
        Remove power from the motor.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_FLOAT


class MotorSet(object):
    def __init__(self, motor_specs, desc=None):
        """
        motor_specs is a dictionary such as
        {
            OUTPUT_A : LargeMotor,
            OUTPUT_C : LargeMotor,
        }
        """
        self.motors = OrderedDict()
        for motor_port in sorted(motor_specs.keys()):
            motor_class = motor_specs[motor_port]
            self.motors[motor_port] = motor_class(motor_port)
            self.motors[motor_port].reset()

        self.desc = desc

    def __str__(self):

        if self.desc:
            return self.desc
        else:
            return self.__class__.__name__

    def set_args(self, **kwargs):
        motors = kwargs.get('motors', self.motors.values())

        for motor in motors:
            for key in kwargs:
                if key != 'motors':
                    try:
                        setattr(motor, key, kwargs[key])
                    except AttributeError as e:
                        # log.error("%s %s cannot set %s to %s" % (self, motor, key, kwargs[key]))
                        raise e

    def set_polarity(self, polarity, motors=None):
        valid_choices = (LargeMotor.POLARITY_NORMAL, LargeMotor.POLARITY_INVERSED)

        assert polarity in valid_choices,\
            "%s is an invalid polarity choice, must be %s" % (polarity, ', '.join(valid_choices))
        motors = motors if motors is not None else self.motors.values()

        for motor in motors:
            motor.polarity = polarity

    def _run_command(self, **kwargs):
        motors = kwargs.get('motors', self.motors.values())

        for motor in motors:
            for key in kwargs:
                if key not in ('motors', 'commands'):
                    # log.debug("%s: %s set %s to %s" % (self, motor, key, kwargs[key]))
                    setattr(motor, key, kwargs[key])

        for motor in motors:
            motor.command = kwargs['command']
            # log.debug("%s: %s command %s" % (self, motor, kwargs['command']))

    def run_forever(self, **kwargs):
        kwargs['command'] = LargeMotor.COMMAND_RUN_FOREVER
        self._run_command(**kwargs)

    def run_to_abs_pos(self, **kwargs):
        kwargs['command'] = LargeMotor.COMMAND_RUN_TO_ABS_POS
        self._run_command(**kwargs)

    def run_to_rel_pos(self, **kwargs):
        kwargs['command'] = LargeMotor.COMMAND_RUN_TO_REL_POS
        self._run_command(**kwargs)

    def run_timed(self, **kwargs):
        kwargs['command'] = LargeMotor.COMMAND_RUN_TIMED
        self._run_command(**kwargs)

    def run_direct(self, **kwargs):
        kwargs['command'] = LargeMotor.COMMAND_RUN_DIRECT
        self._run_command(**kwargs)

    def reset(self, motors=None):
        motors = motors if motors is not None else self.motors.values()

        for motor in motors:
            motor.reset()

    def off(self, motors=None, brake=True):
        """
        Stop motors immediately. Configure motors to brake if ``brake`` is set.
        """
        motors = motors if motors is not None else self.motors.values()

        for motor in motors:
            motor._set_brake(brake)

        for motor in motors:
            motor.stop()

    def stop(self, motors=None, brake=True):
        """
        ``stop`` is an alias of ``off``.  This is deprecated but helps keep
        the API for MotorSet somewhat similar to Motor which has both ``stop``
        and ``off``.
        """
        self.off(motors, brake)

    def _is_state(self, motors, state):
        motors = motors if motors is not None else self.motors.values()

        for motor in motors:
            if state not in motor.state:
                return False

        return True

    @property
    def is_running(self, motors=None):
        return self._is_state(motors, LargeMotor.STATE_RUNNING)

    @property
    def is_ramping(self, motors=None):
        return self._is_state(motors, LargeMotor.STATE_RAMPING)

    @property
    def is_holding(self, motors=None):
        return self._is_state(motors, LargeMotor.STATE_HOLDING)

    @property
    def is_overloaded(self, motors=None):
        return self._is_state(motors, LargeMotor.STATE_OVERLOADED)

    @property
    def is_stalled(self, motors=None):
        return self._is_state(motors, LargeMotor.STATE_STALLED)

    def wait(self, cond, timeout=None, motors=None):
        motors = motors if motors is not None else self.motors.values()

        for motor in motors:
            motor.wait(cond, timeout)

    def wait_until_not_moving(self, timeout=None, motors=None):
        motors = motors if motors is not None else self.motors.values()

        for motor in motors:
            motor.wait_until_not_moving(timeout)

    def wait_until(self, s, timeout=None, motors=None):
        motors = motors if motors is not None else self.motors.values()

        for motor in motors:
            motor.wait_until(s, timeout)

    def wait_while(self, s, timeout=None, motors=None):
        motors = motors if motors is not None else self.motors.values()

        for motor in motors:
            motor.wait_while(s, timeout)

    def _block(self):
        self.wait_until('running', timeout=WAIT_RUNNING_TIMEOUT)
        self.wait_until_not_moving()


# follow gyro angle classes
class FollowGyroAngleErrorTooFast(Exception):
    """
    Raised when a gyro following robot has been asked to follow
    an angle at an unrealistic speed
    """
    pass


# line follower classes
class LineFollowErrorLostLine(Exception):
    """
    Raised when a line following robot has lost the line
    """
    pass


class LineFollowErrorTooFast(Exception):
    """
    Raised when a line following robot has been asked to follow
    a line at an unrealistic speed
    """
    pass


# line follower functions
def follow_for_forever(tank):
    """
    ``tank``: the MoveTank object that is following a line
    """
    return True


def follow_for_ms(tank, ms):
    """
    ``tank``: the MoveTank object that is following a line
    ``ms`` : the number of milliseconds to follow the line
    """
    if not hasattr(tank, 'stopwatch') or tank.stopwatch is None:
        tank.stopwatch = StopWatch()
        tank.stopwatch.start()

    if tank.stopwatch.value_ms >= ms:
        tank.stopwatch = None
        return False
    else:
        return True


class MoveTank(MotorSet):
    """
    Controls a pair of motors simultaneously, via individual speed setpoints for each motor.

    Example:

    .. code:: python

        tank_drive = MoveTank(OUTPUT_A, OUTPUT_B)
        # drive in a turn for 10 rotations of the outer motor
        tank_drive.on_for_rotations(50, 75, 10)
    """
    def __init__(self, left_motor_port, right_motor_port, desc=None, motor_class=LargeMotor):
        motor_specs = {
            left_motor_port: motor_class,
            right_motor_port: motor_class,
        }

        MotorSet.__init__(self, motor_specs, desc)
        self.left_motor = self.motors[left_motor_port]
        self.right_motor = self.motors[right_motor_port]
        self.max_speed = self.left_motor.max_speed
        self._cs = None
        self._gyro = None

    # color sensor used by follow_line()
    @property
    def cs(self):
        return self._cs

    @cs.setter
    def cs(self, cs):
        self._cs = cs

    # gyro sensor used by follow_gyro_angle()
    @property
    def gyro(self):
        return self._gyro

    @gyro.setter
    def gyro(self, gyro):
        self._gyro = gyro

    def _unpack_speeds_to_native_units(self, left_speed, right_speed):
        left_speed = self.left_motor._speed_native_units(left_speed, "left_speed")
        right_speed = self.right_motor._speed_native_units(right_speed, "right_speed")

        return (left_speed, right_speed)

    def on_for_degrees(self, left_speed, right_speed, degrees, brake=True, block=True):
        """
        Rotate the motors at 'left_speed & right_speed' for 'degrees'. Speeds
        can be percentages or any SpeedValue implementation.

        If the left speed is not equal to the right speed (i.e., the robot will
        turn), the motor on the outside of the turn will rotate for the full
        ``degrees`` while the motor on the inside will have its requested
        distance calculated according to the expected turn.
        """
        (left_speed_native_units,
         right_speed_native_units) = self._unpack_speeds_to_native_units(left_speed, right_speed)

        # proof of the following distance calculation: consider the circle formed by each wheel's path
        # v_l = d_l/t, v_r = d_r/t
        # therefore, t = d_l/v_l = d_r/v_r

        if degrees == 0 or (left_speed_native_units == 0 and right_speed_native_units == 0):
            left_degrees = degrees
            right_degrees = degrees

        # larger speed by magnitude is the "outer" wheel, and rotates the full "degrees"
        elif abs(left_speed_native_units) > abs(right_speed_native_units):
            left_degrees = degrees
            right_degrees = abs(right_speed_native_units / left_speed_native_units) * degrees

        else:
            left_degrees = abs(left_speed_native_units / right_speed_native_units) * degrees
            right_degrees = degrees

        # Set all parameters
        self.left_motor._set_rel_position_degrees_and_speed_sp(left_degrees, left_speed_native_units)
        self.left_motor._set_brake(brake)
        self.right_motor._set_rel_position_degrees_and_speed_sp(right_degrees, right_speed_native_units)
        self.right_motor._set_brake(brake)

        # Start the motors
        self.left_motor.run_to_rel_pos()
        self.right_motor.run_to_rel_pos()

        if block:
            self._block()

    def on_for_rotations(self, left_speed, right_speed, rotations, brake=True, block=True):
        """
        Rotate the motors at 'left_speed & right_speed' for 'rotations'. Speeds
        can be percentages or any SpeedValue implementation.

        If the left speed is not equal to the right speed (i.e., the robot will
        turn), the motor on the outside of the turn will rotate for the full
        ``rotations`` while the motor on the inside will have its requested
        distance calculated according to the expected turn.
        """
        MoveTank.on_for_degrees(self, left_speed, right_speed, rotations * 360, brake, block)

    def on_for_seconds(self, left_speed, right_speed, seconds, brake=True, block=True):
        """
        Rotate the motors at 'left_speed & right_speed' for 'seconds'. Speeds
        can be percentages or any SpeedValue implementation.
        """

        if seconds < 0:
            raise ValueError("seconds is negative ({})".format(seconds))

        (left_speed_native_units,
         right_speed_native_units) = self._unpack_speeds_to_native_units(left_speed, right_speed)

        # Set all parameters
        self.left_motor.speed_sp = int(round(left_speed_native_units))
        self.left_motor.time_sp = int(seconds * 1000)
        self.left_motor._set_brake(brake)
        self.right_motor.speed_sp = int(round(right_speed_native_units))
        self.right_motor.time_sp = int(seconds * 1000)
        self.right_motor._set_brake(brake)

        log.debug("%s: on_for_seconds %ss at left-speed %s, right-speed %s" % (self, seconds, left_speed, right_speed))

        # Start the motors
        self.left_motor.run_timed()
        self.right_motor.run_timed()

        if block:
            self._block()

    def on(self, left_speed, right_speed):
        """
        Start rotating the motors according to ``left_speed`` and ``right_speed`` forever.
        Speeds can be percentages or any SpeedValue implementation.
        """
        (left_speed_native_units,
         right_speed_native_units) = self._unpack_speeds_to_native_units(left_speed, right_speed)

        # Set all parameters
        self.left_motor.speed_sp = int(round(left_speed_native_units))
        self.right_motor.speed_sp = int(round(right_speed_native_units))

        # Start the motors
        self.left_motor.run_forever()
        self.right_motor.run_forever()

    def follow_line(self,
                    kp,
                    ki,
                    kd,
                    speed,
                    target_light_intensity=None,
                    follow_left_edge=True,
                    white=60,
                    off_line_count_max=20,
                    sleep_time=0.01,
                    follow_for=follow_for_forever,
                    **kwargs):
        """
        PID line follower

        ``kp``, ``ki``, and ``kd`` are the PID constants.

        ``speed`` is the desired speed of the midpoint of the robot

        ``target_light_intensity`` is the reflected light intensity when the color sensor
            is on the edge of the line.  If this is None we assume that the color sensor
            is on the edge of the line and will take a reading to set this variable.

        ``follow_left_edge`` determines if we follow the left or right edge of the line

        ``white`` is the reflected_light_intensity that is used to determine if we have
            lost the line

        ``off_line_count_max`` is how many consecutive times through the loop the
            reflected_light_intensity must be greater than ``white`` before we
            declare the line lost and raise an exception

        ``sleep_time`` is how many seconds we sleep on each pass through
            the loop.  This is to give the robot a chance to react
            to the new motor settings. This should be something small such
            as 0.01 (10ms).

        ``follow_for`` is called to determine if we should keep following the
            line or stop.  This function will be passed ``self`` (the current
            ``MoveTank`` object). Current supported options are:
            - ``follow_for_forever``
            - ``follow_for_ms``

        ``**kwargs`` will be passed to the ``follow_for`` function

        Example:

        .. code:: python

            from ev3dev2.motor import OUTPUT_A, OUTPUT_B, MoveTank, SpeedPercent, follow_for_ms
            from ev3dev2.sensor.lego import ColorSensor

            tank = MoveTank(OUTPUT_A, OUTPUT_B)
            tank.cs = ColorSensor()

            try:
                # Follow the line for 4500ms
                tank.follow_line(
                    kp=11.3, ki=0.05, kd=3.2,
                    speed=SpeedPercent(30),
                    follow_for=follow_for_ms,
                    ms=4500
                )
            except LineFollowErrorTooFast:
                tank.stop()
                raise
        """
        if not self._cs:
            raise DeviceNotDefined(
                "The 'cs' variable must be defined with a ColorSensor. Example: tank.cs = ColorSensor()")

        if target_light_intensity is None:
            target_light_intensity = self._cs.reflected_light_intensity

        integral = 0.0
        last_error = 0.0
        derivative = 0.0
        off_line_count = 0
        speed = speed_to_speedvalue(speed)
        speed_native_units = speed.to_native_units(self.left_motor)

        while follow_for(self, **kwargs):
            reflected_light_intensity = self._cs.reflected_light_intensity
            error = target_light_intensity - reflected_light_intensity
            integral = integral + error
            derivative = error - last_error
            last_error = error
            turn_native_units = (kp * error) + (ki * integral) + (kd * derivative)

            if not follow_left_edge:
                turn_native_units *= -1

            left_speed = SpeedNativeUnits(speed_native_units - turn_native_units)
            right_speed = SpeedNativeUnits(speed_native_units + turn_native_units)

            # Have we lost the line?
            if reflected_light_intensity >= white:
                off_line_count += 1

                if off_line_count >= off_line_count_max:
                    self.stop()
                    raise LineFollowErrorLostLine("we lost the line")
            else:
                off_line_count = 0

            if sleep_time:
                time.sleep(sleep_time)

            try:
                self.on(left_speed, right_speed)
            except SpeedInvalid as e:
                log.exception(e)
                self.stop()
                raise LineFollowErrorTooFast("The robot is moving too fast to follow the line")

        self.stop()

    def follow_gyro_angle(self,
                          kp,
                          ki,
                          kd,
                          speed,
                          target_angle=0,
                          sleep_time=0.01,
                          follow_for=follow_for_forever,
                          **kwargs):
        """
        PID gyro angle follower

        ``kp``, ``ki``, and ``kd`` are the PID constants.

        ``speed`` is the desired speed of the midpoint of the robot

        ``target_angle`` is the angle we want to maintain

        ``sleep_time`` is how many seconds we sleep on each pass through
            the loop.  This is to give the robot a chance to react
            to the new motor settings. This should be something small such
            as 0.01 (10ms).

        ``follow_for`` is called to determine if we should keep following the
            desired angle or stop.  This function will be passed ``self`` (the current
            ``MoveTank`` object). Current supported options are:
            - ``follow_for_forever``
            - ``follow_for_ms``

        ``**kwargs`` will be passed to the ``follow_for`` function

        Example:

        .. code:: python

            from ev3dev2.motor import OUTPUT_A, OUTPUT_B, MoveTank, SpeedPercent, follow_for_ms
            from ev3dev2.sensor.lego import GyroSensor

            # Instantiate the MoveTank object
            tank = MoveTank(OUTPUT_A, OUTPUT_B)

            # Initialize the tank's gyro sensor
            tank.gyro = GyroSensor()

            # Calibrate the gyro to eliminate drift, and to initialize the current angle as 0
            tank.gyro.calibrate()

            try:

                # Follow the target_angle for 4500ms
                tank.follow_gyro_angle(
                    kp=11.3, ki=0.05, kd=3.2,
                    speed=SpeedPercent(30),
                    target_angle=0,
                    follow_for=follow_for_ms,
                    ms=4500
                )
            except FollowGyroAngleErrorTooFast:
                tank.stop()
                raise
        """
        if not self._gyro:
            raise DeviceNotDefined(
                "The 'gyro' variable must be defined with a GyroSensor. Example: tank.gyro = GyroSensor()")

        integral = 0.0
        last_error = 0.0
        derivative = 0.0
        speed = speed_to_speedvalue(speed)
        speed_native_units = speed.to_native_units(self.left_motor)

        while follow_for(self, **kwargs):
            current_angle = self._gyro.angle
            error = current_angle - target_angle
            integral = integral + error
            derivative = error - last_error
            last_error = error
            turn_native_units = (kp * error) + (ki * integral) + (kd * derivative)

            left_speed = SpeedNativeUnits(speed_native_units - turn_native_units)
            right_speed = SpeedNativeUnits(speed_native_units + turn_native_units)

            if sleep_time:
                time.sleep(sleep_time)

            try:
                self.on(left_speed, right_speed)
            except SpeedInvalid as e:
                log.exception(e)
                self.stop()
                raise FollowGyroAngleErrorTooFast("The robot is moving too fast to follow the angle")

        self.stop()

    def turn_degrees(self, speed, target_angle, brake=True, error_margin=2, sleep_time=0.01):
        """
        Use a GyroSensor to rotate in place for ``target_angle``

        ``speed`` is the desired speed of the midpoint of the robot

        ``target_angle`` is the number of degrees we want to rotate

        ``brake`` hit the brakes once we reach ``target_angle``

        ``error_margin`` is the +/- angle threshold to control how accurate the turn should be

        ``sleep_time`` is how many seconds we sleep on each pass through
            the loop.  This is to give the robot a chance to react
            to the new motor settings. This should be something small such
            as 0.01 (10ms).

        Rotate in place for ``target_degrees`` at ``speed``

        Example:

        .. code:: python

            from ev3dev2.motor import OUTPUT_A, OUTPUT_B, MoveTank, SpeedPercent
            from ev3dev2.sensor.lego import GyroSensor

            # Instantiate the MoveTank object
            tank = MoveTank(OUTPUT_A, OUTPUT_B)

            # Initialize the tank's gyro sensor
            tank.gyro = GyroSensor()

            # Calibrate the gyro to eliminate drift, and to initialize the current angle as 0
            tank.gyro.calibrate()

            # Pivot 30 degrees
            tank.turn_degrees(
                speed=SpeedPercent(5),
                target_angle=30
            )
        """

        # MoveTank does not have information on wheel size and distance (that is
        # MoveDifferential) so we must use a GyroSensor to control how far we rotate.
        if not self._gyro:
            raise DeviceNotDefined(
                "The 'gyro' variable must be defined with a GyroSensor. Example: tank.gyro = GyroSensor()")

        speed = speed_to_speedvalue(speed)
        speed_native_units = speed.to_native_units(self.left_motor)
        target_angle = self._gyro.angle + target_angle

        while True:
            current_angle = self._gyro.angle
            delta = abs(target_angle - current_angle)

            if delta <= error_margin:
                self.stop(brake=brake)
                break

            # we are left of our target, rotate clockwise
            if current_angle < target_angle:
                left_speed = SpeedNativeUnits(speed_native_units)
                right_speed = SpeedNativeUnits(-1 * speed_native_units)

            # we are right of our target, rotate counter-clockwise
            else:
                left_speed = SpeedNativeUnits(-1 * speed_native_units)
                right_speed = SpeedNativeUnits(speed_native_units)

            self.on(left_speed, right_speed)

            if sleep_time:
                time.sleep(sleep_time)

    def turn_right(self, speed, degrees, brake=True, error_margin=2, sleep_time=0.01):
        """
        Rotate clockwise ``degrees`` in place
        """
        self.turn_degrees(speed, abs(degrees), brake, error_margin, sleep_time)

    def turn_left(self, speed, degrees, brake=True, error_margin=2, sleep_time=0.01):
        """
        Rotate counter-clockwise ``degrees`` in place
        """
        self.turn_degrees(speed, abs(degrees) * -1, brake, error_margin, sleep_time)


class MoveSteering(MoveTank):
    """
    Controls a pair of motors simultaneously, via a single "steering" value and a speed.

    steering [-100, 100]:
        * -100 means turn left on the spot (right motor at 100% forward, left motor at 100% backward),
        *  0   means drive in a straight line, and
        *  100 means turn right on the spot (left motor at 100% forward, right motor at 100% backward).

    "steering" can be any number between -100 and 100.

    Example:

    .. code:: python

        steering_drive = MoveSteering(OUTPUT_A, OUTPUT_B)
        # drive in a turn for 10 rotations of the outer motor
        steering_drive.on_for_rotations(-20, SpeedPercent(75), 10)
    """
    def on_for_rotations(self, steering, speed, rotations, brake=True, block=True):
        """
        Rotate the motors according to the provided ``steering``.

        The distance each motor will travel follows the rules of :meth:`MoveTank.on_for_rotations`.
        """
        (left_speed, right_speed) = self.get_speed_steering(steering, speed)
        MoveTank.on_for_rotations(self, SpeedNativeUnits(left_speed), SpeedNativeUnits(right_speed), rotations, brake,
                                  block)

    def on_for_degrees(self, steering, speed, degrees, brake=True, block=True):
        """
        Rotate the motors according to the provided ``steering``.

        The distance each motor will travel follows the rules of :meth:`MoveTank.on_for_degrees`.
        """
        (left_speed, right_speed) = self.get_speed_steering(steering, speed)
        MoveTank.on_for_degrees(self, SpeedNativeUnits(left_speed), SpeedNativeUnits(right_speed), degrees, brake,
                                block)

    def on_for_seconds(self, steering, speed, seconds, brake=True, block=True):
        """
        Rotate the motors according to the provided ``steering`` for ``seconds``.
        """
        (left_speed, right_speed) = self.get_speed_steering(steering, speed)
        MoveTank.on_for_seconds(self, SpeedNativeUnits(left_speed), SpeedNativeUnits(right_speed), seconds, brake,
                                block)

    def on(self, steering, speed):
        """
        Start rotating the motors according to the provided ``steering`` and
        ``speed`` forever.
        """
        (left_speed, right_speed) = self.get_speed_steering(steering, speed)
        MoveTank.on(self, SpeedNativeUnits(left_speed), SpeedNativeUnits(right_speed))

    def get_speed_steering(self, steering, speed):
        """
        Calculate the speed_sp for each motor in a pair to achieve the specified
        steering. Note that calling this function alone will not make the
        motors move, it only calculates the speed. A run_* function must be called
        afterwards to make the motors move.

        steering [-100, 100]:
            * -100 means turn left on the spot (right motor at 100% forward, left motor at 100% backward),
            *  0   means drive in a straight line, and
            *  100 means turn right on the spot (left motor at 100% forward, right motor at 100% backward).

        speed:
            The speed that should be applied to the outmost motor (the one
            rotating faster). The speed of the other motor will be computed
            automatically.
        """

        assert steering >= -100 and steering <= 100,\
            "{} is an invalid steering, must be between -100 and 100 (inclusive)".format(steering)

        # We don't have a good way to make this generic for the pair... so we
        # assume that the left motor's speed stats are the same as the right
        # motor's.
        speed = self.left_motor._speed_native_units(speed)
        left_speed = speed
        right_speed = speed
        speed_factor = (50 - abs(float(steering))) / 50

        if steering >= 0:
            right_speed *= speed_factor
        else:
            left_speed *= speed_factor

        return (left_speed, right_speed)


class MoveDifferential(MoveTank):
    """
    MoveDifferential is a child of MoveTank that adds the following capabilities:

    - drive in a straight line for a specified distance

    - rotate in place in a circle (clockwise or counter clockwise) for a
      specified number of degrees

    - drive in an arc (clockwise or counter clockwise) of a specified radius
      for a specified distance

    Odometry can be use to enable driving to specific coordinates and
    rotating to a specific angle.

    New arguments:

    wheel_class - Typically a child class of :class:`ev3dev2.wheel.Wheel`. This is used to
    get the circumference of the wheels of the robot. The circumference is
    needed for several calculations in this class.

    wheel_distance_mm - The distance between the mid point of the two
    wheels of the robot. You may need to do some test drives to find
    the correct value for your robot.  It is not as simple as measuring
    the distance between the midpoints of the two wheels. The weight of
    the robot, center of gravity, etc come into play.

    You can use utils/move_differential.py to call on_arc_left() to do
    some test drives of circles with a radius of 200mm. Adjust your
    wheel_distance_mm until your robot can drive in a perfect circle
    and stop exactly where it started. It does not have to be a circle
    with a radius of 200mm, you can test with any size circle but you do
    not want it to be too small or it will be difficult to test small
    adjustments to wheel_distance_mm.

    Example:

    .. code:: python

        from ev3dev2.motor import OUTPUT_A, OUTPUT_B, MoveDifferential, SpeedRPM
        from ev3dev2.wheel import EV3Tire

        STUD_MM = 8

        # test with a robot that:
        # - uses the standard wheels known as EV3Tire
        # - wheels are 16 studs apart
        mdiff = MoveDifferential(OUTPUT_A, OUTPUT_B, EV3Tire, 16 * STUD_MM)

        # Rotate 90 degrees clockwise
        mdiff.turn_right(SpeedRPM(40), 90)

        # Drive forward 500 mm
        mdiff.on_for_distance(SpeedRPM(40), 500)

        # Drive in arc to the right along an imaginary circle of radius 150 mm.
        # Drive for 700 mm around this imaginary circle.
        mdiff.on_arc_right(SpeedRPM(80), 150, 700)

        # Enable odometry
        mdiff.odometry_start()

        # Use odometry to drive to specific coordinates
        mdiff.on_to_coordinates(SpeedRPM(40), 300, 300)

        # Use odometry to go back to where we started
        mdiff.on_to_coordinates(SpeedRPM(40), 0, 0)

        # Use odometry to rotate in place to 90 degrees
        mdiff.turn_to_angle(SpeedRPM(40), 90)

        # Disable odometry
        mdiff.odometry_stop()
    """
    def __init__(self,
                 left_motor_port,
                 right_motor_port,
                 wheel_class,
                 wheel_distance_mm,
                 desc=None,
                 motor_class=LargeMotor):

        MoveTank.__init__(self, left_motor_port, right_motor_port, desc, motor_class)
        self.wheel = wheel_class()
        self.wheel_distance_mm = wheel_distance_mm

        # The circumference of the circle made if this robot were to rotate in place
        self.circumference_mm = self.wheel_distance_mm * math.pi

        self.min_circle_radius_mm = self.wheel_distance_mm / 2

        # odometry variables
        self.x_pos_mm = 0.0  # robot X position in mm
        self.y_pos_mm = 0.0  # robot Y position in mm
        self.odometry_thread_run = False
        self.theta = 0.0

    def on_for_distance(self, speed, distance_mm, brake=True, block=True):
        """
        Drive in a straight line for ``distance_mm``
        """
        rotations = distance_mm / self.wheel.circumference_mm
        log.debug("%s: on_for_rotations distance_mm %s, rotations %s, speed %s" % (self, distance_mm, rotations, speed))

        MoveTank.on_for_rotations(self, speed, speed, rotations, brake, block)

    def _on_arc(self, speed, radius_mm, distance_mm, brake, block, arc_right):
        """
        Drive in a circle with 'radius' for 'distance'
        """

        if radius_mm < self.min_circle_radius_mm:
            raise ValueError("{}: radius_mm {} is less than min_circle_radius_mm {}".format(
                self, radius_mm, self.min_circle_radius_mm))

        # The circle formed at the halfway point between the two wheels is the
        # circle that must have a radius of radius_mm
        circle_outer_mm = 2 * math.pi * (radius_mm + (self.wheel_distance_mm / 2))
        circle_middle_mm = 2 * math.pi * radius_mm
        circle_inner_mm = 2 * math.pi * (radius_mm - (self.wheel_distance_mm / 2))

        if arc_right:
            # The left wheel is making the larger circle and will move at 'speed'
            # The right wheel is making a smaller circle so its speed will be a fraction of the left motor's speed
            left_speed = speed
            right_speed = float(circle_inner_mm / circle_outer_mm) * left_speed

        else:
            # The right wheel is making the larger circle and will move at 'speed'
            # The left wheel is making a smaller circle so its speed will be a fraction of the right motor's speed
            right_speed = speed
            left_speed = float(circle_inner_mm / circle_outer_mm) * right_speed

        log.debug("%s: arc %s, radius %s, distance %s, left-speed %s, right-speed %s" %
                  (self, "right" if arc_right else "left", radius_mm, distance_mm, left_speed, right_speed))
        log.debug("%s: circle_outer_mm %s, circle_middle_mm %s, circle_inner_mm %s" %
                  (self, circle_outer_mm, circle_middle_mm, circle_inner_mm))

        # We know we want the middle circle to be of length distance_mm so
        # calculate the percentage of circle_middle_mm we must travel for the
        # middle of the robot to travel distance_mm.
        circle_middle_percentage = float(distance_mm / circle_middle_mm)

        # Now multiple that percentage by circle_outer_mm to calculate how
        # many mm the outer wheel should travel.
        circle_outer_final_mm = circle_middle_percentage * circle_outer_mm

        outer_wheel_rotations = float(circle_outer_final_mm / self.wheel.circumference_mm)
        outer_wheel_degrees = outer_wheel_rotations * 360

        log.debug("%s: arc %s, circle_middle_percentage %s, circle_outer_final_mm %s, " %
                  (self, "right" if arc_right else "left", circle_middle_percentage, circle_outer_final_mm))
        log.debug("%s: outer_wheel_rotations %s, outer_wheel_degrees %s" %
                  (self, outer_wheel_rotations, outer_wheel_degrees))

        MoveTank.on_for_degrees(self, left_speed, right_speed, outer_wheel_degrees, brake, block)

    def on_arc_right(self, speed, radius_mm, distance_mm, brake=True, block=True):
        """
        Drive clockwise in a circle with 'radius_mm' for 'distance_mm'
        """
        self._on_arc(speed, radius_mm, distance_mm, brake, block, True)

    def on_arc_left(self, speed, radius_mm, distance_mm, brake=True, block=True):
        """
        Drive counter-clockwise in a circle with 'radius_mm' for 'distance_mm'
        """
        self._on_arc(speed, radius_mm, distance_mm, brake, block, False)

    def turn_degrees(self, speed, degrees, brake=True, block=True, error_margin=2, use_gyro=False):
        """
        Rotate in place ``degrees``. Both wheels must turn at the same speed for us
        to rotate in place.  If the following conditions are met the GryoSensor will
        be used to improve the accuracy of our turn:
        - ``use_gyro``, ``brake`` and ``block`` are all True
        - A GyroSensor has been defined via ``self.gyro = GyroSensor()``
        """
        def final_angle(init_angle, degrees):
            result = init_angle - degrees

            while result <= -360:
                result += 360

            while result >= 360:
                result -= 360

            if result < 0:
                result += 360

            return result

        # use the gyro to check that we turned the correct amount?
        use_gyro = bool(use_gyro and block and brake)
        if use_gyro and not self._gyro:
            raise DeviceNotDefined(
                "The 'gyro' variable must be defined with a GyroSensor. Example: tank.gyro = GyroSensor()")

        if use_gyro:
            angle_init_degrees = self._gyro.circle_angle()
        else:
            angle_init_degrees = math.degrees(self.theta)

        angle_target_degrees = final_angle(angle_init_degrees, degrees)

        log.info("%s: turn_degrees() %d degrees from %s to %s" %
                 (self, degrees, angle_init_degrees, angle_target_degrees))

        # The distance each wheel needs to travel
        distance_mm = (abs(degrees) / 360) * self.circumference_mm

        # The number of rotations to move distance_mm
        rotations = distance_mm / self.wheel.circumference_mm

        # If degrees is positive rotate clockwise
        if degrees > 0:
            MoveTank.on_for_rotations(self, speed, speed * -1, rotations, brake, block)

        # If degrees is negative rotate counter-clockwise
        else:
            MoveTank.on_for_rotations(self, speed * -1, speed, rotations, brake, block)

        if use_gyro:
            angle_current_degrees = self._gyro.circle_angle()

            # This can happen if we are aiming for 2 degrees and overrotate to 358 degrees
            # We need to rotate counter-clockwise
            if 90 >= angle_target_degrees >= 0 and 270 <= angle_current_degrees <= 360:
                degrees_error = (angle_target_degrees + (360 - angle_current_degrees)) * -1

            # This can happen if we are aiming for 358 degrees and overrotate to 2 degrees
            # We need to rotate clockwise
            elif 360 >= angle_target_degrees >= 270 and 0 <= angle_current_degrees <= 90:
                degrees_error = angle_current_degrees + (360 - angle_target_degrees)

            # We need to rotate clockwise
            elif angle_current_degrees > angle_target_degrees:
                degrees_error = angle_current_degrees - angle_target_degrees

            # We need to rotate counter-clockwise
            else:
                degrees_error = (angle_target_degrees - angle_current_degrees) * -1

            log.info("%s: turn_degrees() ended up at %s, error %s, error_margin %s" %
                     (self, angle_current_degrees, degrees_error, error_margin))

            if abs(degrees_error) > error_margin:
                self.turn_degrees(speed, degrees_error, brake, block, error_margin, use_gyro)

    def turn_right(self, speed, degrees, brake=True, block=True, error_margin=2, use_gyro=False):
        """
        Rotate clockwise ``degrees`` in place
        """
        self.turn_degrees(speed, abs(degrees), brake, block, error_margin, use_gyro)

    def turn_left(self, speed, degrees, brake=True, block=True, error_margin=2, use_gyro=False):
        """
        Rotate counter-clockwise ``degrees`` in place
        """
        self.turn_degrees(speed, abs(degrees) * -1, brake, block, error_margin, use_gyro)

    def turn_to_angle(self, speed, angle_target_degrees, brake=True, block=True, error_margin=2, use_gyro=False):
        """
        Rotate in place to ``angle_target_degrees`` at ``speed``
        """
        if not self.odometry_thread_run:
            raise ThreadNotRunning("odometry_start() must be called to track robot coordinates")

        # Make both target and current angles positive numbers between 0 and 360
        while angle_target_degrees < 0:
            angle_target_degrees += 360

        angle_current_degrees = math.degrees(self.theta)

        while angle_current_degrees < 0:
            angle_current_degrees += 360

        # Is it shorter to rotate to the right or left
        # to reach angle_target_degrees?
        if angle_current_degrees > angle_target_degrees:
            turn_right = True
            angle_delta = angle_current_degrees - angle_target_degrees
        else:
            turn_right = False
            angle_delta = angle_target_degrees - angle_current_degrees

        if angle_delta > 180:
            angle_delta = 360 - angle_delta
            turn_right = not turn_right

        log.debug("%s: turn_to_angle %s, current angle %s, delta %s, turn_right %s" %
                  (self, angle_target_degrees, angle_current_degrees, angle_delta, turn_right))
        self.odometry_coordinates_log()

        if turn_right:
            self.turn_degrees(speed, abs(angle_delta), brake, block, error_margin, use_gyro)
        else:
            self.turn_degrees(speed, abs(angle_delta) * -1, brake, block, error_margin, use_gyro)

        self.odometry_coordinates_log()

    def odometry_coordinates_log(self):
        log.debug("%s: odometry angle %s at (%d, %d)" % (self, math.degrees(self.theta), self.x_pos_mm, self.y_pos_mm))

    def odometry_start(self, theta_degrees_start=90.0, x_pos_start=0.0, y_pos_start=0.0, sleep_time=0.005):  # 5ms
        """
        Ported from:
        http://seattlerobotics.org/encoder/200610/Article3/IMU%20Odometry,%20by%20David%20Anderson.htm

        A thread is started that will run until the user calls odometry_stop()
        which will set odometry_thread_run to False
        """
        def _odometry_monitor():
            left_previous = 0
            right_previous = 0
            self.theta = math.radians(theta_degrees_start)  # robot heading
            self.x_pos_mm = x_pos_start  # robot X position in mm
            self.y_pos_mm = y_pos_start  # robot Y position in mm
            TWO_PI = 2 * math.pi
            self.odometry_thread_run = True

            while self.odometry_thread_run:

                # sample the left and right encoder counts as close together
                # in time as possible
                left_current = self.left_motor.position
                right_current = self.right_motor.position

                # determine how many ticks since our last sampling
                left_ticks = left_current - left_previous
                right_ticks = right_current - right_previous

                # Have we moved?
                if not left_ticks and not right_ticks:
                    if sleep_time:
                        time.sleep(sleep_time)
                    continue

                # update _previous for next time
                left_previous = left_current
                right_previous = right_current

                # rotations = distance_mm/self.wheel.circumference_mm
                left_rotations = float(left_ticks / self.left_motor.count_per_rot)
                right_rotations = float(right_ticks / self.right_motor.count_per_rot)

                # convert longs to floats and ticks to mm
                left_mm = float(left_rotations * self.wheel.circumference_mm)
                right_mm = float(right_rotations * self.wheel.circumference_mm)

                # calculate distance we have traveled since last sampling
                mm = (left_mm + right_mm) / 2.0

                # accumulate total rotation around our center
                self.theta += (right_mm - left_mm) / self.wheel_distance_mm

                # and clip the rotation to plus or minus 360 degrees
                self.theta -= float(int(self.theta / TWO_PI) * TWO_PI)

                # now calculate and accumulate our position in mm
                self.x_pos_mm += mm * math.cos(self.theta)
                self.y_pos_mm += mm * math.sin(self.theta)

                if sleep_time:
                    time.sleep(sleep_time)

        _thread.start_new_thread(_odometry_monitor, ())

        # Block until the thread has started doing work
        while not self.odometry_thread_run:
            pass

    def odometry_stop(self):
        """
        Signal the odometry thread to exit
        """

        if self.odometry_thread_run:
            self.odometry_thread_run = False

    def on_to_coordinates(self, speed, x_target_mm, y_target_mm, brake=True, block=True):
        """
        Drive to (``x_target_mm``, ``y_target_mm``) coordinates at ``speed``
        """
        if not self.odometry_thread_run:
            raise ThreadNotRunning("odometry_start() must be called to track robot coordinates")

        # stop moving
        self.off(brake='hold')

        # rotate in place so we are pointed straight at our target
        x_delta = x_target_mm - self.x_pos_mm
        y_delta = y_target_mm - self.y_pos_mm
        angle_target_radians = math.atan2(y_delta, x_delta)
        angle_target_degrees = math.degrees(angle_target_radians)
        self.turn_to_angle(speed, angle_target_degrees, brake=True, block=True)

        # drive in a straight line to the target coordinates
        distance_mm = math.sqrt(pow(self.x_pos_mm - x_target_mm, 2) + pow(self.y_pos_mm - y_target_mm, 2))
        self.on_for_distance(speed, distance_mm, brake, block)


class MoveJoystick(MoveTank):
    """
    Used to control a pair of motors via a single joystick vector.
    """
    def on(self, x, y, radius=100.0):
        """
        Convert ``x``,``y`` joystick coordinates to left/right motor speed percentages
        and move the motors.

        This will use a classic "arcade drive" algorithm: a full-forward joystick
        goes straight forward and likewise for full-backward. Pushing the joystick
        all the way to one side will make it turn on the spot in that direction.
        Positions in the middle will control how fast the vehicle moves and how
        sharply it turns.

        ``x``, ``y``:
            The X and Y coordinates of the joystick's position, with
            (0,0) representing the center position. X is horizontal and Y is vertical.

        ``radius`` (default 100):
            The radius of the joystick, controlling the range of the input (x, y) values.
            e.g. if "x" and "y" can be between -1 and 1, radius should be set to "1".
        """

        # If joystick is in the middle stop the tank
        if not x and not y:
            self.off()
            return

        vector_length = math.sqrt((x * x) + (y * y))
        angle = math.degrees(math.atan2(y, x))

        if angle < 0:
            angle += 360

        # Should not happen but can happen (just by a hair) due to floating point math
        if vector_length > radius:
            vector_length = radius

        (init_left_speed_percentage, init_right_speed_percentage) = MoveJoystick.angle_to_speed_percentage(angle)

        # scale the speed percentages based on vector_length vs. radius
        left_speed_percentage = (init_left_speed_percentage * vector_length) / radius
        right_speed_percentage = (init_right_speed_percentage * vector_length) / radius

        #     log.debug("""
        # x, y                         : %s, %s
        # radius                       : %s
        # angle                        : %s
        # vector length                : %s
        # init left_speed_percentage   : %s
        # init right_speed_percentage  : %s
        # final left_speed_percentage  : %s
        # final right_speed_percentage : %s
        # """ % (x, y, radius, angle, vector_length,
        #         init_left_speed_percentage, init_right_speed_percentage,
        #         left_speed_percentage, right_speed_percentage))

        MoveTank.on(self, SpeedPercent(left_speed_percentage), SpeedPercent(right_speed_percentage))

    @staticmethod
    def angle_to_speed_percentage(angle):
        """
        The following graphic illustrates the **motor power outputs** for the
        left and right motors based on where the joystick is pointing, of the
        form ``(left power, right power)``::

                                     (1, 1)
                                  . . . . . . .
                               .        |        .
                            .           |           .
                   (0, 1) .             |             . (1, 0)
                        .               |               .
                       .                |                 .
                      .                 |                  .
                     .                  |                   .
                    .                   |                   .
                    .                   |     x-axis        .
            (-1, 1) .---------------------------------------. (1, -1)
                    .                   |                   .
                    .                   |                   .
                     .                  |                  .
                      .                 | y-axis          .
                        .               |               .
                  (0, -1) .             |             . (-1, 0)
                            .           |           .
                               .        |        .
                                  . . . . . . .
                                     (-1, -1)


        The joystick is a circle within a circle where the (x, y) coordinates
        of the joystick form an angle with the x-axis.  Our job is to translate
        this angle into the percentage of power that should be sent to each motor.
        For instance if the joystick is moved all the way to the top of the circle
        we want both motors to move forward with 100% power...that is represented
        above by (1, 1).  If the joystick is moved all the way to the right side of
        the circle we want to rotate clockwise so we move the left motor forward 100%
        and the right motor backwards 100%...so (1, -1).  If the joystick is at
        45 degrees then we move apply (1, 0) to move the left motor forward 100% and
        the right motor stays still.

        The 8 points shown above are pretty easy. For the points in between those 8
        we do some math to figure out what the percentages should be. Take 11.25 degrees
        for example. We look at how the motors transition from 0 degrees to 45 degrees:
        - the left motor is 1 so that is easy
        - the right motor moves from -1 to 0

        We determine how far we are between 0 and 45 degrees (11.25 is 25% of 45) so we
        know that the right motor should be 25% of the way from -1 to 0...so -0.75 is the
        percentage for the right motor at 11.25 degrees.
        """

        if 0 <= angle <= 45:

            # left motor stays at 1
            left_speed_percentage = 1

            # right motor transitions from -1 to 0
            right_speed_percentage = -1 + (angle / 45.0)

        elif 45 < angle <= 90:

            # left motor stays at 1
            left_speed_percentage = 1

            # right motor transitions from 0 to 1
            percentage_from_45_to_90 = (angle - 45) / 45.0
            right_speed_percentage = percentage_from_45_to_90

        elif 90 < angle <= 135:

            # left motor transitions from 1 to 0
            percentage_from_90_to_135 = (angle - 90) / 45.0
            left_speed_percentage = 1 - percentage_from_90_to_135

            # right motor stays at 1
            right_speed_percentage = 1

        elif 135 < angle <= 180:

            # left motor transitions from 0 to -1
            percentage_from_135_to_180 = (angle - 135) / 45.0
            left_speed_percentage = -1 * percentage_from_135_to_180

            # right motor stays at 1
            right_speed_percentage = 1

        elif 180 < angle <= 225:

            # left motor transitions from -1 to 0
            percentage_from_180_to_225 = (angle - 180) / 45.0
            left_speed_percentage = -1 + percentage_from_180_to_225

            # right motor transitions from 1 to -1
            # right motor transitions from 1 to 0 between 180 and 202.5
            if angle < 202.5:
                percentage_from_180_to_202 = (angle - 180) / 22.5
                right_speed_percentage = 1 - percentage_from_180_to_202

            # right motor is 0 at 202.5
            elif angle == 202.5:
                right_speed_percentage = 0

            # right motor transitions from 0 to -1 between 202.5 and 225
            else:
                percentage_from_202_to_225 = (angle - 202.5) / 22.5
                right_speed_percentage = -1 * percentage_from_202_to_225

        elif 225 < angle <= 270:

            # left motor transitions from 0 to -1
            percentage_from_225_to_270 = (angle - 225) / 45.0
            left_speed_percentage = -1 * percentage_from_225_to_270

            # right motor stays at -1
            right_speed_percentage = -1

        elif 270 < angle <= 315:

            # left motor stays at -1
            left_speed_percentage = -1

            # right motor transitions from -1 to 0
            percentage_from_270_to_315 = (angle - 270) / 45.0
            right_speed_percentage = -1 + percentage_from_270_to_315

        elif 315 < angle <= 360:

            # left motor transitions from -1 to 1
            # left motor transitions from -1 to 0 between 315 and 337.5
            if angle < 337.5:
                percentage_from_315_to_337 = (angle - 315) / 22.5
                left_speed_percentage = (1 - percentage_from_315_to_337) * -1

            # left motor is 0 at 337.5
            elif angle == 337.5:
                left_speed_percentage = 0

            # left motor transitions from 0 to 1 between 337.5 and 360
            elif angle > 337.5:
                percentage_from_337_to_360 = (angle - 337.5) / 22.5
                left_speed_percentage = percentage_from_337_to_360

            # right motor transitions from 0 to -1
            percentage_from_315_to_360 = (angle - 315) / 45.0
            right_speed_percentage = -1 * percentage_from_315_to_360

        else:
            raise Exception(
                'You created a circle with more than 360 degrees ({})...that is quite the trick'.format(angle))

        return (left_speed_percentage * 100, right_speed_percentage * 100)
