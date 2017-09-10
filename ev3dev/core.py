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

# ~autogen autogen-header
# Sections of the following code were auto-generated based on spec v1.2.0

# ~autogen

# -----------------------------------------------------------------------------

import sys

if sys.version_info < (3,4):
    raise SystemError('Must be using Python 3.4 or higher')

# -----------------------------------------------------------------------------

import os
import io
import fnmatch
import numbers
import array
import re
import select
import shlex
import stat
import time
import errno
from os.path import abspath
from struct import pack, unpack

try:
    # This is a linux-specific module.
    # It is required by the Button() class, but failure to import it may be
    # safely ignored if one just needs to run API tests on Windows.
    import fcntl
except ImportError:
    print("WARNING: Failed to import fcntl. Button class will be unuseable!")

INPUT_AUTO = ''
OUTPUT_AUTO = ''

# -----------------------------------------------------------------------------
def list_device_names(class_path, name_pattern, **kwargs):
    """
    This is a generator function that lists names of all devices matching the
    provided parameters.

    Parameters:
	class_path: class path of the device, a subdirectory of /sys/class.
	    For example, '/sys/class/tacho-motor'.
	name_pattern: pattern that device name should match.
	    For example, 'sensor*' or 'motor*'. Default value: '*'.
	keyword arguments: used for matching the corresponding device
	    attributes. For example, address='outA', or
	    driver_name=['lego-ev3-us', 'lego-nxt-us']. When argument value
	    is a list, then a match against any entry of the list is
	    enough.
    """

    if not os.path.isdir(class_path):
        return

    def matches(attribute, pattern):
        try:
            with io.FileIO(attribute) as f:
                value = f.read().strip().decode()
        except:
            return False

        if isinstance(pattern, list):
            return any([value.find(p) >= 0 for p in pattern])
        else:
            return value.find(pattern) >= 0

    for f in os.listdir(class_path):
        if fnmatch.fnmatch(f, name_pattern):
            path = class_path + '/' + f
            if all([matches(path + '/' + k, kwargs[k]) for k in kwargs]):
                yield f

# -----------------------------------------------------------------------------
# Define the base class from which all other ev3dev classes are defined.

class Device(object):
    """The ev3dev device base class"""

    __slots__ = ['_path', 'connected', '_device_index', 'kwargs']

    DEVICE_ROOT_PATH = '/sys/class'

    _DEVICE_INDEX = re.compile(r'^.*(\d+)$')

    def __init__(self, class_name, name_pattern='*', name_exact=False, **kwargs):
        """Spin through the Linux sysfs class for the device type and find
        a device that matches the provided name pattern and attributes (if any).

        Parameters:
            class_name: class name of the device, a subdirectory of /sys/class.
                For example, 'tacho-motor'.
            name_pattern: pattern that device name should match.
                For example, 'sensor*' or 'motor*'. Default value: '*'.
            name_exact: when True, assume that the name_pattern provided is the
                exact device name and use it directly.
            keyword arguments: used for matching the corresponding device
                attributes. For example, address='outA', or
                driver_name=['lego-ev3-us', 'lego-nxt-us']. When argument value
                is a list, then a match against any entry of the list is
                enough.

        Example::

            d = ev3dev.Device('tacho-motor', address='outA')
            s = ev3dev.Device('lego-sensor', driver_name=['lego-ev3-us', 'lego-nxt-us'])

        When connected succesfully, the `connected` attribute is set to True.
        """

        classpath = abspath(Device.DEVICE_ROOT_PATH + '/' + class_name)
        self.kwargs = kwargs

        def get_index(file):
            match = Device._DEVICE_INDEX.match(file)
            if match:
                return int(match.group(1))
            else:
                return None

        if name_exact:
            self._path = classpath + '/' + name_pattern
            self._device_index = get_index(name_pattern)
            self.connected = True
        else:
            try:
                name = next(list_device_names(classpath, name_pattern, **kwargs))
                self._path = classpath + '/' + name
                self._device_index = get_index(name)
                self.connected = True
            except StopIteration:
                self._path = None
                self._device_index = None
                self.connected = False

    def __str__(self):
        if 'address' in self.kwargs:
            return "%s(%s)" % (self.__class__.__name__, self.kwargs.get('address'))
        else:
            return self.__class__.__name__

    def _attribute_file_open( self, name ):
        path = self._path + '/' + name
        mode = stat.S_IMODE(os.stat(path)[stat.ST_MODE])
        r_ok = mode & stat.S_IRGRP
        w_ok = mode & stat.S_IWGRP

        if r_ok and w_ok:
            mode = 'r+'
        elif w_ok:
            mode = 'w'
        else:
            mode = 'r'

        return io.FileIO(path, mode)

    def _get_attribute(self, attribute, name):
        """Device attribute getter"""
        if self.connected:
            if None == attribute:
                attribute = self._attribute_file_open( name )
            else:
                attribute.seek(0)
            return attribute, attribute.read().strip().decode()
        else:
            raise Exception('Device is not connected')

    def _set_attribute(self, attribute, name, value):
        """Device attribute setter"""
        if self.connected:
            if None == attribute:
                attribute = self._attribute_file_open( name )
            else:
                attribute.seek(0)

            try:
                attribute.write(value.encode())
                attribute.flush()
            except Exception as ex:
                self._raise_friendly_access_error(ex, name)
            return attribute
        else:
            raise Exception('Device is not connected')

    def _raise_friendly_access_error(self, driver_error, attribute):
        if not isinstance(driver_error, OSError):
            raise driver_error

        if driver_error.errno == errno.EINVAL:
            if attribute == "speed_sp":
                try:
                    max_speed = self.max_speed
                except (AttributeError, Exception):
                    raise ValueError("The given speed value was out of range") from driver_error
                else:
                    raise ValueError("The given speed value was out of range. Max speed: +/-" + str(max_speed)) from driver_error
            raise ValueError("One or more arguments were out of range or invalid") from driver_error
        raise driver_error

    def get_attr_int(self, attribute, name):
        attribute, value = self._get_attribute(attribute, name)
        return attribute, int(value)

    def set_attr_int(self, attribute, name, value):
        return self._set_attribute(attribute, name, str(int(value)))

    def get_attr_string(self, attribute, name):
        return self._get_attribute(attribute, name)

    def set_attr_string(self, attribute, name, value):
        return self._set_attribute(attribute, name, value)

    def get_attr_line(self, attribute, name):
        return self._get_attribute(attribute, name)

    def get_attr_set(self, attribute, name):
        attribute, value = self.get_attr_line(attribute, name)
        return attribute, [v.strip('[]') for v in value.split()]

    def get_attr_from_set(self, attribute, name):
        attribute, value = self.get_attr_line(attribute, name)
        for a in value.split():
            v = a.strip('[]')
            if v != a:
                return v
        return ""

    @property
    def device_index(self):
        return self._device_index

