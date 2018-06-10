# -----------------------------------------------------------------------------
# Copyright (c) 2015 Ralph Hempel <rhempel@hempeldesigngroup.com>
# Copyright (c) 2015 Anton Vanhoucke <antonvh@gmail.com>
# Copyright (c) 2015 Denis Demidov <dennis.demidov@gmail.com>
# Copyright (c) 2015 Eric Pascual <eric@pobot.org>
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

if sys.version_info < (3,4):
    raise SystemError('Must be using Python 3.4 or higher')

import select
import time
from logging import getLogger
from math import atan2, degrees as math_degrees, hypot
from os.path import abspath
from ev3dev2 import get_current_platform, Device, list_device_names

log = getLogger(__name__)

# The number of milliseconds we wait for the state of a motor to
# update to 'running' in the "on_for_XYZ" methods of the Motor class
WAIT_RUNNING_TIMEOUT = 100


# OUTPUT ports have platform specific values that we must import
platform = get_current_platform()

if platform == 'ev3':
    from ev3dev2._platform.ev3 import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D

elif platform == 'evb':
    from ev3dev2._platform.evb import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D

elif platform == 'pistorms':
    from ev3dev2._platform.pistorms import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D

elif platform == 'brickpi':
    from ev3dev2._platform.brickpi import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D

elif platform == 'brickpi3':
    from ev3dev2._platform.brickpi3 import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D

elif platform == 'fake':
    from ev3dev2._platform.fake import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D

else:
    raise Exception("Unsupported platform '%s'" % platform)


class SpeedInteger(int):
    pass


class SpeedRPS(SpeedInteger):
    """
    Speed in rotations-per-second
    """

    def __str__(self):
        return ("%d rps" % self)

    def get_speed_pct(self, motor):
        """
        Return the motor speed percentage to achieve desired rotations-per-second
        """
        assert self <= motor.max_rps, "%s max RPS is %s, %s was requested"  % (motor, motor.max_rps, self)
        return (self/motor.max_rps) * 100


class SpeedRPM(SpeedInteger):
    """
    Speed in rotations-per-minute
    """

    def __str__(self):
        return ("%d rpm" % self)

    def get_speed_pct(self, motor):
        """
        Return the motor speed percentage to achieve desired rotations-per-minute
        """
        assert self <= motor.max_rpm, "%s max RPM is %s, %s was requested"  % (motor, motor.max_rpm, self)
        return (self/motor.max_rpm) * 100


class SpeedDPS(SpeedInteger):
    """
    Speed in degrees-per-second
    """

    def __str__(self):
        return ("%d dps" % self)

    def get_speed_pct(self, motor):
        """
        Return the motor speed percentage to achieve desired degrees-per-second
        """
        assert self <= motor.max_dps, "%s max DPS is %s, %s was requested"  % (motor, motor.max_dps, self)
        return (self/motor.max_dps) * 100


class SpeedDPM(SpeedInteger):
    """
    Speed in degrees-per-minute
    """

    def __str__(self):
        return ("%d dpm" % self)

    def get_speed_pct(self, motor):
        """
        Return the motor speed percentage to achieve desired degrees-per-minute
        """
        assert self <= motor.max_dps, "%s max DPM is %s, %s was requested"  % (motor, motor.max_dpm, self)
        return (self/motor.max_dpm) * 100


