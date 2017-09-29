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

import os
import io
import fnmatch
import numbers
import array
import mmap
import ctypes
import re
import select
import shlex
import stat
import time
import errno
from os.path import abspath
from struct import pack, unpack
from subprocess import Popen, check_output, PIPE

try:
    # This is a linux-specific module.
    # It is required by the Button() class, but failure to import it may be
    # safely ignored if one just needs to run API tests on Windows.
    import fcntl
except ImportError:
    print("WARNING: Failed to import fcntl. Button class will be unuseable!")

INPUT_AUTO = ''
OUTPUT_AUTO = ''

# The number of milliseconds we wait for the state of a motor to
# update to 'running' in the "on_for_XYZ" methods of the Motor class
WAIT_RUNNING_TIMEOUT = 100


def get_current_platform():
    """
    Look in /sys/class/board-info/ to determine the platform type.

    This can return 'ev3', 'evb', 'pistorms', 'brickpi' or 'brickpi3'.
    """
    board_info_dir = '/sys/class/board-info/'

    for board in os.listdir(board_info_dir):
        uevent_filename = os.path.join(board_info_dir, board, 'uevent')

        if os.path.exists(uevent_filename):
            with open(uevent_filename, 'r') as fh:
                for line in fh.readlines():
                    (key, value) = line.strip().split('=')

                    if key == 'BOARD_INFO_MODEL':

                        if value == 'LEGO MINDSTORMS EV3':
                            return 'ev3'

                        elif value in ('FatcatLab EVB', 'QuestCape'):
                            return 'evb'

                        elif value == 'PiStorms':
                            return 'pistorms'

                        # This is the same for both BrickPi and BrickPi+.
                        # There is not a way to tell the difference.
                        elif value == 'Dexter Industries BrickPi':
                            return 'brickpi'

                        elif value == 'Dexter Industries BrickPi3':
                            return 'brickpi3'
    return None


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
            if attribute is None:
                attribute = self._attribute_file_open( name )
            else:
                attribute.seek(0)
            return attribute, attribute.read().strip().decode()
        else:
            #log.info("%s: path %s, attribute %s" % (self, self._path, name))
            raise Exception("%s is not connected" % self)

    def _set_attribute(self, attribute, name, value, raw=False):
        """Device attribute setter"""
        if self.connected:
            try:
                if attribute is None:
                    attribute = self._attribute_file_open( name )
                else:
                    attribute.seek(0)

                if raw:
                    attribute.write(value)
                else:
                    attribute.write(value.encode())

                attribute.flush()
            except Exception as ex:
                self._raise_friendly_access_error(ex, name)
            return attribute
        else:
            #log.info("%s: path %s, attribute %s" % (self, self._path, name))
            raise Exception("%s is not connected" % self)

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
        elif driver_error.errno == errno.ENODEV or driver_error.errno == errno.ENOENT:
            # We will assume that a file-not-found error is the result of a disconnected device
            # rather than a library error. If that isn't the case, at a minimum the underlying
            # error info will be printed for debugging.
            raise Exception("%s is no longer connected" % self) from driver_error
        raise driver_error

    def get_attr_int(self, attribute, name):
        attribute, value = self._get_attribute(attribute, name)
        return attribute, int(value)

    def set_attr_int(self, attribute, name, value):
        return self._set_attribute(attribute, name, str(int(value)))

    def set_attr_raw(self, attribute, name, value):
        return self._set_attribute(attribute, name, value, True)

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
        self._poll = None

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
    ]

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

    def _set_position_rotations(self, speed_pct, rotations):
        if speed_pct > 0:
            self.position_sp = self.position + int(rotations * self.count_per_rot)
        else:
            self.position_sp = self.position - int(rotations * self.count_per_rot)

    def _set_position_degrees(self, speed_pct, degrees):
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
        Rotate the motor at 'speed' for 'rotations'
        """
        assert speed_pct >= -100 and speed_pct <= 100,\
            "%s is an invalid speed_pct, must be between -100 and 100 (inclusive)" % speed_pct
        self.speed_sp = int((speed_pct * self.max_speed) / 100)
        self._set_position_rotations(speed_pct, rotations)
        self._set_brake(brake)
        self.run_to_abs_pos()

        if block:
            self.wait_until('running', timeout=WAIT_RUNNING_TIMEOUT)
            self.wait_until_not_moving()

    def on_for_degrees(self, speed_pct, degrees, brake=True, block=True):
        """
        Rotate the motor at 'speed' for 'degrees'
        """
        assert speed_pct >= -100 and speed_pct <= 100,\
            "%s is an invalid speed_pct, must be between -100 and 100 (inclusive)" % speed_pct
        self.speed_sp = int((speed_pct * self.max_speed) / 100)
        self._set_position_degrees(speed_pct, degrees)
        self._set_brake(brake)
        self.run_to_abs_pos()

        if block:
            self.wait_until('running', timeout=WAIT_RUNNING_TIMEOUT)
            self.wait_until_not_moving()

    def on_for_seconds(self, speed_pct, seconds, brake=True, block=True):
        """
        Rotate the motor at 'speed' for 'seconds'
        """
        assert speed_pct >= -100 and speed_pct <= 100,\
            "%s is an invalid speed_pct, must be between -100 and 100 (inclusive)" % speed_pct
        self.speed_sp = int((speed_pct * self.max_speed) / 100)
        self.time_sp = int(seconds * 1000)
        self._set_brake(brake)
        self.run_timed()

        if block:
            self.wait_until('running', timeout=WAIT_RUNNING_TIMEOUT)
            self.wait_until_not_moving()

    def on(self, speed_pct):
        """
        Rotate the motor at 'speed' for forever
        """
        assert speed_pct >= -100 and speed_pct <= 100,\
            "%s is an invalid speed_pct, must be between -100 and 100 (inclusive)" % speed_pct
        self.speed_sp = int((speed_pct * self.max_speed) / 100)
        self.run_forever()

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
        self.verify_connected()

    def __str__(self):

        if self.desc:
            return self.desc
        else:
            return self.__class__.__name__

    def verify_connected(self):
        for motor in self.motors.values():
            if not motor.connected:
                print("%s: %s is not connected" % (self, motor))
                sys.exit(1)

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
            right_rotations = float(right_speed / left_speed) * rotations
        else:
            left_rotations = float(left_speed / right_speed) * rotations
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
    __slots__ = [
    '_address',
    '_command',
    '_commands',
    '_decimals',
    '_driver_name',
    '_mode',
    '_modes',
    '_num_values',
    '_units',
    '_value',
    '_bin_data_format',
    '_bin_data_size',
    '_bin_data',
    '_mode_scale'
    ]

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
        self._value = [None,None,None,None,None,None,None,None]

        self._bin_data_format = None
        self._bin_data_size = None
        self._bin_data = None
        self._mode_scale = {}

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

    def value(self, n=0):
        """
        Returns the value or values measured by the sensor. Check num_values to
        see how many values there are. Values with N >= num_values will return
        an error. The values are fixed point numbers, so check decimals to see
        if you need to divide to get the actual value.
        """
        if isinstance(n, numbers.Real):
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


class TouchSensor(Sensor):

    """
    Touch Sensor
    """

    __slots__ = ['_poll', '_value0']

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    #: Button state
    MODE_TOUCH = 'TOUCH'
    MODES = (MODE_TOUCH,)

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(TouchSensor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-touch', 'lego-nxt-touch'], **kwargs)
        self._poll = None
        self._value0 = None

    @property
    def is_pressed(self):
        """
        A boolean indicating whether the current touch sensor is being
        pressed.
        """
        self.mode = self.MODE_TOUCH
        return self.value(0)

    @property
    def is_released(self):
        return not self.is_pressed

    def _wait(self, wait_for_press, timeout_ms):
        tic = time.time()

        if self._poll is None:
            self._value0 = self._attribute_file_open('value0')
            self._poll = select.poll()
            self._poll.register(self._value0, select.POLLPRI)

        while True:
            self._poll.poll(timeout_ms)

            if self.is_pressed == wait_for_press:
                return True

            if timeout_ms is not None and time.time() >= tic + timeout_ms / 1000:
                return False

    def wait_for_pressed(self, timeout_ms=None):
        return self._wait(True, timeout_ms)

    def wait_for_released(self, timeout_ms=None):
        return self._wait(False, timeout_ms)

    def wait_for_bump(self, timeout_ms=None):
        """
        Wait for the touch sensor to be pressed down and then released.
        Both actions must happen within timeout_ms.
        """
        start_time = time.time()

        if self.wait_for_pressed(timeout_ms):
            if timeout_ms is not None:
                timeout_ms -= int((time.time() - start_time) * 1000)
            return self.wait_for_released(timeout_ms)

        return False


class ColorSensor(Sensor):

    """
    LEGO EV3 color sensor.
    """

    __slots__ = ['red_max', 'green_max', 'blue_max']

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

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
      MODE_COL_REFLECT,
      MODE_COL_AMBIENT,
      MODE_COL_COLOR,
      MODE_REF_RAW,
      MODE_RGB_RAW
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

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(ColorSensor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-color'], **kwargs)

        # See calibrate_white() for more details
        self.red_max = 300
        self.green_max = 300
        self.blue_max = 300

    @property
    def reflected_light_intensity(self):
        """
        Reflected light intensity as a percentage. Light on sensor is red.
        """
        self.mode = self.MODE_COL_REFLECT
        return self.value(0)

    @property
    def ambient_light_intensity(self):
        """
        Ambient light intensity. Light on sensor is dimly lit blue.
        """
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
        self.mode = self.MODE_COL_COLOR
        return self.value(0)

    @property
    def color_name(self):
        """
        Returns NoColor, Black, Blue, etc
        """
        return self.COLORS[self.color]

    @property
    def raw(self):
        """
        Red, green, and blue components of the detected color, officially in the
        range 0-1020 but the values returned will never be that high. We do not
        yet know why the values returned are low, but pointing the color sensor
        at a well lit sheet of white paper will return values in the 250-400 range.

        If this is an issue, check out the rgb() and calibrate_white() methods.
        """
        self.mode = self.MODE_RGB_RAW
        return self.value(0), self.value(1), self.value(2)

    def calibrate_white(self):
        """
        The RGB raw values are on a scale of 0-1020 but you never see a value
        anywhere close to 1020.  This function is designed to be called when
        the sensor is placed over a white object in order to figure out what
        are the maximum RGB values the robot can expect to see.  We will use
        these maximum values to scale future raw values to a 0-255 range in
        rgb().

        If you never call this function red_max, green_max, and blue_max will
        use a default value of 300.  This default was selected by measuring
        the RGB values of a white sheet of paper in a well lit room.

        Note that there are several variables that influence the maximum RGB
        values detected by the color sensor
        - the distance of the color sensor to the white object
        - the amount of light in the room
        - shadows that the robot casts on the sensor
        """
        (self.red_max, self.green_max, self.blue_max) = self.raw

    @property
    def rgb(self):
        """
        Same as raw() but RGB values are scaled to 0-255
        """
        (red, green, blue) = self.raw

        return (min(int((red * 255) / self.red_max), 255),
                min(int((green * 255) / self.green_max), 255),
                min(int((blue * 255) / self.blue_max), 255))

    @property
    def red(self):
        """
        Red component of the detected color, in the range 0-1020.
        """
        self.mode = self.MODE_RGB_RAW
        return self.value(0)

    @property
    def green(self):
        """
        Green component of the detected color, in the range 0-1020.
        """
        self.mode = self.MODE_RGB_RAW
        return self.value(1)

    @property
    def blue(self):
        """
        Blue component of the detected color, in the range 0-1020.
        """
        self.mode = self.MODE_RGB_RAW
        return self.value(2)


class UltrasonicSensor(Sensor):

    """
    LEGO EV3 ultrasonic sensor.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(UltrasonicSensor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-us', 'lego-nxt-us'], **kwargs)

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
        self.mode = self.MODE_US_DIST_CM
        return self.value(0) * self._scale('US_DIST_CM')

    @property
    def distance_inches(self):
        """
        Measurement of the distance detected by the sensor,
        in inches.
        """
        self.mode = self.MODE_US_DIST_IN
        return self.value(0) * self._scale('US_DIST_IN')

    @property
    def other_sensor_present(self):
        """
        Value indicating whether another ultrasonic sensor could
        be heard nearby.
        """
        self.mode = self.MODE_US_LISTEN
        return self.value(0)


class GyroSensor(Sensor):

    """
    LEGO EV3 gyro sensor.
    """
    __slots__ = ['_direct',]

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

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

    # Newer versions of the Gyro sensor also have an additional second axis
    # accessible via the TILT-ANGLE and TILT-RATE modes that is not usable
    # using the official EV3-G blocks
    MODE_TILT_ANG = 'TILT-ANGLE'
    MODE_TILT_RATE = 'TILT-RATE'

    MODES = (
        MODE_GYRO_ANG,
        MODE_GYRO_RATE,
        MODE_GYRO_FAS,
        MODE_GYRO_G_A,
        MODE_GYRO_CAL,
        MODE_TILT_ANG,
        MODE_TILT_RATE,
    )

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(GyroSensor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-gyro'], **kwargs)
        self._direct = None

    @property
    def angle(self):
        """
        The number of degrees that the sensor has been rotated
        since it was put into this mode.
        """
        self.mode = self.MODE_GYRO_ANG
        return self.value(0)

    @property
    def rate(self):
        """
        The rate at which the sensor is rotating, in degrees/second.
        """
        self.mode = self.MODE_GYRO_RATE
        return self.value(0)

    @property
    def rate_and_angle(self):
        """
        Angle (degrees) and Rotational Speed (degrees/second).
        """
        self.mode = self.MODE_GYRO_G_A
        return self.value(0), self.value(1)

    @property
    def tilt_angle(self):
        self.mode = self.MODE_TILT_ANG
        return self.value(0)

    @property
    def tilt_rate(self):
        self.mode = self.MODE_TILT_RATE
        return self.value(0)

    @property
    def direct(self):
        raise Exception("direct is a write-only property!")

    @direct.setter
    def direct(self, value):
        raw_value = pack('B', value)
        self._direct = self.set_attr_raw(self._direct, 'direct', raw_value)

    def reset(self):
        self.mode = self.MODE_GYRO_ANG
        self.direct = 17


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

    def process(self, new_state=None):
        """
        Check for currenly pressed buttons. If the new state differs from the
        old state, call the appropriate button event handlers.
        """
        if new_state is None:
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


class InfraredSensor(Sensor, ButtonBase):
    """
    LEGO EV3 infrared sensor.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

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
      MODE_IR_PROX,
      MODE_IR_SEEK,
      MODE_IR_REMOTE,
      MODE_IR_REM_A,
      MODE_IR_CAL
    )

    # The following are all of the various combinations of button presses for
    # the remote control.  The key/index is the number that will be written in
    # the attribute file to indicate what combination of buttons are currently
    # pressed.
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

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(InfraredSensor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-ir'], **kwargs)

    def _normalize_channel(self, channel):
        assert channel >= 1 and channel <= 4, "channel is %s, it must be 1, 2, 3, or 4" % channel
        channel = max(1, min(4, channel)) - 1
        return channel

    @property
    def proximity(self):
        """
        A measurement of the distance between the sensor and the remote,
        as a percentage. 100% is approximately 70cm/27in.
        """
        self.mode = self.MODE_IR_PROX
        return self.value(0)

    def heading(self, channel=1):
        """
        Returns heading (-25, 25) to the beacon on the given channel.
        """
        self.mode = self.MODE_IR_SEEK
        channel = self._normalize_channel(channel)
        return self.value(channel * 2)

    def distance(self, channel=1):
        """
        Returns distance (0, 100) to the beacon on the given channel.
        Returns None when beacon is not found.
        """
        self.mode = self.MODE_IR_SEEK
        channel = self._normalize_channel(channel)
        ret_value = self.value((channel * 2) + 1)

        # The value will be -128 if no beacon is found, return None instead
        return None if ret_value == -128 else ret_value

    def heading_and_distance(self, channel=1):
        """
        Returns heading and distance to the beacon on the given channel as a
        tuple.
        """
        return (self.heading(channel), self.distance(channel))

    def red_up(self, channel=1):
        """
        Checks if `red_up` button is pressed.
        """
        return 'red_up' in self.buttons_pressed(channel)

    def red_down(self, channel=1):
        """
        Checks if `red_down` button is pressed.
        """
        return 'red_down' in self.buttons_pressed(channel)

    def blue_up(self, channel=1):
        """
        Checks if `blue_up` button is pressed.
        """
        return 'blue_up' in self.buttons_pressed(channel)

    def blue_down(self, channel=1):
        """
        Checks if `blue_down` button is pressed.
        """
        return 'blue_down' in self.buttons_pressed(channel)

    def beacon(self, channel=1):
        """
        Checks if `beacon` button is pressed.
        """
        return 'beacon' in self.buttons_pressed(channel)

    def buttons_pressed(self, channel=1):
        """
        Returns list of currently pressed buttons.
        """
        self.mode = self.MODE_IR_REMOTE
        channel = self._normalize_channel(channel)
        return self._BUTTON_VALUES.get(self.value(channel), [])

    def process(self, channel=1):
        """
        ButtonBase expects buttons_pressed to be a @property but we need to
        pass 'channel' to our buttons_pressed. Get the new_state and pass
        that to ButtonBase.process().
        """
        new_state = set(self.buttons_pressed(channel))
        ButtonBase.process(self, new_state)


class SoundSensor(Sensor):

    """
    LEGO NXT Sound Sensor
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(SoundSensor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-nxt-sound'], **kwargs)

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
        self.mode = self.MODE_DB
        return self.value(0) * self._scale('DB')

    @property
    def sound_pressure_low(self):
        """
        A measurement of the measured sound pressure level, as a
        percent. Uses A-weighting, which focuses on levels up to 55 dB.
        """
        self.mode = self.MODE_DBA
        return self.value(0) * self._scale('DBA')


class LightSensor(Sensor):

    """
    LEGO NXT Light Sensor
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(LightSensor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-nxt-light'], **kwargs)

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
        self.mode = self.MODE_REFLECT
        return self.value(0) * self._scale('REFLECT')

    @property
    def ambient_light_intensity(self):
        """
        A measurement of the ambient light intensity, as a percentage.
        """
        self.mode = self.MODE_AMBIENT
        return self.value(0) * self._scale('AMBIENT')


class Led(Device):

    """
    Any device controlled by the generic LED driver.
    See https://www.kernel.org/doc/Documentation/leds/leds-class.txt
    for more details.
    """

    SYSTEM_CLASS_NAME = 'leds'
    SYSTEM_DEVICE_NAME_CONVENTION = '*'
    __slots__ = [
    '_max_brightness',
    '_brightness',
    '_triggers',
    '_trigger',
    '_delay_on',
    '_delay_off',
    ]

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


class PowerSupply(Device):

    """
    A generic interface to read data from the system's power_supply class.
    Uses the built-in legoev3-battery if none is specified.
    """

    SYSTEM_CLASS_NAME = 'power_supply'
    SYSTEM_DEVICE_NAME_CONVENTION = '*'
    __slots__ = [
    '_measured_current',
    '_measured_voltage',
    '_max_voltage',
    '_min_voltage',
    '_technology',
    '_type',
    ]

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
    __slots__ = [
    '_address',
    '_driver_name',
    '_modes',
    '_mode',
    '_set_device',
    '_status',
    ]

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


class FbMem(object):

    """The framebuffer memory object.

    Made of:
        - the framebuffer file descriptor
        - the fix screen info struct
        - the var screen info struct
        - the mapped memory
    """

    # ------------------------------------------------------------------
    # The code is adapted from
    # https://github.com/LinkCareServices/cairotft/blob/master/cairotft/linuxfb.py
    #
    # The original code came with the following license:
    # ------------------------------------------------------------------
    # Copyright (c) 2012 Kurichan
    #
    # This program is free software. It comes without any warranty, to
    # the extent permitted by applicable law. You can redistribute it
    # and/or modify it under the terms of the Do What The Fuck You Want
    # To Public License, Version 2, as published by Sam Hocevar. See
    # http://sam.zoy.org/wtfpl/COPYING for more details.
    # ------------------------------------------------------------------

    __slots__ = ('fid', 'fix_info', 'var_info', 'mmap')

    FBIOGET_VSCREENINFO = 0x4600
    FBIOGET_FSCREENINFO = 0x4602

    FB_VISUAL_MONO01 = 0
    FB_VISUAL_MONO10 = 1

    class FixScreenInfo(ctypes.Structure):

        """The fb_fix_screeninfo from fb.h."""

        _fields_ = [
            ('id_name', ctypes.c_char * 16),
            ('smem_start', ctypes.c_ulong),
            ('smem_len', ctypes.c_uint32),
            ('type', ctypes.c_uint32),
            ('type_aux', ctypes.c_uint32),
            ('visual', ctypes.c_uint32),
            ('xpanstep', ctypes.c_uint16),
            ('ypanstep', ctypes.c_uint16),
            ('ywrapstep', ctypes.c_uint16),
            ('line_length', ctypes.c_uint32),
            ('mmio_start', ctypes.c_ulong),
            ('mmio_len', ctypes.c_uint32),
            ('accel', ctypes.c_uint32),
            ('reserved', ctypes.c_uint16 * 3),
        ]

    class VarScreenInfo(ctypes.Structure):

        class FbBitField(ctypes.Structure):

            """The fb_bitfield struct from fb.h."""

            _fields_ = [
                ('offset', ctypes.c_uint32),
                ('length', ctypes.c_uint32),
                ('msb_right', ctypes.c_uint32),
            ]

        """The fb_var_screeninfo struct from fb.h."""

        _fields_ = [
            ('xres', ctypes.c_uint32),
            ('yres', ctypes.c_uint32),
            ('xres_virtual', ctypes.c_uint32),
            ('yres_virtual', ctypes.c_uint32),
            ('xoffset', ctypes.c_uint32),
            ('yoffset', ctypes.c_uint32),

            ('bits_per_pixel', ctypes.c_uint32),
            ('grayscale', ctypes.c_uint32),

            ('red', FbBitField),
            ('green', FbBitField),
            ('blue', FbBitField),
            ('transp', FbBitField),
        ]

    def __init__(self, fbdev=None):
        """Create the FbMem framebuffer memory object."""
        fid = FbMem._open_fbdev(fbdev)
        fix_info = FbMem._get_fix_info(fid)
        fbmmap = FbMem._map_fb_memory(fid, fix_info)
        self.fid = fid
        self.fix_info = fix_info
        self.var_info = FbMem._get_var_info(fid)
        self.mmap = fbmmap

    def __del__(self):
        """Close the FbMem framebuffer memory object."""
        self.mmap.close()
        FbMem._close_fbdev(self.fid)

    @staticmethod
    def _open_fbdev(fbdev=None):
        """Return the framebuffer file descriptor.

        Try to use the FRAMEBUFFER
        environment variable if fbdev is not given. Use '/dev/fb0' by
        default.
        """
        dev = fbdev or os.getenv('FRAMEBUFFER', '/dev/fb0')
        fbfid = os.open(dev, os.O_RDWR)
        return fbfid

    @staticmethod
    def _close_fbdev(fbfid):
        """Close the framebuffer file descriptor."""
        os.close(fbfid)

    @staticmethod
    def _get_fix_info(fbfid):
        """Return the fix screen info from the framebuffer file descriptor."""
        fix_info = FbMem.FixScreenInfo()
        fcntl.ioctl(fbfid, FbMem.FBIOGET_FSCREENINFO, fix_info)
        return fix_info

    @staticmethod
    def _get_var_info(fbfid):
        """Return the var screen info from the framebuffer file descriptor."""
        var_info = FbMem.VarScreenInfo()
        fcntl.ioctl(fbfid, FbMem.FBIOGET_VSCREENINFO, var_info)
        return var_info

    @staticmethod
    def _map_fb_memory(fbfid, fix_info):
        """Map the framebuffer memory."""
        return mmap.mmap(
            fbfid,
            fix_info.smem_len,
            mmap.MAP_SHARED,
            mmap.PROT_READ | mmap.PROT_WRITE,
            offset=0
        )


class Screen(FbMem):
    """
    A convenience wrapper for the FbMem class.
    Provides drawing functions from the python imaging library (PIL).
    """

    def __init__(self):
        from PIL import Image, ImageDraw
        FbMem.__init__(self)

        self._img = Image.new(
                self.var_info.bits_per_pixel == 1 and "1" or "RGB",
                (self.fix_info.line_length * 8 // self.var_info.bits_per_pixel, self.yres),
                "white")

        self._draw = ImageDraw.Draw(self._img)

    @property
    def xres(self):
        """
        Horizontal screen resolution
        """
        return self.var_info.xres

    @property
    def yres(self):
        """
        Vertical screen resolution
        """
        return self.var_info.yres

    @property
    def shape(self):
        """
        Dimensions of the screen.
        """
        return (self.xres, self.yres)

    @property
    def draw(self):
        """
        Returns a handle to PIL.ImageDraw.Draw class associated with the screen.

        Example::

            screen.draw.rectangle((10,10,60,20), fill='black')
        """
        return self._draw

    @property
    def image(self):
        """
        Returns a handle to PIL.Image class that is backing the screen. This can
        be accessed for blitting images to the screen.

        Example::

            screen.image.paste(picture, (0, 0))
        """
        return self._img

    def clear(self):
        """
        Clears the screen
        """
        self._draw.rectangle(((0, 0), self.shape), fill="white")

    def _color565(self, r, g, b):
        """Convert red, green, blue components to a 16-bit 565 RGB value. Components
        should be values 0 to 255.
        """
        return (((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3))

    def _img_to_rgb565_bytes(self):
        pixels = [self._color565(r, g, b) for (r, g, b) in self._img.getdata()]
        return pack('H' * len(pixels), *pixels)

    def update(self):
        """
        Applies pending changes to the screen.
        Nothing will be drawn on the screen until this function is called.
        """
        if self.var_info.bits_per_pixel == 1:
            self.mmap[:] = self._img.tobytes("raw", "1;IR")
        elif self.var_info.bits_per_pixel == 16:
            self.mmap[:] = self._img_to_rgb565_bytes()
        else:
            raise Exception("Not supported")


def _make_scales(notes):
    """ Utility function used by Sound class for building the note frequencies table """
    res = dict()
    for note, freq in notes:
        freq = round(freq)
        for n in note.split('/'):
            res[n] = freq
    return res


class Sound:
    """
    Sound-related functions. The class has only static methods and is not
    intended for instantiation. It can beep, play wav files, or convert text to
    speech.

    Note that all methods of the class spawn system processes and return
    subprocess.Popen objects. The methods are asynchronous (they return
    immediately after child process was spawned, without waiting for its
    completion), but you can call wait() on the returned result.

    Examples::

        # Play 'bark.wav', return immediately:
        Sound.play('bark.wav')

        # Introduce yourself, wait for completion:
        Sound.speak('Hello, I am Robot').wait()

        # Play a small song
        Sound.play_song((
            ('D4', 'e3'),
            ('D4', 'e3'),
            ('D4', 'e3'),
            ('G4', 'h'),
            ('D5', 'h')
        ))
    """

    channel = None

    @staticmethod
    def beep(args=''):
        """
        Call beep command with the provided arguments (if any).
        See `beep man page`_ and google `linux beep music`_ for inspiration.

        .. _`beep man page`: https://linux.die.net/man/1/beep
        .. _`linux beep music`: https://www.google.com/search?q=linux+beep+music
        """
        with open(os.devnull, 'w') as n:
            return Popen(shlex.split('/usr/bin/beep %s' % args), stdout=n)

    @staticmethod
    def tone(*args):
        """
        .. rubric:: tone(tone_sequence)

        Play tone sequence. The tone_sequence parameter is a list of tuples,
        where each tuple contains up to three numbers. The first number is
        frequency in Hz, the second is duration in milliseconds, and the third
        is delay in milliseconds between this and the next tone in the
        sequence.

        Here is a cheerful example::

            Sound.tone([
                (392, 350, 100), (392, 350, 100), (392, 350, 100), (311.1, 250, 100),
                (466.2, 25, 100), (392, 350, 100), (311.1, 250, 100), (466.2, 25, 100),
                (392, 700, 100), (587.32, 350, 100), (587.32, 350, 100),
                (587.32, 350, 100), (622.26, 250, 100), (466.2, 25, 100),
                (369.99, 350, 100), (311.1, 250, 100), (466.2, 25, 100), (392, 700, 100),
                (784, 350, 100), (392, 250, 100), (392, 25, 100), (784, 350, 100),
                (739.98, 250, 100), (698.46, 25, 100), (659.26, 25, 100),
                (622.26, 25, 100), (659.26, 50, 400), (415.3, 25, 200), (554.36, 350, 100),
                (523.25, 250, 100), (493.88, 25, 100), (466.16, 25, 100), (440, 25, 100),
                (466.16, 50, 400), (311.13, 25, 200), (369.99, 350, 100),
                (311.13, 250, 100), (392, 25, 100), (466.16, 350, 100), (392, 250, 100),
                (466.16, 25, 100), (587.32, 700, 100), (784, 350, 100), (392, 250, 100),
                (392, 25, 100), (784, 350, 100), (739.98, 250, 100), (698.46, 25, 100),
                (659.26, 25, 100), (622.26, 25, 100), (659.26, 50, 400), (415.3, 25, 200),
                (554.36, 350, 100), (523.25, 250, 100), (493.88, 25, 100),
                (466.16, 25, 100), (440, 25, 100), (466.16, 50, 400), (311.13, 25, 200),
                (392, 350, 100), (311.13, 250, 100), (466.16, 25, 100),
                (392.00, 300, 150), (311.13, 250, 100), (466.16, 25, 100), (392, 700)
                ]).wait()

        .. rubric:: tone(frequency, duration)

        Play single tone of given frequency (Hz) and duration (milliseconds).
        """
        def play_tone_sequence(tone_sequence):
            def beep_args(frequency=None, duration=None, delay=None):
                args = ''
                if frequency is not None: args += '-f %s ' % frequency
                if duration  is not None: args += '-l %s ' % duration
                if delay     is not None: args += '-D %s ' % delay

                return args

            return Sound.beep(' -n '.join([beep_args(*t) for t in tone_sequence]))

        if len(args) == 1:
            return play_tone_sequence(args[0])
        elif len(args) == 2:
            return play_tone_sequence([(args[0], args[1])])
        else:
            raise Exception("Unsupported number of parameters in Sound.tone()")

    @staticmethod
    def play(wav_file):
        """
        Play wav file.
        """
        with open(os.devnull, 'w') as n:
            return Popen(shlex.split('/usr/bin/aplay -q "%s"' % wav_file), stdout=n)

    @staticmethod
    def speak(text, espeak_opts='-a 200 -s 130'):
        """
        Speak the given text aloud.
        """
        with open(os.devnull, 'w') as n:
            cmd_line = '/usr/bin/espeak --stdout {0} "{1}"'.format(espeak_opts, text)
            espeak = Popen(shlex.split(cmd_line), stdout=PIPE)
            play = Popen(['/usr/bin/aplay', '-q'], stdin=espeak.stdout, stdout=n)
            return espeak

    @staticmethod
    def _get_channel():
        """
        :return: the detected sound channel
        :rtype: str
        """
        if Sound.channel is None:
            # Get default channel as the first one that pops up in
            # 'amixer scontrols' output, which contains strings in the
            # following format:
            #
            #     Simple mixer control 'Master',0
            #     Simple mixer control 'Capture',0
            out = check_output(['amixer', 'scontrols']).decode()
            m = re.search("'(?P<channel>[^']+)'", out)
            if m:
                Sound.channel = m.group('channel')
            else:
                Sound.channel = 'Playback'

        return Sound.channel

    @staticmethod
    def set_volume(pct, channel=None):
        """
        Sets the sound volume to the given percentage [0-100] by calling
        ``amixer -q set <channel> <pct>%``.
        If the channel is not specified, it tries to determine the default one
        by running ``amixer scontrols``. If that fails as well, it uses the
        ``Playback`` channel, as that is the only channel on the EV3.
        """

        if channel is None:
            channel = Sound._get_channel()

        cmd_line = '/usr/bin/amixer -q set {0} {1:d}%'.format(channel, pct)
        Popen(shlex.split(cmd_line)).wait()

    @staticmethod
    def get_volume(channel=None):
        """
        Gets the current sound volume by parsing the output of
        ``amixer get <channel>``.
        If the channel is not specified, it tries to determine the default one
        by running ``amixer scontrols``. If that fails as well, it uses the
        ``Playback`` channel, as that is the only channel on the EV3.
        """

        if channel is None:
            channel = Sound._get_channel()

        out = check_output(['amixer', 'get', channel]).decode()
        m = re.search('\[(?P<volume>\d+)%\]', out)
        if m:
            return int(m.group('volume'))
        else:
            raise Exception('Failed to parse output of `amixer get {}`'.format(channel))

    @classmethod
    def play_song(cls, song, tempo=120, delay=50):
        """ Plays a song provided as a list of tuples containing the note name and its
        value using music conventional notation instead of numerical values for frequency
        and duration.

        It supports symbolic notes (e.g. ``A4``, ``D#3``, ``Gb5``) and durations (e.g. ``q``, ``h``).

        For an exhaustive list of accepted note symbols and values, have a look at the :py:attr:`_NOTE_FREQUENCIES`
        and :py:attr:`_NOTE_VALUES` private dictionaries in the source code.

        The value can be suffixed by modifiers:

        - a *divider* introduced by a ``/`` to obtain triplets for instance
          (e.g. ``q/3`` for a triplet of eight note)
        - a *multiplier* introduced by ``*`` (e.g. ``*1.5`` is a dotted note).

        Shortcuts exist for common modifiers:

        - ``3`` produces a triplet member note. For instance `e3` gives a triplet of eight notes,
          i.e. 3 eight notes in the duration of a single quarter. You must ensure that 3 triplets
          notes are defined in sequence to match the count, otherwise the result will not be the
          expected one.
        - ``.`` produces a dotted note, i.e. which duration is one and a half the base one. Double dots
          are not currently supported.

        Example::

            >>> # A long time ago in a galaxy far,
            >>> # far away...
            >>> Sound.play_song((
            >>>     ('D4', 'e3'),      # intro anacrouse
            >>>     ('D4', 'e3'),
            >>>     ('D4', 'e3'),
            >>>     ('G4', 'h'),       # meas 1
            >>>     ('D5', 'h'),
            >>>     ('C5', 'e3'),      # meas 2
            >>>     ('B4', 'e3'),
            >>>     ('A4', 'e3'),
            >>>     ('G5', 'h'),
            >>>     ('D5', 'q'),
            >>>     ('C5', 'e3'),      # meas 3
            >>>     ('B4', 'e3'),
            >>>     ('A4', 'e3'),
            >>>     ('G5', 'h'),
            >>>     ('D5', 'q'),
            >>>     ('C5', 'e3'),      # meas 4
            >>>     ('B4', 'e3'),
            >>>     ('C5', 'e3'),
            >>>     ('A4', 'h.'),
            >>> ))

        .. important::

            Only 4/4 signature songs are supported with respect to note durations.

        Args:
            song (iterable[tuple(str, str)]): the song
            tempo (int): the song tempo, given in quarters per minute
            delay (int): delay in ms between notes

        Returns:
            subprocess.Popen: the spawn subprocess
        """
        meas_duration = 60000 / tempo * 4

        def beep_args(note, value):
            """ Builds the arguments string for producing a beep matching
            the requested note and value.

            Args:
                note (str): the note note and octave
                value (str): the note value expression
            Returns:
                str: the arguments to be passed to the beep command
            """
            freq = Sound._NOTE_FREQUENCIES[note.upper()]
            if '/' in value:
                base, factor = value.split('/')
                duration = meas_duration * Sound._NOTE_VALUES[base] / float(factor)
            elif '*' in value:
                base, factor = value.split('*')
                duration = meas_duration * Sound._NOTE_VALUES[base] * float(factor)
            elif value.endswith('.'):
                base = value[:-1]
                duration = meas_duration * Sound._NOTE_VALUES[base] * 1.5
            elif value.endswith('3'):
                base = value[:-1]
                duration = meas_duration * Sound._NOTE_VALUES[base] * 2 / 3
            else:
                duration = meas_duration * Sound._NOTE_VALUES[value]

            return '-f %d -l %d -D %d' % (freq, duration, delay)

        return Sound.beep(' -n '.join(
            [beep_args(note, value) for note, value in song]
        ))

    #: Note frequencies.
    #:
    #: This dictionary gives the rounded frequency of a note specified by its
    #: standard US abbreviation and its octave number (e.g. ``C3``).
    #: Alterations use the ``#`` and ``b`` symbols, respectively for
    #: *sharp* and *flat*, between the note code and the octave number (e.g. ``D#4``, ``Gb5``).
    _NOTE_FREQUENCIES = _make_scales((
        ('C0', 16.35),
        ('C#0/Db0', 17.32),
        ('D0', 18.35),
        ('D#0/Eb0', 19.45),     # expanded in one entry per symbol by _make_scales
        ('E0', 20.60),
        ('F0', 21.83),
        ('F#0/Gb0', 23.12),
        ('G0', 24.50),
        ('G#0/Ab0', 25.96),
        ('A0', 27.50),
        ('A#0/Bb0', 29.14),
        ('B0', 30.87),
        ('C1', 32.70),
        ('C#1/Db1', 34.65),
        ('D1', 36.71),
        ('D#1/Eb1', 38.89),
        ('E1', 41.20),
        ('F1', 43.65),
        ('F#1/Gb1', 46.25),
        ('G1', 49.00),
        ('G#1/Ab1', 51.91),
        ('A1', 55.00),
        ('A#1/Bb1', 58.27),
        ('B1', 61.74),
        ('C2', 65.41),
        ('C#2/Db2', 69.30),
        ('D2', 73.42),
        ('D#2/Eb2', 77.78),
        ('E2', 82.41),
        ('F2', 87.31),
        ('F#2/Gb2', 92.50),
        ('G2', 98.00),
        ('G#2/Ab2', 103.83),
        ('A2', 110.00),
        ('A#2/Bb2', 116.54),
        ('B2', 123.47),
        ('C3', 130.81),
        ('C#3/Db3', 138.59),
        ('D3', 146.83),
        ('D#3/Eb3', 155.56),
        ('E3', 164.81),
        ('F3', 174.61),
        ('F#3/Gb3', 185.00),
        ('G3', 196.00),
        ('G#3/Ab3', 207.65),
        ('A3', 220.00),
        ('A#3/Bb3', 233.08),
        ('B3', 246.94),
        ('C4', 261.63),
        ('C#4/Db4', 277.18),
        ('D4', 293.66),
        ('D#4/Eb4', 311.13),
        ('E4', 329.63),
        ('F4', 349.23),
        ('F#4/Gb4', 369.99),
        ('G4', 392.00),
        ('G#4/Ab4', 415.30),
        ('A4', 440.00),
        ('A#4/Bb4', 466.16),
        ('B4', 493.88),
        ('C5', 523.25),
        ('C#5/Db5', 554.37),
        ('D5', 587.33),
        ('D#5/Eb5', 622.25),
        ('E5', 659.25),
        ('F5', 698.46),
        ('F#5/Gb5', 739.99),
        ('G5', 783.99),
        ('G#5/Ab5', 830.61),
        ('A5', 880.00),
        ('A#5/Bb5', 932.33),
        ('B5', 987.77),
        ('C6', 1046.50),
        ('C#6/Db6', 1108.73),
        ('D6', 1174.66),
        ('D#6/Eb6', 1244.51),
        ('E6', 1318.51),
        ('F6', 1396.91),
        ('F#6/Gb6', 1479.98),
        ('G6', 1567.98),
        ('G#6/Ab6', 1661.22),
        ('A6', 1760.00),
        ('A#6/Bb6', 1864.66),
        ('B6', 1975.53),
        ('C7', 2093.00),
        ('C#7/Db7', 2217.46),
        ('D7', 2349.32),
        ('D#7/Eb7', 2489.02),
        ('E7', 2637.02),
        ('F7', 2793.83),
        ('F#7/Gb7', 2959.96),
        ('G7', 3135.96),
        ('G#7/Ab7', 3322.44),
        ('A7', 3520.00),
        ('A#7/Bb7', 3729.31),
        ('B7', 3951.07),
        ('C8', 4186.01),
        ('C#8/Db8', 4434.92),
        ('D8', 4698.63),
        ('D#8/Eb8', 4978.03),
        ('E8', 5274.04),
        ('F8', 5587.65),
        ('F#8/Gb8', 5919.91),
        ('G8', 6271.93),
        ('G#8/Ab8', 6644.88),
        ('A8', 7040.00),
        ('A#8/Bb8', 7458.62),
        ('B8', 7902.13)
    ))

    #: Common note values.
    #:
    #: See https://en.wikipedia.org/wiki/Note_value
    #:
    #: This dictionary provides the multiplier to be applied to de whole note duration
    #: to obtain subdivisions, given the corresponding symbolic identifier:
    #:
    #:  = ===============================
    #:  w whole note (UK: semibreve)
    #:  h half note (UK: minim)
    #:  q quarter note (UK: crotchet)
    #:  e eight note (UK: quaver)
    #:  s sixteenth note (UK: semiquaver)
    #:  = ===============================
    #:
    #:
    #: Triplets can be obtained by dividing the corresponding reference by 3.
    #: For instance, the note value of a eight triplet will be ``NOTE_VALUE['e'] / 3``.
    #: It is simpler however to user the ``3`` modifier of notes, as supported by the
    #: :py:meth:`Sound.play_song` method.
    _NOTE_VALUES = {
        'w': 1.,
        'h': 1./2,
        'q': 1./4,
        'e': 1./8,
        's': 1./16,
    }