def list_devices(class_name, name_pattern, **kwargs):
    """
    This is a generator function that takes same arguments as `Device` class
    and enumerates all devices present in the system that match the provided
    arguments.

    Parameters:
	class_name: class name of the device, a subdirectory of /sys/class.
	    For example, 'tacho-motor'.
	name_pattern: pattern that device name should match.
	    For example, 'sensor*' or 'motor*'. Default value: '*'.
	keyword arguments: used for matching the corresponding device
	    attributes. For example, address='outA', or
	    driver_name=['lego-ev3-us', 'lego-nxt-us']. When argument value
	    is a list, then a match against any entry of the list is
	    enough.
    """
    classpath = abspath(Device.DEVICE_ROOT_PATH + '/' + class_name)

    return (Device(class_name, name, name_exact=True)
            for name in list_device_names(classpath, name_pattern, **kwargs))

# ~autogen generic-class classes.motor>currentClass

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

# ~autogen

        self._poll = None

    __slots__ = [
# ~autogen generic-class-slots classes.motor>currentClass

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

# ~autogen
    '_poll',
    ]

# ~autogen generic-get-set classes.motor>currentClass

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
        can use the value returned by `counts_per_rot` to convert tacho counts to/from
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


# ~autogen
# ~autogen generic-property-value classes.motor>currentClass

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


# ~autogen
# ~autogen motor_commands classes.motor>currentClass

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


# ~autogen
# ~autogen motor_states classes.motor>currentClass

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


# ~autogen

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

# ~autogen generic-class classes.largeMotor>currentClass