class Motor(Device):

    """
    The motor class provides a uniform interface for using motors with
    positional and directional feedback such as the EV3 and NXT motors.
    This feedback allows for precise control of the motors. This is the
    most common type of motor, so we just call it `motor`.

    The way to configure a motor is to set the '_sp' attributes when
    calling a command or before. Only in 'run_direct' mode attribute
    changes are processed immediately, in the other modes they only
    take place when a new command is issued.
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

    #: Run to an absolute position specified by `position_sp` and then
    #: stop using the action specified in `stop_action`.
    COMMAND_RUN_TO_ABS_POS = 'run-to-abs-pos'

    #: Run to a position relative to the current `position` value.
    #: The new position will be current `position` + `position_sp`.
    #: When the new position is reached, the motor will stop using
    #: the action specified by `stop_action`.
    COMMAND_RUN_TO_REL_POS = 'run-to-rel-pos'

    #: Run the motor for the amount of time specified in `time_sp`
    #: and then stop the motor using the action specified by `stop_action`.
    COMMAND_RUN_TIMED = 'run-timed'

    #: Run the motor at the duty cycle specified by `duty_cycle_sp`.
    #: Unlike other run commands, changing `duty_cycle_sp` while running *will*
    #: take effect immediately.
    COMMAND_RUN_DIRECT = 'run-direct'

    #: Stop any of the run commands before they are complete using the
    #: action specified by `stop_action`.
    COMMAND_STOP = 'stop'

    #: Reset all of the motor parameter attributes to their default value.
    #: This will also have the effect of stopping the motor.
    COMMAND_RESET = 'reset'

    #: Sets the normal polarity of the rotary encoder.
    ENCODER_POLARITY_NORMAL = 'normal'

    #: Sets the inversed polarity of the rotary encoder.
    ENCODER_POLARITY_INVERSED = 'inversed'

    #: With `normal` polarity, a positive duty cycle will
    #: cause the motor to rotate clockwise.
    POLARITY_NORMAL = 'normal'

    #: With `inversed` polarity, a positive duty cycle will
    #: cause the motor to rotate counter-clockwise.
    POLARITY_INVERSED = 'inversed'

    #: Power is being sent to the motor.
    STATE_RUNNING = 'running'

    #: The motor is ramping up or down and has not yet reached a constant output level.
    STATE_RAMPING = 'ramping'

    #: The motor is not turning, but rather attempting to hold a fixed position.
    STATE_HOLDING = 'holding'

    #: The motor is turning, but cannot reach its `speed_sp`.
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
    #: will `push back` to maintain its position.
    STOP_ACTION_HOLD = 'hold'

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

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
        self.max_rps = float(self.max_speed/self.count_per_rot)
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
        Sends a command to the motor controller. See `commands` for a list of
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
        controller. Possible values are `run-forever`, `run-to-abs-pos`, `run-to-rel-pos`,
        `run-timed`, `run-direct`, `stop` and `reset`. Not all commands may be supported.

        - `run-forever` will cause the motor to run until another command is sent.
        - `run-to-abs-pos` will run to an absolute position specified by `position_sp`
          and then stop using the action specified in `stop_action`.
        - `run-to-rel-pos` will run to a position relative to the current `position` value.
          The new position will be current `position` + `position_sp`. When the new
          position is reached, the motor will stop using the action specified by `stop_action`.
        - `run-timed` will run the motor for the amount of time specified in `time_sp`
          and then stop the motor using the action specified by `stop_action`.
        - `run-direct` will run the motor at the duty cycle specified by `duty_cycle_sp`.
          Unlike other run commands, changing `duty_cycle_sp` while running *will*
          take effect immediately.
        - `stop` will stop any of the run commands before they are complete using the
          action specified by `stop_action`.
        - `reset` will reset all of the motor parameter attributes to their default value.
          This will also have the effect of stopping the motor.
        """
        self._commands, value = self.get_attr_set(self._commands, 'commands')
        return value

    @property
    def count_per_rot(self):
        """
        Returns the number of tacho counts in one rotation of the motor. Tacho counts
        are used by the position and speed attributes, so you can use this value
        to convert rotations or degrees to tacho counts. (rotation motors only)
        """
        self._count_per_rot, value = self.get_attr_int(self._count_per_rot, 'count_per_rot')
        return value

    @property
    def count_per_m(self):
        """
        Returns the number of tacho counts in one meter of travel of the motor. Tacho
        counts are used by the position and speed attributes, so you can use this
        value to convert from distance to tacho counts. (linear motors only)
        """
        self._count_per_m, value = self.get_attr_int(self._count_per_m, 'count_per_m')
        return value

    @property
    def driver_name(self):
        """
        Returns the name of the driver that provides this tacho motor device.
        """
        self._driver_name, value = self.get_attr_string(self._driver_name, 'driver_name')
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
        combined with the `count_per_m` atribute, you can use this value to
        calculate the maximum travel distance of the motor. (linear motors only)
        """
        self._full_travel_count, value = self.get_attr_int(self._full_travel_count, 'full_travel_count')
        return value

    @property
    def polarity(self):
        """
        Sets the polarity of the motor. With `normal` polarity, a positive duty
        cycle will cause the motor to rotate clockwise. With `inversed` polarity,
        a positive duty cycle will cause the motor to rotate counter-clockwise.
        Valid values are `normal` and `inversed`.
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
        Writing specifies the target position for the `run-to-abs-pos` and `run-to-rel-pos`
        commands. Reading returns the current value. Units are in tacho counts. You
        can use the value returned by `count_per_rot` to convert tacho counts to/from
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
        Returns the maximum value that is accepted by the `speed_sp` attribute. This
        may be slightly different than the maximum speed that a particular motor can
        reach - it's the maximum theoretical speed.
        """
        self._max_speed, value = self.get_attr_int(self._max_speed, 'max_speed')
        return value

    @property
    def speed(self):
        """
        Returns the current motor speed in tacho counts per second. Note, this is
        not necessarily degrees (although it is for LEGO motors). Use the `count_per_rot`
        attribute to convert this value to RPM or deg/sec.
        """
        self._speed, value = self.get_attr_int(self._speed, 'speed')
        return value

    @property
    def speed_sp(self):
        """
        Writing sets the target speed in tacho counts per second used for all `run-*`
        commands except `run-direct`. Reading returns the current value. A negative
        value causes the motor to rotate in reverse with the exception of `run-to-*-pos`
        commands where the sign is ignored. Use the `count_per_rot` attribute to convert
        RPM or deg/sec to tacho counts per second. Use the `count_per_m` attribute to
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
        motor speed will increase from 0 to 100% of `max_speed` over the span of this
        setpoint. The actual ramp time is the ratio of the difference between the
        `speed_sp` and the current `speed` and max_speed multiplied by `ramp_up_sp`.
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
        motor speed will decrease from 0 to 100% of `max_speed` over the span of this
        setpoint. The actual ramp time is the ratio of the difference between the
        `speed_sp` and the current `speed` and max_speed multiplied by `ramp_down_sp`.
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
        `running`, `ramping`, `holding`, `overloaded` and `stalled`.
        """
        self._state, value = self.get_attr_set(self._state, 'state')
        return value

    @property
    def stop_action(self):
        """
        Reading returns the current stop action. Writing sets the stop action.
        The value determines the motors behavior when `command` is set to `stop`.
        Also, it determines the motors behavior when a run command completes. See
        `stop_actions` for a list of possible values.
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
        Possible values are `coast`, `brake` and `hold`. `coast` means that power will
        be removed from the motor and it will freely coast to a stop. `brake` means
        that power will be removed from the motor and a passive electrical load will
        be placed on the motor. This is usually done by shorting the motor terminals
        together. This load will absorb the energy from the rotation of the motors and
        cause the motor to stop more quickly than coasting. `hold` does not remove
        power from the motor. Instead it actively tries to hold the motor at the current
        position. If an external force tries to turn the motor, the motor will 'push
        back' to maintain its position.
        """
        self._stop_actions, value = self.get_attr_set(self._stop_actions, 'stop_actions')
        return value

    @property
    def time_sp(self):
        """
        Writing specifies the amount of time the motor will run when using the
        `run-timed` command. Reading returns the current value. Units are in
        milliseconds.
        """
        self._time_sp, value = self.get_attr_int(self._time_sp, 'time_sp')
        return value

    @time_sp.setter
    def time_sp(self, value):
        self._time_sp = self.set_attr_int(self._time_sp, 'time_sp', value)

    def run_forever(self, **kwargs):
        """Run the motor until another command is sent.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_FOREVER

    def run_to_abs_pos(self, **kwargs):
        """Run to an absolute position specified by `position_sp` and then
        stop using the action specified in `stop_action`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_TO_ABS_POS

    def run_to_rel_pos(self, **kwargs):
        """Run to a position relative to the current `position` value.
        The new position will be current `position` + `position_sp`.
        When the new position is reached, the motor will stop using
        the action specified by `stop_action`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_TO_REL_POS

    def run_timed(self, **kwargs):
        """Run the motor for the amount of time specified in `time_sp`
        and then stop the motor using the action specified by `stop_action`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_TIMED

    def run_direct(self, **kwargs):
        """Run the motor at the duty cycle specified by `duty_cycle_sp`.
        Unlike other run commands, changing `duty_cycle_sp` while running *will*
        take effect immediately.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_DIRECT

    def stop(self, **kwargs):
        """Stop any of the run commands before they are complete using the
        action specified by `stop_action`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_STOP

    def reset(self, **kwargs):
        """Reset all of the motor parameter attributes to their default value.
        This will also have the effect of stopping the motor.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RESET

    @property
    def is_running(self):
        """Power is being sent to the motor.
        """
        return self.STATE_RUNNING in self.state

    @property
    def is_ramping(self):
        """The motor is ramping up or down and has not yet reached a constant output level.
        """
        return self.STATE_RAMPING in self.state

    @property
    def is_holding(self):
        """The motor is not turning, but rather attempting to hold a fixed position.
        """
        return self.STATE_HOLDING in self.state

    @property
    def is_overloaded(self):
        """The motor is turning, but cannot reach its `speed_sp`.
        """
        return self.STATE_OVERLOADED in self.state

    @property
    def is_stalled(self):
        """The motor is not turning when it should be.
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

        while True:
            self._poll.poll(None if timeout is None else timeout)

            if timeout is not None and time.time() >= tic + timeout / 1000:
                return False

            if cond(self.state):
                return True

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

    def _speed_pct(self, speed_pct):

        # If speed_pct is SpeedInteger object we must convert
        # SpeedRPS, etc to an actual speed percentage
        if isinstance(speed_pct, SpeedInteger):
            speed_pct = speed_pct.get_speed_pct(self)

        assert -100 <= speed_pct <= 100,\
            "%s is an invalid speed_pct, must be between -100 and 100 (inclusive)" % speed_pct

        return speed_pct

    def _set_position_rotations(self, speed_pct, rotations):

        # +/- speed is used to control direction, rotations must be positive
        assert rotations >= 0, "rotations is %s, must be >= 0" % rotations

        if speed_pct > 0:
            self.position_sp = self.position + int(rotations * self.count_per_rot)
        else:
            self.position_sp = self.position - int(rotations * self.count_per_rot)

    def _set_position_degrees(self, speed_pct, degrees):

        # +/- speed is used to control direction, degrees must be positive
        assert degrees >= 0, "degrees is %s, must be >= 0" % degrees

        if speed_pct > 0:
            self.position_sp = self.position + int((degrees * self.count_per_rot)/360)
        else:
            self.position_sp = self.position - int((degrees * self.count_per_rot)/360)

    def _set_brake(self, brake):
        if brake:
            self.stop_action = self.STOP_ACTION_HOLD
        else:
            self.stop_action = self.STOP_ACTION_COAST

    def on_for_rotations(self, speed_pct, rotations, brake=True, block=True):
        """
        Rotate the motor at 'speed_pct' for 'rotations'

        'speed_pct' can be an integer or a SpeedInteger object which will be
        converted to an actual speed percentage in _speed_pct()
        """
        speed_pct = self._speed_pct(speed_pct)

        if not speed_pct or not rotations:
            log.warning("%s speed_pct is %s but rotations is %s, motor will not move" % (self, speed_pct, rotations))
            self._set_brake(brake)
            return

        self.speed_sp = int((speed_pct * self.max_speed) / 100)
        self._set_position_rotations(speed_pct, rotations)
        self._set_brake(brake)
        self.run_to_abs_pos()

        if block:
            self.wait_until('running', timeout=WAIT_RUNNING_TIMEOUT)
            self.wait_until_not_moving()

    def on_for_degrees(self, speed_pct, degrees, brake=True, block=True):
        """
        Rotate the motor at 'speed_pct' for 'degrees'

        'speed_pct' can be an integer or a SpeedInteger object which will be
        converted to an actual speed percentage in _speed_pct()
        """
        speed_pct = self._speed_pct(speed_pct)

        if not speed_pct or not degrees:
            log.warning("%s speed_pct is %s but degrees is %s, motor will not move" % (self, speed_pct, degrees))
            self._set_brake(brake)
            return

        self.speed_sp = int((speed_pct * self.max_speed) / 100)
        self._set_position_degrees(speed_pct, degrees)
        self._set_brake(brake)
        self.run_to_abs_pos()

        if block:
            self.wait_until('running', timeout=WAIT_RUNNING_TIMEOUT)
            self.wait_until_not_moving()

    def on_to_position(self, speed_pct, position, brake=True, block=True):
        """
        Rotate the motor at 'speed_pct' to 'position'

        'speed_pct' can be an integer or a SpeedInteger object which will be
        converted to an actual speed percentage in _speed_pct()
        """
        speed_pct = self._speed_pct(speed_pct)

        if not speed_pct:
            log.warning("%s speed_pct is %s, motor will not move" % (self, speed_pct))
            self._set_brake(brake)
            return

        self.speed_sp = int((speed_pct * self.max_speed) / 100)
        self.position_sp = position
        self._set_brake(brake)
        self.run_to_abs_pos()

        if block:
            self.wait_until('running', timeout=WAIT_RUNNING_TIMEOUT)
            self.wait_until_not_moving()

    def on_for_seconds(self, speed_pct, seconds, brake=True, block=True):
        """
        Rotate the motor at 'speed_pct' for 'seconds'

        'speed_pct' can be an integer or a SpeedInteger object which will be
        converted to an actual speed percentage in _speed_pct()
        """
        speed_pct = self._speed_pct(speed_pct)

        if not speed_pct or not seconds:
            log.warning("%s speed_pct is %s but seconds is %s, motor will not move" % (self, speed_pct, seconds))
            self._set_brake(brake)
            return

        self.speed_sp = int((speed_pct * self.max_speed) / 100)
        self.time_sp = int(seconds * 1000)
        self._set_brake(brake)
        self.run_timed()

        if block:
            self.wait_until('running', timeout=WAIT_RUNNING_TIMEOUT)
            self.wait_until_not_moving()

    def on(self, speed_pct, brake=True, block=False):
        """
        Rotate the motor at 'speed_pct' for forever

        'speed_pct' can be an integer or a SpeedInteger object which will be
        converted to an actual speed percentage in _speed_pct()

        Note that `block` is False by default, this is different from the
        other `on_for_XYZ` methods
        """
        speed_pct = self._speed_pct(speed_pct)

        if not speed_pct:
            log.warning("%s speed_pct is %s, motor will not move" % (self, speed_pct))
            self._set_brake(brake)
            return

        self.speed_sp = int((speed_pct * self.max_speed) / 100)
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

    return (Motor(name_pattern=name, name_exact=True)
            for name in list_device_names(class_path, name_pattern, **kwargs))

class LargeMotor(Motor):

    """
    EV3/NXT large servo motor
    """

    SYSTEM_CLASS_NAME = Motor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = '*'
    __slots__ = []

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        super(LargeMotor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-l-motor', 'lego-nxt-motor'], **kwargs)


class MediumMotor(Motor):

    """
    EV3 medium servo motor
    """

    SYSTEM_CLASS_NAME = Motor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = '*'
    __slots__ = []

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        super(MediumMotor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-m-motor'], **kwargs)


class ActuonixL1250Motor(Motor):

    """
    Actuonix L12 50 linear servo motor
    """

    SYSTEM_CLASS_NAME = Motor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = 'linear*'
    __slots__ = []

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        super(ActuonixL1250Motor, self).__init__(address, name_pattern, name_exact, driver_name=['act-l12-ev3-50'], **kwargs)


class ActuonixL12100Motor(Motor):

    """
    Actuonix L12 100 linear servo motor
    """

    SYSTEM_CLASS_NAME = Motor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = 'linear*'
    __slots__ = []

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        super(ActuonixL12100Motor, self).__init__(address, name_pattern, name_exact, driver_name=['act-l12-ev3-100'], **kwargs)


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
        Sets the command for the motor. Possible values are `run-forever`, `run-timed` and
        `stop`. Not all commands may be supported, so be sure to check the contents
        of the `commands` attribute.
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
        Sets the polarity of the motor. Valid values are `normal` and `inversed`.
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
        flags are `running` and `ramping`. `running` indicates that the motor is
        powered. `ramping` indicates that the motor has not yet reached the
        `duty_cycle_sp`.
        """
        self._state, value = self.get_attr_set(self._state, 'state')
        return value

    @property
    def stop_action(self):
        """
        Sets the stop action that will be used when the motor stops. Read
        `stop_actions` to get the list of valid values.
        """
        raise Exception("stop_action is a write-only property!")

    @stop_action.setter
    def stop_action(self, value):
        self._stop_action = self.set_attr_string(self._stop_action, 'stop_action', value)

    @property
    def stop_actions(self):
        """
        Gets a list of stop actions. Valid values are `coast`
        and `brake`.
        """
        self._stop_actions, value = self.get_attr_set(self._stop_actions, 'stop_actions')
        return value

    @property
    def time_sp(self):
        """
        Writing specifies the amount of time the motor will run when using the
        `run-timed` command. Reading returns the current value. Units are in
        milliseconds.
        """
        self._time_sp, value = self.get_attr_int(self._time_sp, 'time_sp')
        return value

    @time_sp.setter
    def time_sp(self, value):
        self._time_sp = self.set_attr_int(self._time_sp, 'time_sp', value)

    #: Run the motor until another command is sent.
    COMMAND_RUN_FOREVER = 'run-forever'

    #: Run the motor for the amount of time specified in `time_sp`
    #: and then stop the motor using the action specified by `stop_action`.
    COMMAND_RUN_TIMED = 'run-timed'

    #: Run the motor at the duty cycle specified by `duty_cycle_sp`.
    #: Unlike other run commands, changing `duty_cycle_sp` while running *will*
    #: take effect immediately.
    COMMAND_RUN_DIRECT = 'run-direct'

    #: Stop any of the run commands before they are complete using the
    #: action specified by `stop_action`.
    COMMAND_STOP = 'stop'

    #: With `normal` polarity, a positive duty cycle will
    #: cause the motor to rotate clockwise.
    POLARITY_NORMAL = 'normal'

    #: With `inversed` polarity, a positive duty cycle will
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
        """Run the motor until another command is sent.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_FOREVER

    def run_timed(self, **kwargs):
        """Run the motor for the amount of time specified in `time_sp`
        and then stop the motor using the action specified by `stop_action`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_TIMED

    def run_direct(self, **kwargs):
        """Run the motor at the duty cycle specified by `duty_cycle_sp`.
        Unlike other run commands, changing `duty_cycle_sp` while running *will*
        take effect immediately.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_DIRECT

    def stop(self, **kwargs):
        """Stop any of the run commands before they are complete using the
        action specified by `stop_action`.
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
        Sets the command for the servo. Valid values are `run` and `float`. Setting
        to `run` will cause the servo to be driven to the position_sp set in the
        `position_sp` attribute. Setting to `float` will remove power from the motor.
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
        Sets the polarity of the servo. Valid values are `normal` and `inversed`.
        Setting the value to `inversed` will cause the position_sp value to be
        inversed. i.e `-100` will correspond to `max_pulse_sp`, and `100` will
        correspond to `min_pulse_sp`.
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
        are -100 to 100 (-100% to 100%) where `-100` corresponds to `min_pulse_sp`,
        `0` corresponds to `mid_pulse_sp` and `100` corresponds to `max_pulse_sp`.
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
        case reading and writing will fail with `-EOPNOTSUPP`. In continuous rotation
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
        * `running`: Indicates that the motor is powered.
        """
        self._state, value = self.get_attr_set(self._state, 'state')
        return value

    #: Drive servo to the position set in the `position_sp` attribute.
    COMMAND_RUN = 'run'

    #: Remove power from the motor.
    COMMAND_FLOAT = 'float'

    #: With `normal` polarity, a positive duty cycle will
    #: cause the motor to rotate clockwise.
    POLARITY_NORMAL = 'normal'

    #: With `inversed` polarity, a positive duty cycle will
    #: cause the motor to rotate counter-clockwise.
    POLARITY_INVERSED = 'inversed'

    def run(self, **kwargs):
        """Drive servo to the position set in the `position_sp` attribute.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN

    def float(self, **kwargs):
        """Remove power from the motor.
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
        self.motors = {}
        for motor_port in sorted(motor_specs.keys()):
            motor_class = motor_specs[motor_port]
            self.motors[motor_port] = motor_class(motor_port)

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
                        #log.error("%s %s cannot set %s to %s" % (self, motor, key, kwargs[key]))
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
                    #log.debug("%s: %s set %s to %s" % (self, motor, key, kwargs[key]))
                    setattr(motor, key, kwargs[key])

        for motor in motors:
            motor.command = kwargs['command']
            #log.debug("%s: %s command %s" % (self, motor, kwargs['command']))

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

    def stop(self, motors=None):
        motors = motors if motors is not None else self.motors.values()

        for motor in motors:
            motor.stop()

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
    def is_stalled(self):
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


class MoveTank(MotorSet):

    def __init__(self, left_motor_port, right_motor_port, desc=None, motor_class=LargeMotor):
        motor_specs = {
            left_motor_port : motor_class,
            right_motor_port : motor_class,
        }

        MotorSet.__init__(self, motor_specs, desc)
        self.left_motor = self.motors[left_motor_port]
        self.right_motor = self.motors[right_motor_port]
        self.max_speed = self.left_motor.max_speed

    def _block(self):
        self.left_motor.wait_until('running', timeout=WAIT_RUNNING_TIMEOUT)
        self.right_motor.wait_until('running', timeout=WAIT_RUNNING_TIMEOUT)
        self.left_motor.wait_until_not_moving()
        self.right_motor.wait_until_not_moving()

    def _validate_speed_pct(self, left_speed_pct, right_speed_pct):
        assert left_speed_pct >= -100 and left_speed_pct <= 100,\
            "%s is an invalid left_speed_pct, must be between -100 and 100 (inclusive)" % left_speed_pct
        assert right_speed_pct >= -100 and right_speed_pct <= 100,\
            "%s is an invalid right_speed_pct, must be between -100 and 100 (inclusive)" % right_speed_pct
        assert left_speed_pct or right_speed_pct,\
            "Either left_speed_pct or right_speed_pct must be non-zero"

    def on_for_rotations(self, left_speed_pct, right_speed_pct, rotations, brake=True, block=True):
        """
        Rotate the motor at 'left_speed & right_speed' for 'rotations'
        """
        self._validate_speed_pct(left_speed_pct, right_speed_pct)
        left_speed = int((left_speed_pct * self.max_speed) / 100)
        right_speed = int((right_speed_pct * self.max_speed) / 100)

        if left_speed > right_speed:
            left_rotations = rotations
            right_rotations = abs(float(right_speed / left_speed)) * rotations
        else:
            left_rotations = abs(float(left_speed / right_speed)) * rotations
            right_rotations = rotations

        # Set all parameters
        self.left_motor.speed_sp = left_speed
        self.left_motor._set_position_rotations(left_speed, left_rotations)
        self.left_motor._set_brake(brake)
        self.right_motor.speed_sp = right_speed
        self.right_motor._set_position_rotations(right_speed, right_rotations)
        self.right_motor._set_brake(brake)

        # Start the motors
        self.left_motor.run_to_abs_pos()
        self.right_motor.run_to_abs_pos()

        if block:
            self._block()

    def on_for_degrees(self, left_speed_pct, right_speed_pct, degrees, brake=True, block=True):
        """
        Rotate the motor at 'left_speed & right_speed' for 'degrees'
        """
        self._validate_speed_pct(left_speed_pct, right_speed_pct)
        left_speed = int((left_speed_pct * self.max_speed) / 100)
        right_speed = int((right_speed_pct * self.max_speed) / 100)

        if left_speed > right_speed:
            left_degrees = degrees
            right_degrees = float(right_speed / left_speed) * degrees
        else:
            left_degrees = float(left_speed / right_speed) * degrees
            right_degrees = degrees

        # Set all parameters
        self.left_motor.speed_sp = left_speed
        self.left_motor._set_position_degrees(left_speed, left_degrees)
        self.left_motor._set_brake(brake)
        self.right_motor.speed_sp = right_speed
        self.right_motor._set_position_degrees(right_speed, right_degrees)
        self.right_motor._set_brake(brake)

        # Start the motors
        self.left_motor.run_to_abs_pos()
        self.right_motor.run_to_abs_pos()

        if block:
            self._block()

    def on_for_seconds(self, left_speed_pct, right_speed_pct, seconds, brake=True, block=True):
        """
        Rotate the motor at 'left_speed & right_speed' for 'seconds'
        """
        self._validate_speed_pct(left_speed_pct, right_speed_pct)

        # Set all parameters
        self.left_motor.speed_sp = int((left_speed_pct * self.max_speed) / 100)
        self.left_motor.time_sp = int(seconds * 1000)
        self.left_motor._set_brake(brake)
        self.right_motor.speed_sp = int((right_speed_pct * self.max_speed) / 100)
        self.right_motor.time_sp = int(seconds * 1000)
        self.right_motor._set_brake(brake)

        # Start the motors
        self.left_motor.run_timed()
        self.right_motor.run_timed()

        if block:
            self._block()

    def on(self, left_speed_pct, right_speed_pct):
        """
        Rotate the motor at 'left_speed & right_speed' for forever
        """
        self._validate_speed_pct(left_speed_pct, right_speed_pct)
        self.left_motor.speed_sp = int((left_speed_pct * self.max_speed) / 100)
        self.right_motor.speed_sp = int((right_speed_pct * self.max_speed) / 100)

        # Start the motors
        self.left_motor.run_forever()
        self.right_motor.run_forever()

    def off(self, brake=True):
        self.left_motor._set_brake(brake)
        self.right_motor._set_brake(brake)
        self.left_motor.stop()
        self.right_motor.stop()


class MoveSteering(MoveTank):

    def get_speed_steering(self, steering, speed_pct):
        """
        Calculate the speed_sp for each motor in a pair to achieve the specified
        steering. Note that calling this function alone will not make the
        motors move, it only sets the speed. A run_* function must be called
        afterwards to make the motors move.

        steering [-100, 100]:
            * -100 means turn left as fast as possible,
            *  0   means drive in a straight line, and
            *  100 means turn right as fast as possible.

        speed_pct:
            The speed that should be applied to the outmost motor (the one
            rotating faster). The speed of the other motor will be computed
            automatically.
        """

        assert steering >= -100 and steering <= 100,\
            "%s is an invalid steering, must be between -100 and 100 (inclusive)" % steering
        assert speed_pct >= -100 and speed_pct <= 100,\
            "%s is an invalid speed_pct, must be between -100 and 100 (inclusive)" % speed_pct

        left_speed = int((speed_pct * self.max_speed) / 100)
        right_speed = left_speed
        speed = (50 - abs(float(steering))) / 50

        if steering >= 0:
            right_speed *= speed
        else:
            left_speed *= speed

        left_speed_pct = int((left_speed * 100) / self.left_motor.max_speed)
        right_speed_pct = int((right_speed * 100) / self.right_motor.max_speed)
        #log.debug("%s: steering %d, %s speed %d, %s speed %d" %
        #    (self, steering, self.left_motor, left_speed_pct, self.right_motor, right_speed_pct))

        return (left_speed_pct, right_speed_pct)

    def on_for_rotations(self, steering, speed_pct, rotations, brake=True, block=True):
        (left_speed_pct, right_speed_pct) = self.get_speed_steering(steering, speed_pct)
        MoveTank.on_for_rotations(self, left_speed_pct, right_speed_pct, rotations, brake, block)

    def on_for_degrees(self, steering, speed_pct, degrees, brake=True, block=True):
        (left_speed_pct, right_speed_pct) = self.get_speed_steering(steering, speed_pct)
        MoveTank.on_for_degrees(self, left_speed_pct, right_speed_pct, degrees, brake, block)

    def on_for_seconds(self, steering, speed_pct, seconds, brake=True, block=True):
        (left_speed_pct, right_speed_pct) = self.get_speed_steering(steering, speed_pct)
        MoveTank.on_for_seconds(self, left_speed_pct, right_speed_pct, seconds, brake, block)

    def on(self, steering, speed_pct):
        (left_speed_pct, right_speed_pct) = self.get_speed_steering(steering, speed_pct)
        MoveTank.on(self, left_speed_pct, right_speed_pct)


class MoveJoystick(MoveTank):
    """
    Used to control a pair of motors via a joystick
    """

    def angle_to_speed_percentage(self, angle):
        """
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
            right_speed_percentage = -1 + (angle/45.0)

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
            raise Exception('You created a circle with more than 360 degrees (%s)...that is quite the trick' % angle)

        return (left_speed_percentage * 100, right_speed_percentage * 100)

    def on(self, x, y, max_speed, radius=100.0):
        """
        Convert x,y joystick coordinates to left/right motor speed percentages
        and move the motors
        """

        # If joystick is in the middle stop the tank
        if not x and not y:
            MoveTank.off()
            return

        vector_length = hypot(x, y)
        angle = math_degrees(atan2(y, x))

        if angle < 0:
            angle += 360

        # Should not happen but can happen (just by a hair) due to floating point math
        if vector_length > radius:
            vector_length = radius

        (init_left_speed_percentage, init_right_speed_percentage) = self.angle_to_speed_percentage(angle)

        # scale the speed percentages based on vector_length vs. radius
        left_speed_percentage = (init_left_speed_percentage * vector_length) / radius
        right_speed_percentage = (init_right_speed_percentage * vector_length) / radius

        log.debug("""
    x, y                         : %s, %s
    radius                       : %s
    angle                        : %s
    vector length                : %s
    init left_speed_percentage   : %s
    init right_speed_percentage  : %s
    final left_speed_percentage  : %s
    final right_speed_percentage : %s
    """ % (x, y, radius, angle, vector_length,
            init_left_speed_percentage, init_right_speed_percentage,
            left_speed_percentage, right_speed_percentage))

        MoveTank.on(self, left_speed_percentage, right_speed_percentage)