class LargeMotor(Motor):

    """
    EV3/NXT large servo motor
    """

    SYSTEM_CLASS_NAME = Motor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = '*'

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        super(LargeMotor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-l-motor', 'lego-nxt-motor'], **kwargs)


# ~autogen
    __slots__ = [
# ~autogen generic-class-slots classes.largeMotor>currentClass


# ~autogen
    ]
# ~autogen generic-class classes.mediumMotor>currentClass

class MediumMotor(Motor):

    """
    EV3 medium servo motor
    """

    SYSTEM_CLASS_NAME = Motor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = '*'

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        super(MediumMotor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-m-motor'], **kwargs)


# ~autogen
    __slots__ = [
# ~autogen generic-class-slots classes.mediumMotor>currentClass


# ~autogen
    ]
# ~autogen generic-class classes.actuonix50Motor>currentClass

class ActuonixL1250Motor(Motor):

    """
    Actuonix L12 50 linear servo motor
    """

    SYSTEM_CLASS_NAME = Motor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = 'linear*'

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        super(ActuonixL1250Motor, self).__init__(address, name_pattern, name_exact, driver_name=['act-l12-ev3-50'], **kwargs)


# ~autogen
    __slots__ = [
# ~autogen generic-class-slots classes.actuonix50Motor>currentClass


# ~autogen
    ]
# ~autogen generic-class classes.actuonix100Motor>currentClass

class ActuonixL12100Motor(Motor):

    """
    Actuonix L12 100 linear servo motor
    """

    SYSTEM_CLASS_NAME = Motor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = 'linear*'

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        super(ActuonixL12100Motor, self).__init__(address, name_pattern, name_exact, driver_name=['act-l12-ev3-100'], **kwargs)


# ~autogen
    __slots__ = [
# ~autogen generic-class-slots classes.actuonix100Motor>currentClass


# ~autogen
    ]
# ~autogen generic-class classes.dcMotor>currentClass

class DcMotor(Device):

    """
    The DC motor class provides a uniform interface for using regular DC motors
    with no fancy controls or feedback. This includes LEGO MINDSTORMS RCX motors
    and LEGO Power Functions motors.
    """

    SYSTEM_CLASS_NAME = 'dc-motor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'motor*'

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

# ~autogen

    __slots__ = [
# ~autogen generic-class-slots classes.dcMotor>currentClass

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

# ~autogen
    ]

# ~autogen generic-get-set classes.dcMotor>currentClass

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


# ~autogen
# ~autogen generic-property-value classes.dcMotor>currentClass

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


# ~autogen
# ~autogen motor_commands classes.dcMotor>currentClass

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


# ~autogen
# ~autogen generic-class classes.servoMotor>currentClass

class ServoMotor(Device):

    """
    The servo motor class provides a uniform interface for using hobby type
    servo motors.
    """

    SYSTEM_CLASS_NAME = 'servo-motor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'motor*'

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

# ~autogen

    __slots__ = [
# ~autogen generic-class-slots classes.servoMotor>currentClass

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

# ~autogen
    ]

# ~autogen generic-get-set classes.servoMotor>currentClass

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


# ~autogen
# ~autogen generic-property-value classes.servoMotor>currentClass

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


# ~autogen
# ~autogen motor_commands classes.servoMotor>currentClass

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


# ~autogen
# ~autogen generic-class classes.sensor>currentClass

class Sensor(Device):

    """
    The sensor class provides a uniform interface for using most of the
    sensors available for the EV3. The various underlying device drivers will
    create a `lego-sensor` device for interacting with the sensors.

    Sensors are primarily controlled by setting the `mode` and monitored by
    reading the `value<N>` attributes. Values can be converted to floating point
    if needed by `value<N>` / 10.0 ^ `decimals`.

    Since the name of the `sensor<N>` device node does not correspond to the port
    that a sensor is plugged in to, you must look at the `address` attribute if
    you need to know which port a sensor is plugged in to. However, if you don't
    have more than one sensor of each type, you can just look for a matching
    `driver_name`. Then it will not matter which port a sensor is plugged in to - your
    program will still work.
    """

    SYSTEM_CLASS_NAME = 'lego-sensor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'sensor*'

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        if address is not None:
            kwargs['address'] = address
        super(Sensor, self).__init__(self.SYSTEM_CLASS_NAME, name_pattern, name_exact, **kwargs)

        self._address = None
        self._command = None
        self._commands = None
        self._decimals = None
        self._driver_name = None
        self._mode = None
        self._modes = None
        self._num_values = None
        self._units = None

# ~autogen

        self._value = [None,None,None,None,None,None,None,None]

        self._bin_data_format = None
        self._bin_data_size = None
        self._bin_data = None
        self._mode_scale = {}

    __slots__ = [
# ~autogen generic-class-slots classes.sensor>currentClass

    '_address',
    '_command',
    '_commands',
    '_decimals',
    '_driver_name',
    '_mode',
    '_modes',
    '_num_values',
    '_units',

# ~autogen
    '_value',
    '_bin_data_format',
    '_bin_data_size',
    '_bin_data',
    '_mode_scale'
    ]

    def _scale(self, mode):
        """
        Returns value scaling coefficient for the given mode.
        """
        if mode in self._mode_scale:
            scale = self._mode_scale[mode]
        else:
            scale = 10**(-self.decimals)
            self._mode_scale[mode] = scale

        return scale

# ~autogen generic-get-set classes.sensor>currentClass

    @property
    def address(self):
        """
        Returns the name of the port that the sensor is connected to, e.g. `ev3:in1`.
        I2C sensors also include the I2C address (decimal), e.g. `ev3:in1:i2c8`.
        """
        self._address, value = self.get_attr_string(self._address, 'address')
        return value

    @property
    def command(self):
        """
        Sends a command to the sensor.
        """
        raise Exception("command is a write-only property!")

    @command.setter
    def command(self, value):
        self._command = self.set_attr_string(self._command, 'command', value)

    @property
    def commands(self):
        """
        Returns a list of the valid commands for the sensor.
        Returns -EOPNOTSUPP if no commands are supported.
        """
        self._commands, value = self.get_attr_set(self._commands, 'commands')
        return value

    @property
    def decimals(self):
        """
        Returns the number of decimal places for the values in the `value<N>`
        attributes of the current mode.
        """
        self._decimals, value = self.get_attr_int(self._decimals, 'decimals')
        return value

    @property
    def driver_name(self):
        """
        Returns the name of the sensor device/driver. See the list of [supported
        sensors] for a complete list of drivers.
        """
        self._driver_name, value = self.get_attr_string(self._driver_name, 'driver_name')
        return value

    @property
    def mode(self):
        """
        Returns the current mode. Writing one of the values returned by `modes`
        sets the sensor to that mode.
        """
        self._mode, value = self.get_attr_string(self._mode, 'mode')
        return value

    @mode.setter
    def mode(self, value):
        self._mode = self.set_attr_string(self._mode, 'mode', value)

    @property
    def modes(self):
        """
        Returns a list of the valid modes for the sensor.
        """
        self._modes, value = self.get_attr_set(self._modes, 'modes')
        return value

    @property
    def num_values(self):
        """
        Returns the number of `value<N>` attributes that will return a valid value
        for the current mode.
        """
        self._num_values, value = self.get_attr_int(self._num_values, 'num_values')
        return value

    @property
    def units(self):
        """
        Returns the units of the measured value for the current mode. May return
        empty string
        """
        self._units, value = self.get_attr_string(self._units, 'units')
        return value


# ~autogen

    def value(self, n=0):
        """
        Returns the value or values measured by the sensor. Check num_values to
        see how many values there are. Values with N >= num_values will return
        an error. The values are fixed point numbers, so check decimals to see
        if you need to divide to get the actual value.
        """
#        if isinstance(n, numbers.Integral):
#           n = '{0:d}'.format(n)
#       elif isinstance(n, numbers.Real):
        if isinstance(n, numbers.Real):
#           n = '{0:.0f}'.format(n)
            n = int(n)
        elif isinstance(n, str):
            n = int(n)

        self._value[n], value = self.get_attr_int(self._value[n], 'value'+str(n))
        return value

    @property
    def bin_data_format(self):
        """
        Returns the format of the values in `bin_data` for the current mode.
        Possible values are:

        - `u8`: Unsigned 8-bit integer (byte)
        - `s8`: Signed 8-bit integer (sbyte)
        - `u16`: Unsigned 16-bit integer (ushort)
        - `s16`: Signed 16-bit integer (short)
        - `s16_be`: Signed 16-bit integer, big endian
        - `s32`: Signed 32-bit integer (int)
        - `float`: IEEE 754 32-bit floating point (float)
        """
        self._bin_data_format, value = self.get_attr_string(self._bin_data_format, 'bin_data_format')
        return value

    def bin_data(self, fmt=None):
        """
        Returns the unscaled raw values in the `value<N>` attributes as raw byte
        array. Use `bin_data_format`, `num_values` and the individual sensor
        documentation to determine how to interpret the data.

        Use `fmt` to unpack the raw bytes into a struct.

        Example::

            >>> from ev3dev import *
            >>> ir = InfraredSensor()
            >>> ir.value()
            28
            >>> ir.bin_data('<b')
            (28,)
        """

        if self._bin_data_size == None:
            self._bin_data_size = {
                    "u8":     1,
                    "s8":     1,
                    "u16":    2,
                    "s16":    2,
                    "s16_be": 2,
                    "s32":    4,
                    "float":  4
                }.get(self.bin_data_format, 1) * self.num_values

        if None == self._bin_data:
            self._bin_data = self._attribute_file_open( 'bin_data' )

        self._bin_data.seek(0)
        raw = bytearray(self._bin_data.read(self._bin_data_size))

        if fmt is None: return raw

        return unpack(fmt, raw)

def list_sensors(name_pattern=Sensor.SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
    """
    This is a generator function that enumerates all sensors that match the
    provided arguments.

    Parameters:
	name_pattern: pattern that device name should match.
	    For example, 'sensor*'. Default value: '*'.
	keyword arguments: used for matching the corresponding device
	    attributes. For example, driver_name='lego-ev3-touch', or
	    address=['in1', 'in3']. When argument value is a list,
        then a match against any entry of the list is enough.
    """
    class_path = abspath(Device.DEVICE_ROOT_PATH + '/' + Sensor.SYSTEM_CLASS_NAME)
    return (Sensor(name_pattern=name, name_exact=True)
            for name in list_device_names(class_path, name_pattern, **kwargs))


# ~autogen generic-class classes.i2cSensor>currentClass

class I2cSensor(Sensor):

    """
    A generic interface to control I2C-type EV3 sensors.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = 'sensor*'

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        super(I2cSensor, self).__init__(address, name_pattern, name_exact, driver_name=['nxt-i2c-sensor'], **kwargs)

        self._fw_version = None
        self._poll_ms = None

# ~autogen
# ~autogen generic-get-set classes.i2cSensor>currentClass

    @property
    def fw_version(self):
        """
        Returns the firmware version of the sensor if available. Currently only
        I2C/NXT sensors support this.
        """
        self._fw_version, value = self.get_attr_string(self._fw_version, 'fw_version')
        return value

    @property
    def poll_ms(self):
        """
        Returns the polling period of the sensor in milliseconds. Writing sets the
        polling period. Setting to 0 disables polling. Minimum value is hard
        coded as 50 msec. Returns -EOPNOTSUPP if changing polling is not supported.
        Currently only I2C/NXT sensors support changing the polling period.
        """
        self._poll_ms, value = self.get_attr_int(self._poll_ms, 'poll_ms')
        return value

    @poll_ms.setter
    def poll_ms(self, value):
        self._poll_ms = self.set_attr_int(self._poll_ms, 'poll_ms', value)


# ~autogen
# ~autogen special-sensors

class TouchSensor(Sensor):

    """
    Touch Sensor
    """

    __slots__ = ['auto_mode']

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(TouchSensor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-touch', 'lego-nxt-touch'], **kwargs)
        self.auto_mode = True


    #: Button state
    MODE_TOUCH = 'TOUCH'


    MODES = (
      'TOUCH',
    )


    @property
    def is_pressed(self):
        """
        A boolean indicating whether the current touch sensor is being
        pressed.
        """

        if self.auto_mode:
            self.mode = self.MODE_TOUCH

        return self.value(0)

class ColorSensor(Sensor):

    """
    LEGO EV3 color sensor.
    """

    __slots__ = ['auto_mode']

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(ColorSensor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-color'], **kwargs)
        self.auto_mode = True


    #: Reflected light. Red LED on.
    MODE_COL_REFLECT = 'COL-REFLECT'

    #: Ambient light. Red LEDs off.
    MODE_COL_AMBIENT = 'COL-AMBIENT'

    #: Color. All LEDs rapidly cycling, appears white.
    MODE_COL_COLOR = 'COL-COLOR'

    #: Raw reflected. Red LED on
    MODE_REF_RAW = 'REF-RAW'

    #: Raw Color Components. All LEDs rapidly cycling, appears white.
    MODE_RGB_RAW = 'RGB-RAW'

    #: No color.
    COLOR_NOCOLOR = 0

    #: Black color.
    COLOR_BLACK = 1

    #: Blue color.
    COLOR_BLUE = 2

    #: Green color.
    COLOR_GREEN = 3

    #: Yellow color.
    COLOR_YELLOW = 4

    #: Red color.
    COLOR_RED = 5

    #: White color.
    COLOR_WHITE = 6

    #: Brown color.
    COLOR_BROWN = 7


    MODES = (
      'COL-REFLECT',
      'COL-AMBIENT',
      'COL-COLOR',
      'REF-RAW',
      'RGB-RAW',
    )

    COLORS = (
      'NoColor',
      'Black',
      'Blue',
      'Green',
      'Yellow',
      'Red',
      'White',
      'Brown',
    )


    @property
    def reflected_light_intensity(self):
        """
        Reflected light intensity as a percentage. Light on sensor is red.
        """

        if self.auto_mode:
            self.mode = self.MODE_COL_REFLECT

        return self.value(0)

    @property
    def ambient_light_intensity(self):
        """
        Ambient light intensity. Light on sensor is dimly lit blue.
        """

        if self.auto_mode:
            self.mode = self.MODE_COL_AMBIENT

        return self.value(0)

    @property
    def color(self):
        """
        Color detected by the sensor, categorized by overall value.
          - 0: No color
          - 1: Black
          - 2: Blue
          - 3: Green
          - 4: Yellow
          - 5: Red
          - 6: White
          - 7: Brown
        """

        if self.auto_mode:
            self.mode = self.MODE_COL_COLOR

        return self.value(0)

    @property
    def raw(self):
        """
        Red, green, and blue components of the detected color, in the range 0-1020.
        """

        if self.auto_mode:
            self.mode = self.MODE_RGB_RAW

        return self.value(0), self.value(1), self.value(2)

    @property
    def red(self):
        """
        Red component of the detected color, in the range 0-1020.
        """

        if self.auto_mode:
            self.mode = self.MODE_RGB_RAW

        return self.value(0)

    @property
    def green(self):
        """
        Green component of the detected color, in the range 0-1020.
        """

        if self.auto_mode:
            self.mode = self.MODE_RGB_RAW

        return self.value(1)

    @property
    def blue(self):
        """
        Blue component of the detected color, in the range 0-1020.
        """

        if self.auto_mode:
            self.mode = self.MODE_RGB_RAW

        return self.value(2)

class UltrasonicSensor(Sensor):

    """
    LEGO EV3 ultrasonic sensor.
    """

    __slots__ = ['auto_mode']

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(UltrasonicSensor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-us', 'lego-nxt-us'], **kwargs)
        self.auto_mode = True


    #: Continuous measurement in centimeters.
    MODE_US_DIST_CM = 'US-DIST-CM'

    #: Continuous measurement in inches.
    MODE_US_DIST_IN = 'US-DIST-IN'

    #: Listen.
    MODE_US_LISTEN = 'US-LISTEN'

    #: Single measurement in centimeters.
    MODE_US_SI_CM = 'US-SI-CM'

    #: Single measurement in inches.
    MODE_US_SI_IN = 'US-SI-IN'


    MODES = (
      'US-DIST-CM',
      'US-DIST-IN',
      'US-LISTEN',
      'US-SI-CM',
      'US-SI-IN',
    )


    @property
    def distance_centimeters(self):
        """
        Measurement of the distance detected by the sensor,
        in centimeters.
        """

        if self.auto_mode:
            self.mode = self.MODE_US_DIST_CM

        return self.value(0) * self._scale('US_DIST_CM')

    @property
    def distance_inches(self):
        """
        Measurement of the distance detected by the sensor,
        in inches.
        """

        if self.auto_mode:
            self.mode = self.MODE_US_DIST_IN

        return self.value(0) * self._scale('US_DIST_IN')

    @property
    def other_sensor_present(self):
        """
        Value indicating whether another ultrasonic sensor could
        be heard nearby.
        """

        if self.auto_mode:
            self.mode = self.MODE_US_LISTEN

        return self.value(0)

class GyroSensor(Sensor):

    """
    LEGO EV3 gyro sensor.
    """

    __slots__ = ['auto_mode']

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(GyroSensor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-gyro'], **kwargs)
        self.auto_mode = True


    #: Angle
    MODE_GYRO_ANG = 'GYRO-ANG'

    #: Rotational speed
    MODE_GYRO_RATE = 'GYRO-RATE'

    #: Raw sensor value
    MODE_GYRO_FAS = 'GYRO-FAS'

    #: Angle and rotational speed
    MODE_GYRO_G_A = 'GYRO-G&A'

    #: Calibration ???
    MODE_GYRO_CAL = 'GYRO-CAL'


    MODES = (
      'GYRO-ANG',
      'GYRO-RATE',
      'GYRO-FAS',
      'GYRO-G&A',
      'GYRO-CAL',
    )


    @property
    def angle(self):
        """
        The number of degrees that the sensor has been rotated
        since it was put into this mode.
        """

        if self.auto_mode:
            self.mode = self.MODE_GYRO_ANG

        return self.value(0)

    @property
    def rate(self):
        """
        The rate at which the sensor is rotating, in degrees/second.
        """

        if self.auto_mode:
            self.mode = self.MODE_GYRO_RATE

        return self.value(0)

    @property
    def rate_and_angle(self):
        """
        Angle (degrees) and Rotational Speed (degrees/second).
        """

        if self.auto_mode:
            self.mode = self.MODE_GYRO_G_A

        return self.value(0), self.value(1)

class InfraredSensor(Sensor):

    """
    LEGO EV3 infrared sensor.
    """

    __slots__ = ['auto_mode']

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(InfraredSensor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-ir'], **kwargs)
        self.auto_mode = True


    #: Proximity
    MODE_IR_PROX = 'IR-PROX'

    #: IR Seeker
    MODE_IR_SEEK = 'IR-SEEK'

    #: IR Remote Control
    MODE_IR_REMOTE = 'IR-REMOTE'

    #: IR Remote Control. State of the buttons is coded in binary
    MODE_IR_REM_A = 'IR-REM-A'

    #: Calibration ???
    MODE_IR_CAL = 'IR-CAL'


    MODES = (
      'IR-PROX',
      'IR-SEEK',
      'IR-REMOTE',
      'IR-REM-A',
      'IR-CAL',
    )


    @property
    def proximity(self):
        """
        A measurement of the distance between the sensor and the remote,
        as a percentage. 100% is approximately 70cm/27in.
        """

        if self.auto_mode:
            self.mode = self.MODE_IR_PROX

        return self.value(0)

class SoundSensor(Sensor):

    """
    LEGO NXT Sound Sensor
    """

    __slots__ = ['auto_mode']

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(SoundSensor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-nxt-sound'], **kwargs)
        self.auto_mode = True


    #: Sound pressure level. Flat weighting
    MODE_DB = 'DB'

    #: Sound pressure level. A weighting
    MODE_DBA = 'DBA'


    MODES = (
      'DB',
      'DBA',
    )


    @property
    def sound_pressure(self):
        """
        A measurement of the measured sound pressure level, as a
        percent. Uses a flat weighting.
        """

        if self.auto_mode:
            self.mode = self.MODE_DB

        return self.value(0) * self._scale('DB')

    @property
    def sound_pressure_low(self):
        """
        A measurement of the measured sound pressure level, as a
        percent. Uses A-weighting, which focuses on levels up to 55 dB.
        """

        if self.auto_mode:
            self.mode = self.MODE_DBA

        return self.value(0) * self._scale('DBA')

class LightSensor(Sensor):

    """
    LEGO NXT Light Sensor
    """

    __slots__ = ['auto_mode']

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(LightSensor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-nxt-light'], **kwargs)
        self.auto_mode = True


    #: Reflected light. LED on
    MODE_REFLECT = 'REFLECT'

    #: Ambient light. LED off
    MODE_AMBIENT = 'AMBIENT'


    MODES = (
      'REFLECT',
      'AMBIENT',
    )


    @property
    def reflected_light_intensity(self):
        """
        A measurement of the reflected light intensity, as a percentage.
        """

        if self.auto_mode:
            self.mode = self.MODE_REFLECT

        return self.value(0) * self._scale('REFLECT')

    @property
    def ambient_light_intensity(self):
        """
        A measurement of the ambient light intensity, as a percentage.
        """

        if self.auto_mode:
            self.mode = self.MODE_AMBIENT

        return self.value(0) * self._scale('AMBIENT')


# ~autogen

# ~autogen generic-class classes.led>currentClass

class Led(Device):

    """
    Any device controlled by the generic LED driver.
    See https://www.kernel.org/doc/Documentation/leds/leds-class.txt
    for more details.
    """

    SYSTEM_CLASS_NAME = 'leds'
    SYSTEM_DEVICE_NAME_CONVENTION = '*'

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        if address is not None:
            kwargs['address'] = address
        super(Led, self).__init__(self.SYSTEM_CLASS_NAME, name_pattern, name_exact, **kwargs)

        self._max_brightness = None
        self._brightness = None
        self._triggers = None
        self._trigger = None
        self._delay_on = None
        self._delay_off = None

# ~autogen

    __slots__ = [
# ~autogen generic-class-slots classes.led>currentClass

    '_max_brightness',
    '_brightness',
    '_triggers',
    '_trigger',
    '_delay_on',
    '_delay_off',

# ~autogen
    ]

# ~autogen generic-get-set classes.led>currentClass

    @property
    def max_brightness(self):
        """
        Returns the maximum allowable brightness value.
        """
        self._max_brightness, value = self.get_attr_int(self._max_brightness, 'max_brightness')
        return value

    @property
    def brightness(self):
        """
        Sets the brightness level. Possible values are from 0 to `max_brightness`.
        """
        self._brightness, value = self.get_attr_int(self._brightness, 'brightness')
        return value

    @brightness.setter
    def brightness(self, value):
        self._brightness = self.set_attr_int(self._brightness, 'brightness', value)

    @property
    def triggers(self):
        """
        Returns a list of available triggers.
        """
        self._triggers, value = self.get_attr_set(self._triggers, 'trigger')
        return value



# ~autogen

    @property
    def trigger(self):
        """
        Sets the led trigger. A trigger
        is a kernel based source of led events. Triggers can either be simple or
        complex. A simple trigger isn't configurable and is designed to slot into
        existing subsystems with minimal additional code. Examples are the `ide-disk` and
        `nand-disk` triggers.

        Complex triggers whilst available to all LEDs have LED specific
        parameters and work on a per LED basis. The `timer` trigger is an example.
        The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `on` and `off` time can
        be specified via `delay_{on,off}` attributes in milliseconds.
        You can change the brightness value of a LED independently of the timer
        trigger. However, if you set the brightness value to 0 it will
        also disable the `timer` trigger.
        """
        self._trigger, value = self.get_attr_from_set(self._trigger, 'trigger')
        return value

    @trigger.setter
    def trigger(self, value):
        self._trigger = self.set_attr_string(self._trigger, 'trigger', value)

        # Workaround for ev3dev/ev3dev#225.
        # When trigger is set to 'timer', we need to wait for 'delay_on' and
        # 'delay_off' attributes to appear with correct permissions.
        if value == 'timer':
            for attr in ('delay_on', 'delay_off'):
                path = self._path + '/' + attr

                # Make sure the file has been created:
                for _ in range(5):
                    if os.path.exists(path):
                        break
                    time.sleep(0.2)
                else:
                    raise Exception('"{}" attribute has not been created'.format(attr))

                # Make sure the file has correct permissions:
                for _ in range(5):
                    mode = stat.S_IMODE(os.stat(path)[stat.ST_MODE])
                    if mode & stat.S_IRGRP and mode & stat.S_IWGRP:
                        break
                    time.sleep(0.2)
                else:
                    raise Exception('"{}" attribute has wrong permissions'.format(attr))


    @property
    def delay_on(self):
        """
        The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `on` time can
        be specified via `delay_on` attribute in milliseconds.
        """

        # Workaround for ev3dev/ev3dev#225.
        # 'delay_on' and 'delay_off' attributes are created when trigger is set
        # to 'timer', and destroyed when it is set to anything else.
        # This means the file cache may become outdated, and we may have to
        # reopen the file.
        for retry in (True, False):
            try:
                self._delay_on, value = self.get_attr_int(self._delay_on, 'delay_on')
                return value
            except OSError:
                if retry:
                    self._delay_on = None
                else:
                    raise

    @delay_on.setter
    def delay_on(self, value):
        # Workaround for ev3dev/ev3dev#225.
        # 'delay_on' and 'delay_off' attributes are created when trigger is set
        # to 'timer', and destroyed when it is set to anything else.
        # This means the file cache may become outdated, and we may have to
        # reopen the file.
        for retry in (True, False):
            try:
                self._delay_on = self.set_attr_int(self._delay_on, 'delay_on', value)
                return
            except OSError:
                if retry:
                    self._delay_on = None
                else:
                    raise

    @property
    def delay_off(self):
        """
        The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `off` time can
        be specified via `delay_off` attribute in milliseconds.
        """

        # Workaround for ev3dev/ev3dev#225.
        # 'delay_on' and 'delay_off' attributes are created when trigger is set
        # to 'timer', and destroyed when it is set to anything else.
        # This means the file cache may become outdated, and we may have to
        # reopen the file.
        for retry in (True, False):
            try:
                self._delay_off, value = self.get_attr_int(self._delay_off, 'delay_off')
                return value
            except OSError:
                if retry:
                    self._delay_off = None
                else:
                    raise

    @delay_off.setter
    def delay_off(self, value):
        # Workaround for ev3dev/ev3dev#225.
        # 'delay_on' and 'delay_off' attributes are created when trigger is set
        # to 'timer', and destroyed when it is set to anything else.
        # This means the file cache may become outdated, and we may have to
        # reopen the file.
        for retry in (True, False):
            try:
                self._delay_off = self.set_attr_int(self._delay_off, 'delay_off', value)
                return
            except OSError:
                if retry:
                    self._delay_off = None
                else:
                    raise


    @property
    def brightness_pct(self):
        """
        Returns led brightness as a fraction of max_brightness
        """
        return float(self.brightness) / self.max_brightness

    @brightness_pct.setter
    def brightness_pct(self, value):
        self.brightness = value * self.max_brightness


class ButtonBase(object):
    """
    Abstract button interface.
    """

    def __str__(self):
        return self.__class__.__name__

    @staticmethod
    def on_change(changed_buttons):
        """
        This handler is called by `process()` whenever state of any button has
        changed since last `process()` call. `changed_buttons` is a list of
        tuples of changed button names and their states.
        """
        pass

    _state = set([])

    def any(self):
        """
        Checks if any button is pressed.
        """
        return bool(self.buttons_pressed)

    def check_buttons(self, buttons=[]):
        """
        Check if currently pressed buttons exactly match the given list.
        """
        return set(self.buttons_pressed) == set(buttons)

    def process(self):
        """
        Check for currenly pressed buttons. If the new state differs from the
        old state, call the appropriate button event handlers.
        """
        new_state = set(self.buttons_pressed)
        old_state = self._state
        self._state = new_state

        state_diff = new_state.symmetric_difference(old_state)
        for button in state_diff:
            handler = getattr(self, 'on_' + button)
            if handler is not None: handler(button in new_state)

        if self.on_change is not None and state_diff:
            self.on_change([(button, button in new_state) for button in state_diff])

    @property
    def buttons_pressed(self):
        raise NotImplementedError()


class ButtonEVIO(ButtonBase):

    """
    Provides a generic button reading mechanism that works with event interface
    and may be adapted to platform specific implementations.

    This implementation depends on the availability of the EVIOCGKEY ioctl
    to be able to read the button state buffer. See Linux kernel source
    in /include/uapi/linux/input.h for details.
    """

    KEY_MAX = 0x2FF
    KEY_BUF_LEN = int((KEY_MAX + 7) / 8)
    EVIOCGKEY = (2 << (14 + 8 + 8) | KEY_BUF_LEN << (8 + 8) | ord('E') << 8 | 0x18)

    _buttons = {}

    def __init__(self):
        self._file_cache = {}
        self._buffer_cache = {}
        for b in self._buttons:
            name = self._buttons[b]['name']
            if name not in self._file_cache:
                self._file_cache[name] = open(name, 'rb', 0)
                self._buffer_cache[name] = array.array('B', [0] * self.KEY_BUF_LEN)

    def _button_file(self, name):
        return self._file_cache[name]

    def _button_buffer(self, name):
        return self._buffer_cache[name]

    @property
    def buttons_pressed(self):
        """
        Returns list of names of pressed buttons.
        """
        for b in self._buffer_cache:
            fcntl.ioctl(self._button_file(b), self.EVIOCGKEY, self._buffer_cache[b])

        pressed = []
        for k, v in self._buttons.items():
            buf = self._buffer_cache[v['name']]
            bit = v['value']
            if bool(buf[int(bit / 8)] & 1 << bit % 8):
                pressed += [k]
        return pressed


# ~autogen remote-control specialSensorTypes.infraredSensor.remoteControl>currentClass
class RemoteControl(ButtonBase):
    """
    EV3 Remote Controller
    """

    _BUTTON_VALUES = {
            0: [],
            1: ['red_up'],
            2: ['red_down'],
            3: ['blue_up'],
            4: ['blue_down'],
            5: ['red_up', 'blue_up'],
            6: ['red_up', 'blue_down'],
            7: ['red_down', 'blue_up'],
            8: ['red_down', 'blue_down'],
            9: ['beacon'],
            10: ['red_up', 'red_down'],
            11: ['blue_up', 'blue_down']
            }

    #: Handles ``Red Up`` events.
    on_red_up = None

    #: Handles ``Red Down`` events.
    on_red_down = None

    #: Handles ``Blue Up`` events.
    on_blue_up = None

    #: Handles ``Blue Down`` events.
    on_blue_down = None

    #: Handles ``Beacon`` events.
    on_beacon = None


    @property
    def red_up(self):
        """
        Checks if `red_up` button is pressed.
        """
        return 'red_up' in self.buttons_pressed

    @property
    def red_down(self):
        """
        Checks if `red_down` button is pressed.
        """
        return 'red_down' in self.buttons_pressed

    @property
    def blue_up(self):
        """
        Checks if `blue_up` button is pressed.
        """
        return 'blue_up' in self.buttons_pressed

    @property
    def blue_down(self):
        """
        Checks if `blue_down` button is pressed.
        """
        return 'blue_down' in self.buttons_pressed

    @property
    def beacon(self):
        """
        Checks if `beacon` button is pressed.
        """
        return 'beacon' in self.buttons_pressed


# ~autogen

    def __init__(self, sensor=None, channel=1):
        if sensor is None:
            self._sensor = InfraredSensor()
        else:
            self._sensor = sensor

        self._channel = max(1, min(4, channel)) - 1
        self._state = set([])

        if self._sensor.connected:
            self._sensor.mode = 'IR-REMOTE'

    @property
    def connected(self):
        return self._sensor.connected

    @property
    def buttons_pressed(self):
        """
        Returns list of currently pressed buttons.
        """
        return RemoteControl._BUTTON_VALUES.get(self._sensor.value(self._channel), [])


class BeaconSeeker(object):
    """
    Seeks EV3 Remote Controller in beacon mode.
    """

    def __init__(self, sensor=None, channel=1):
        self._sensor  = InfraredSensor() if sensor is None else sensor
        self._channel = max(1, min(4, channel)) - 1

        if self._sensor.connected:
            self._sensor.mode = 'IR-SEEK'

    @property
    def heading(self):
        """
        Returns heading (-25, 25) to the beacon on the given channel.
        """
        return self._sensor.value(self._channel * 2)

    @property
    def distance(self):
        """
        Returns distance (0, 100) to the beacon on the given channel.
        Returns -128 when beacon is not found.
        """
        return self._sensor.value(self._channel * 2 + 1)

    @property
    def heading_and_distance(self):
        """
        Returns heading and distance to the beacon on the given channel as a
        tuple.
        """
        return self._sensor.value(self._channel * 2), self._sensor.value(self._channel * 2 + 1)


# ~autogen generic-class classes.powerSupply>currentClass

class PowerSupply(Device):

    """
    A generic interface to read data from the system's power_supply class.
    Uses the built-in legoev3-battery if none is specified.
    """

    SYSTEM_CLASS_NAME = 'power_supply'
    SYSTEM_DEVICE_NAME_CONVENTION = '*'

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        if address is not None:
            kwargs['address'] = address
        super(PowerSupply, self).__init__(self.SYSTEM_CLASS_NAME, name_pattern, name_exact, **kwargs)

        self._measured_current = None
        self._measured_voltage = None
        self._max_voltage = None
        self._min_voltage = None
        self._technology = None
        self._type = None

# ~autogen

    __slots__ = [
# ~autogen generic-class-slots classes.powerSupply>currentClass

    '_measured_current',
    '_measured_voltage',
    '_max_voltage',
    '_min_voltage',
    '_technology',
    '_type',

# ~autogen
    ]

# ~autogen generic-get-set classes.powerSupply>currentClass

    @property
    def measured_current(self):
        """
        The measured current that the battery is supplying (in microamps)
        """
        self._measured_current, value = self.get_attr_int(self._measured_current, 'current_now')
        return value

    @property
    def measured_voltage(self):
        """
        The measured voltage that the battery is supplying (in microvolts)
        """
        self._measured_voltage, value = self.get_attr_int(self._measured_voltage, 'voltage_now')
        return value

    @property
    def max_voltage(self):
        """
        """
        self._max_voltage, value = self.get_attr_int(self._max_voltage, 'voltage_max_design')
        return value

    @property
    def min_voltage(self):
        """
        """
        self._min_voltage, value = self.get_attr_int(self._min_voltage, 'voltage_min_design')
        return value

    @property
    def technology(self):
        """
        """
        self._technology, value = self.get_attr_string(self._technology, 'technology')
        return value

    @property
    def type(self):
        """
        """
        self._type, value = self.get_attr_string(self._type, 'type')
        return value


# ~autogen

    @property
    def measured_amps(self):
        """
        The measured current that the battery is supplying (in amps)
        """
        return self.measured_current / 1e6

    @property
    def measured_volts(self):
        """
        The measured voltage that the battery is supplying (in volts)
        """
        return self.measured_voltage / 1e6


# ~autogen generic-class classes.legoPort>currentClass

class LegoPort(Device):

    """
    The `lego-port` class provides an interface for working with input and
    output ports that are compatible with LEGO MINDSTORMS RCX/NXT/EV3, LEGO
    WeDo and LEGO Power Functions sensors and motors. Supported devices include
    the LEGO MINDSTORMS EV3 Intelligent Brick, the LEGO WeDo USB hub and
    various sensor multiplexers from 3rd party manufacturers.

    Some types of ports may have multiple modes of operation. For example, the
    input ports on the EV3 brick can communicate with sensors using UART, I2C
    or analog validate signals - but not all at the same time. Therefore there
    are multiple modes available to connect to the different types of sensors.

    In most cases, ports are able to automatically detect what type of sensor
    or motor is connected. In some cases though, this must be manually specified
    using the `mode` and `set_device` attributes. The `mode` attribute affects
    how the port communicates with the connected device. For example the input
    ports on the EV3 brick can communicate using UART, I2C or analog voltages,
    but not all at the same time, so the mode must be set to the one that is
    appropriate for the connected sensor. The `set_device` attribute is used to
    specify the exact type of sensor that is connected. Note: the mode must be
    correctly set before setting the sensor type.

    Ports can be found at `/sys/class/lego-port/port<N>` where `<N>` is
    incremented each time a new port is registered. Note: The number is not
    related to the actual port at all - use the `address` attribute to find
    a specific port.
    """

    SYSTEM_CLASS_NAME = 'lego-port'
    SYSTEM_DEVICE_NAME_CONVENTION = '*'

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        if address is not None:
            kwargs['address'] = address
        super(LegoPort, self).__init__(self.SYSTEM_CLASS_NAME, name_pattern, name_exact, **kwargs)

        self._address = None
        self._driver_name = None
        self._modes = None
        self._mode = None
        self._set_device = None
        self._status = None

# ~autogen

    __slots__ = [
# ~autogen generic-class-slots classes.legoPort>currentClass

    '_address',
    '_driver_name',
    '_modes',
    '_mode',
    '_set_device',
    '_status',

# ~autogen
    ]

# ~autogen generic-get-set classes.legoPort>currentClass

    @property
    def address(self):
        """
        Returns the name of the port. See individual driver documentation for
        the name that will be returned.
        """
        self._address, value = self.get_attr_string(self._address, 'address')
        return value

    @property
    def driver_name(self):
        """
        Returns the name of the driver that loaded this device. You can find the
        complete list of drivers in the [list of port drivers].
        """
        self._driver_name, value = self.get_attr_string(self._driver_name, 'driver_name')
        return value

    @property
    def modes(self):
        """
        Returns a list of the available modes of the port.
        """
        self._modes, value = self.get_attr_set(self._modes, 'modes')
        return value

    @property
    def mode(self):
        """
        Reading returns the currently selected mode. Writing sets the mode.
        Generally speaking when the mode changes any sensor or motor devices
        associated with the port will be removed new ones loaded, however this
        this will depend on the individual driver implementing this class.
        """
        self._mode, value = self.get_attr_string(self._mode, 'mode')
        return value

    @mode.setter
    def mode(self, value):
        self._mode = self.set_attr_string(self._mode, 'mode', value)

    @property
    def set_device(self):
        """
        For modes that support it, writing the name of a driver will cause a new
        device to be registered for that driver and attached to this port. For
        example, since NXT/Analog sensors cannot be auto-detected, you must use
        this attribute to load the correct driver. Returns -EOPNOTSUPP if setting a
        device is not supported.
        """
        raise Exception("set_device is a write-only property!")

    @set_device.setter
    def set_device(self, value):
        self._set_device = self.set_attr_string(self._set_device, 'set_device', value)

    @property
    def status(self):
        """
        In most cases, reading status will return the same value as `mode`. In
        cases where there is an `auto` mode additional values may be returned,
        such as `no-device` or `error`. See individual port driver documentation
        for the full list of possible values.
        """
        self._status, value = self.get_attr_string(self._status, 'status')
        return value


# ~autogen