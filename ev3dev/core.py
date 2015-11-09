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
# Sections of the following code were auto-generated based on spec v0.9.3-pre, rev 2

# ~autogen

import os
import fnmatch
import numbers
import fcntl
import array
import mmap
import ctypes
import re
import stat
from os.path import abspath
from PIL import Image, ImageDraw
from struct import pack, unpack
from subprocess import Popen

INPUT_AUTO = ''
OUTPUT_AUTO = ''

# -----------------------------------------------------------------------------
# Attribute reader/writer with cached file access
class FileCache(object):
    def __init__(self):
        self._cache = {}

    def __del__(self):
        for f in self._cache.values():
            f.close()

    def file_handle(self, path, binary=False):
        """Manages the file handle cache and opening the files in the correct mode"""

        if path not in self._cache:
            mode = stat.S_IMODE(os.stat(path)[stat.ST_MODE])

            r_ok = mode & stat.S_IRGRP
            w_ok = mode & stat.S_IWGRP

            if r_ok and w_ok:
                mode = 'a+'
            elif w_ok:
                mode = 'a'
            else:
                mode = 'r'

            if binary:
                mode += 'b'

            f = open(path, mode, 0)
            self._cache[path] = f
        else:
            f = self._cache[path]

        return f

    def read(self, path):
        f = self.file_handle(path)

        f.seek(0)
        return f.read().strip()

    def write(self, path, value):
        f = self.file_handle(path)

        f.seek(0)
        f.write(value)


# -----------------------------------------------------------------------------
# Define the base class from which all other ev3dev classes are defined.

class Device(object):
    """The ev3dev device base class"""

    DEVICE_ROOT_PATH = '/sys/class'

    _DEVICE_INDEX = re.compile(r'^.*(?P<idx>\d+)$')

    def __init__(self, class_name, name='*', **kwargs):
        """Spin through the Linux sysfs class for the device type and find
        a device that matches the provided name and attributes (if any).

        Parameters:
            class_name: class name of the device, a subdirectory of /sys/class.
                For example, 'tacho-motor'.
            name: pattern that device name should match.
                For example, 'sensor*' or 'motor*'. Default value: '*'.
            keyword arguments: used for matching the corresponding device
                attributes. For example, port_name='outA', or
                driver_name=['lego-ev3-us', 'lego-nxt-us']. When argument value
                is a list, then a match against any entry of the list is
                enough.

        Example::

            d = ev3dev.Device('tacho-motor', port_name='outA')
            s = ev3dev.Device('lego-sensor', driver_name=['lego-ev3-us', 'lego-nxt-us'])

        When connected succesfully, the `connected` attribute is set to True.
        """

        classpath = abspath(Device.DEVICE_ROOT_PATH + '/' + class_name)
        self._attribute_cache = FileCache()

        for file in os.listdir(classpath):
            if fnmatch.fnmatch(file, name):
                self._path = abspath(classpath + '/' + file)

                # See if requested attributes match:
                if all([self._matches(k, kwargs[k]) for k in kwargs]):
                    self.connected = True

                    match = Device._DEVICE_INDEX.match(file)
                    if match:
                        self._device_index = int(match.group('idx'))
                    else:
                        self._device_index = None

                    return

        self._path = ''
        self.connected = False

    def _matches(self, attribute, pattern):
        """Test if attribute value matches pattern (that is, if pattern is a
        substring of attribute value).  If pattern is a list, then a match with
        any one entry is enough.
        """
        value = self._get_attribute(attribute)
        if isinstance(pattern, list):
            return any([value.find(pat) >= 0 for pat in pattern])
        else:
            return value.find(pattern) >= 0

    def _get_attribute(self, attribute):
        """Device attribute getter"""
        return self._attribute_cache.read(abspath(self._path + '/' + attribute))

    def _set_attribute(self, attribute, value):
        """Device attribute setter"""
        self._attribute_cache.write(abspath(self._path + '/' + attribute), value)

    def get_attr_int(self, attribute):
        return int(self._get_attribute(attribute))

    def set_attr_int(self, attribute, value):
        self._set_attribute(attribute, '{0:d}'.format(int(value)))

    def get_attr_string(self, attribute):
        return self._get_attribute(attribute)

    def set_attr_string(self, attribute, value):
        self._set_attribute(attribute, "{0}".format(value))

    def get_attr_line(self, attribute):
        return self._get_attribute(attribute)

    def get_attr_set(self, attribute):
        return [v.strip('[]') for v in self.get_attr_line(attribute).split()]

    def get_attr_from_set(self, attribute):
        for a in self.get_attr_line(attribute).split():
            v = a.strip('[]')
            if v != a:
                return v
        return ""

    @property
    def device_index(self):
        return self._device_index


# ~autogen generic-class classes.motor>currentClass

class Motor(Device):

    """
    The motor class provides a uniform interface for using motors with
    positional and directional feedback such as the EV3 and NXT motors.
    This feedback allows for precise control of the motors. This is the
    most common type of motor, so we just call it `motor`.
    """

    SYSTEM_CLASS_NAME = 'tacho-motor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'motor*'

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)


# ~autogen

    def __del__(self):
        self.stop()

# ~autogen generic-get-set classes.motor>currentClass

    @property
    def command(self):
        """
        Sends a command to the motor controller. See `commands` for a list of
        possible values.
        """
        raise Exception("command is a write-only property!")

    @command.setter
    def command(self, value):
        self.set_attr_string('command', value)

    @property
    def commands(self):
        """
        Returns a list of commands that are supported by the motor
        controller. Possible values are `run-forever`, `run-to-abs-pos`, `run-to-rel-pos`,
        `run-timed`, `run-direct`, `stop` and `reset`. Not all commands may be supported.

        - `run-forever` will cause the motor to run until another command is sent.
        - `run-to-abs-pos` will run to an absolute position specified by `position_sp`
          and then stop using the command specified in `stop_command`.
        - `run-to-rel-pos` will run to a position relative to the current `position` value.
          The new position will be current `position` + `position_sp`. When the new
          position is reached, the motor will stop using the command specified by `stop_command`.
        - `run-timed` will run the motor for the amount of time specified in `time_sp`
          and then stop the motor using the command specified by `stop_command`.
        - `run-direct` will run the motor at the duty cycle specified by `duty_cycle_sp`.
          Unlike other run commands, changing `duty_cycle_sp` while running *will*
          take effect immediately.
        - `stop` will stop any of the run commands before they are complete using the
          command specified by `stop_command`.
        - `reset` will reset all of the motor parameter attributes to their default value.
          This will also have the effect of stopping the motor.
        """
        return self.get_attr_set('commands')

    @property
    def count_per_rot(self):
        """
        Returns the number of tacho counts in one rotation of the motor. Tacho counts
        are used by the position and speed attributes, so you can use this value
        to convert rotations or degrees to tacho counts. In the case of linear
        actuators, the units here will be counts per centimeter.
        """
        return self.get_attr_int('count_per_rot')

    @property
    def driver_name(self):
        """
        Returns the name of the driver that provides this tacho motor device.
        """
        return self.get_attr_string('driver_name')

    @property
    def duty_cycle(self):
        """
        Returns the current duty cycle of the motor. Units are percent. Values
        are -100 to 100.
        """
        return self.get_attr_int('duty_cycle')

    @property
    def duty_cycle_sp(self):
        """
        Writing sets the duty cycle setpoint. Reading returns the current value.
        Units are in percent. Valid values are -100 to 100. A negative value causes
        the motor to rotate in reverse. This value is only used when `speed_regulation`
        is off.
        """
        return self.get_attr_int('duty_cycle_sp')

    @duty_cycle_sp.setter
    def duty_cycle_sp(self, value):
        self.set_attr_int('duty_cycle_sp', value)

    @property
    def encoder_polarity(self):
        """
        Sets the polarity of the rotary encoder. This is an advanced feature to all
        use of motors that send inversed encoder signals to the EV3. This should
        be set correctly by the driver of a device. It You only need to change this
        value if you are using a unsupported device. Valid values are `normal` and
        `inversed`.
        """
        return self.get_attr_string('encoder_polarity')

    @encoder_polarity.setter
    def encoder_polarity(self, value):
        self.set_attr_string('encoder_polarity', value)

    @property
    def polarity(self):
        """
        Sets the polarity of the motor. With `normal` polarity, a positive duty
        cycle will cause the motor to rotate clockwise. With `inversed` polarity,
        a positive duty cycle will cause the motor to rotate counter-clockwise.
        Valid values are `normal` and `inversed`.
        """
        return self.get_attr_string('polarity')

    @polarity.setter
    def polarity(self, value):
        self.set_attr_string('polarity', value)

    @property
    def port_name(self):
        """
        Returns the name of the port that the motor is connected to.
        """
        return self.get_attr_string('port_name')

    @property
    def position(self):
        """
        Returns the current position of the motor in pulses of the rotary
        encoder. When the motor rotates clockwise, the position will increase.
        Likewise, rotating counter-clockwise causes the position to decrease.
        Writing will set the position to that value.
        """
        return self.get_attr_int('position')

    @position.setter
    def position(self, value):
        self.set_attr_int('position', value)

    @property
    def position_p(self):
        """
        The proportional constant for the position PID.
        """
        return self.get_attr_int('hold_pid/Kp')

    @position_p.setter
    def position_p(self, value):
        self.set_attr_int('hold_pid/Kp', value)

    @property
    def position_i(self):
        """
        The integral constant for the position PID.
        """
        return self.get_attr_int('hold_pid/Ki')

    @position_i.setter
    def position_i(self, value):
        self.set_attr_int('hold_pid/Ki', value)

    @property
    def position_d(self):
        """
        The derivative constant for the position PID.
        """
        return self.get_attr_int('hold_pid/Kd')

    @position_d.setter
    def position_d(self, value):
        self.set_attr_int('hold_pid/Kd', value)

    @property
    def position_sp(self):
        """
        Writing specifies the target position for the `run-to-abs-pos` and `run-to-rel-pos`
        commands. Reading returns the current value. Units are in tacho counts. You
        can use the value returned by `counts_per_rot` to convert tacho counts to/from
        rotations or degrees.
        """
        return self.get_attr_int('position_sp')

    @position_sp.setter
    def position_sp(self, value):
        self.set_attr_int('position_sp', value)

    @property
    def speed(self):
        """
        Returns the current motor speed in tacho counts per second. Not, this is
        not necessarily degrees (although it is for LEGO motors). Use the `count_per_rot`
        attribute to convert this value to RPM or deg/sec.
        """
        return self.get_attr_int('speed')

    @property
    def speed_sp(self):
        """
        Writing sets the target speed in tacho counts per second used when `speed_regulation`
        is on. Reading returns the current value.  Use the `count_per_rot` attribute
        to convert RPM or deg/sec to tacho counts per second.
        """
        return self.get_attr_int('speed_sp')

    @speed_sp.setter
    def speed_sp(self, value):
        self.set_attr_int('speed_sp', value)

    @property
    def ramp_up_sp(self):
        """
        Writing sets the ramp up setpoint. Reading returns the current value. Units
        are in milliseconds. When set to a value > 0, the motor will ramp the power
        sent to the motor from 0 to 100% duty cycle over the span of this setpoint
        when starting the motor. If the maximum duty cycle is limited by `duty_cycle_sp`
        or speed regulation, the actual ramp time duration will be less than the setpoint.
        """
        return self.get_attr_int('ramp_up_sp')

    @ramp_up_sp.setter
    def ramp_up_sp(self, value):
        self.set_attr_int('ramp_up_sp', value)

    @property
    def ramp_down_sp(self):
        """
        Writing sets the ramp down setpoint. Reading returns the current value. Units
        are in milliseconds. When set to a value > 0, the motor will ramp the power
        sent to the motor from 100% duty cycle down to 0 over the span of this setpoint
        when stopping the motor. If the starting duty cycle is less than 100%, the
        ramp time duration will be less than the full span of the setpoint.
        """
        return self.get_attr_int('ramp_down_sp')

    @ramp_down_sp.setter
    def ramp_down_sp(self, value):
        self.set_attr_int('ramp_down_sp', value)

    @property
    def speed_regulation_enabled(self):
        """
        Turns speed regulation on or off. If speed regulation is on, the motor
        controller will vary the power supplied to the motor to try to maintain the
        speed specified in `speed_sp`. If speed regulation is off, the controller
        will use the power specified in `duty_cycle_sp`. Valid values are `on` and
        `off`.
        """
        return self.get_attr_string('speed_regulation')

    @speed_regulation_enabled.setter
    def speed_regulation_enabled(self, value):
        self.set_attr_string('speed_regulation', value)

    @property
    def speed_regulation_p(self):
        """
        The proportional constant for the speed regulation PID.
        """
        return self.get_attr_int('speed_pid/Kp')

    @speed_regulation_p.setter
    def speed_regulation_p(self, value):
        self.set_attr_int('speed_pid/Kp', value)

    @property
    def speed_regulation_i(self):
        """
        The integral constant for the speed regulation PID.
        """
        return self.get_attr_int('speed_pid/Ki')

    @speed_regulation_i.setter
    def speed_regulation_i(self, value):
        self.set_attr_int('speed_pid/Ki', value)

    @property
    def speed_regulation_d(self):
        """
        The derivative constant for the speed regulation PID.
        """
        return self.get_attr_int('speed_pid/Kd')

    @speed_regulation_d.setter
    def speed_regulation_d(self, value):
        self.set_attr_int('speed_pid/Kd', value)

    @property
    def state(self):
        """
        Reading returns a list of state flags. Possible flags are
        `running`, `ramping` `holding` and `stalled`.
        """
        return self.get_attr_set('state')

    @property
    def stop_command(self):
        """
        Reading returns the current stop command. Writing sets the stop command.
        The value determines the motors behavior when `command` is set to `stop`.
        Also, it determines the motors behavior when a run command completes. See
        `stop_commands` for a list of possible values.
        """
        return self.get_attr_string('stop_command')

    @stop_command.setter
    def stop_command(self, value):
        self.set_attr_string('stop_command', value)

    @property
    def stop_commands(self):
        """
        Returns a list of stop modes supported by the motor controller.
        Possible values are `coast`, `brake` and `hold`. `coast` means that power will
        be removed from the motor and it will freely coast to a stop. `brake` means
        that power will be removed from the motor and a passive electrical load will
        be placed on the motor. This is usually done by shorting the motor terminals
        together. This load will absorb the energy from the rotation of the motors and
        cause the motor to stop more quickly than coasting. `hold` does not remove
        power from the motor. Instead it actively try to hold the motor at the current
        position. If an external force tries to turn the motor, the motor will 'push
        back' to maintain its position.
        """
        return self.get_attr_set('stop_commands')

    @property
    def time_sp(self):
        """
        Writing specifies the amount of time the motor will run when using the
        `run-timed` command. Reading returns the current value. Units are in
        milliseconds.
        """
        return self.get_attr_int('time_sp')

    @time_sp.setter
    def time_sp(self, value):
        self.set_attr_int('time_sp', value)


# ~autogen
# ~autogen generic-property-value classes.motor>currentClass

    # Run the motor until another command is sent.
    COMMAND_RUN_FOREVER = 'run-forever'

    # Run to an absolute position specified by `position_sp` and then
    # stop using the command specified in `stop_command`.
    COMMAND_RUN_TO_ABS_POS = 'run-to-abs-pos'

    # Run to a position relative to the current `position` value.
    # The new position will be current `position` + `position_sp`.
    # When the new position is reached, the motor will stop using
    # the command specified by `stop_command`.
    COMMAND_RUN_TO_REL_POS = 'run-to-rel-pos'

    # Run the motor for the amount of time specified in `time_sp`
    # and then stop the motor using the command specified by `stop_command`.
    COMMAND_RUN_TIMED = 'run-timed'

    # Run the motor at the duty cycle specified by `duty_cycle_sp`.
    # Unlike other run commands, changing `duty_cycle_sp` while running *will*
    # take effect immediately.
    COMMAND_RUN_DIRECT = 'run-direct'

    # Stop any of the run commands before they are complete using the
    # command specified by `stop_command`.
    COMMAND_STOP = 'stop'

    # Reset all of the motor parameter attributes to their default value.
    # This will also have the effect of stopping the motor.
    COMMAND_RESET = 'reset'

    # Sets the normal polarity of the rotary encoder.
    ENCODER_POLARITY_NORMAL = 'normal'

    # Sets the inversed polarity of the rotary encoder.
    ENCODER_POLARITY_INVERSED = 'inversed'

    # With `normal` polarity, a positive duty cycle will
    # cause the motor to rotate clockwise.
    POLARITY_NORMAL = 'normal'

    # With `inversed` polarity, a positive duty cycle will
    # cause the motor to rotate counter-clockwise.
    POLARITY_INVERSED = 'inversed'

    # The motor controller will vary the power supplied to the motor
    # to try to maintain the speed specified in `speed_sp`.
    SPEED_REGULATION_ON = 'on'

    # The motor controller will use the power specified in `duty_cycle_sp`.
    SPEED_REGULATION_OFF = 'off'

    # Power will be removed from the motor and it will freely coast to a stop.
    STOP_COMMAND_COAST = 'coast'

    # Power will be removed from the motor and a passive electrical load will
    # be placed on the motor. This is usually done by shorting the motor terminals
    # together. This load will absorb the energy from the rotation of the motors and
    # cause the motor to stop more quickly than coasting.
    STOP_COMMAND_BRAKE = 'brake'

    # Does not remove power from the motor. Instead it actively try to hold the motor
    # at the current position. If an external force tries to turn the motor, the motor
    # will ``push back`` to maintain its position.
    STOP_COMMAND_HOLD = 'hold'


# ~autogen
# ~autogen motor_commands classes.motor>currentClass

    def run_forever(self, **kwargs):
        """Run the motor until another command is sent.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-forever'

    def run_to_abs_pos(self, **kwargs):
        """Run to an absolute position specified by `position_sp` and then
        stop using the command specified in `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-to-abs-pos'

    def run_to_rel_pos(self, **kwargs):
        """Run to a position relative to the current `position` value.
        The new position will be current `position` + `position_sp`.
        When the new position is reached, the motor will stop using
        the command specified by `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-to-rel-pos'

    def run_timed(self, **kwargs):
        """Run the motor for the amount of time specified in `time_sp`
        and then stop the motor using the command specified by `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-timed'

    def run_direct(self, **kwargs):
        """Run the motor at the duty cycle specified by `duty_cycle_sp`.
        Unlike other run commands, changing `duty_cycle_sp` while running *will*
        take effect immediately.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-direct'

    def stop(self, **kwargs):
        """Stop any of the run commands before they are complete using the
        command specified by `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'stop'

    def reset(self, **kwargs):
        """Reset all of the motor parameter attributes to their default value.
        This will also have the effect of stopping the motor.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'reset'


# ~autogen
# ~autogen generic-class classes.largeMotor>currentClass

class LargeMotor(Motor):

    """
    EV3 large servo motor
    """

    SYSTEM_CLASS_NAME = Motor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Motor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-l-motor'], **kwargs)


# ~autogen
# ~autogen generic-class classes.mediumMotor>currentClass

class MediumMotor(Motor):

    """
    EV3 medium servo motor
    """

    SYSTEM_CLASS_NAME = Motor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Motor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-m-motor'], **kwargs)


# ~autogen
# ~autogen generic-class classes.dcMotor>currentClass

class DcMotor(Device):

    """
    The DC motor class provides a uniform interface for using regular DC motors
    with no fancy controls or feedback. This includes LEGO MINDSTORMS RCX motors
    and LEGO Power Functions motors.
    """

    SYSTEM_CLASS_NAME = 'dc-motor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'motor*'

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)


# ~autogen

    def __del__(self):
        self.stop()

# ~autogen generic-get-set classes.dcMotor>currentClass

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
        self.set_attr_string('command', value)

    @property
    def commands(self):
        """
        Returns a list of commands supported by the motor
        controller.
        """
        return self.get_attr_set('commands')

    @property
    def driver_name(self):
        """
        Returns the name of the motor driver that loaded this device. See the list
        of [supported devices] for a list of drivers.
        """
        return self.get_attr_string('driver_name')

    @property
    def duty_cycle(self):
        """
        Shows the current duty cycle of the PWM signal sent to the motor. Values
        are -100 to 100 (-100% to 100%).
        """
        return self.get_attr_int('duty_cycle')

    @property
    def duty_cycle_sp(self):
        """
        Writing sets the duty cycle setpoint of the PWM signal sent to the motor.
        Valid values are -100 to 100 (-100% to 100%). Reading returns the current
        setpoint.
        """
        return self.get_attr_int('duty_cycle_sp')

    @duty_cycle_sp.setter
    def duty_cycle_sp(self, value):
        self.set_attr_int('duty_cycle_sp', value)

    @property
    def polarity(self):
        """
        Sets the polarity of the motor. Valid values are `normal` and `inversed`.
        """
        return self.get_attr_string('polarity')

    @polarity.setter
    def polarity(self, value):
        self.set_attr_string('polarity', value)

    @property
    def port_name(self):
        """
        Returns the name of the port that the motor is connected to.
        """
        return self.get_attr_string('port_name')

    @property
    def ramp_down_sp(self):
        """
        Sets the time in milliseconds that it take the motor to ramp down from 100%
        to 0%. Valid values are 0 to 10000 (10 seconds). Default is 0.
        """
        return self.get_attr_int('ramp_down_sp')

    @ramp_down_sp.setter
    def ramp_down_sp(self, value):
        self.set_attr_int('ramp_down_sp', value)

    @property
    def ramp_up_sp(self):
        """
        Sets the time in milliseconds that it take the motor to up ramp from 0% to
        100%. Valid values are 0 to 10000 (10 seconds). Default is 0.
        """
        return self.get_attr_int('ramp_up_sp')

    @ramp_up_sp.setter
    def ramp_up_sp(self, value):
        self.set_attr_int('ramp_up_sp', value)

    @property
    def state(self):
        """
        Gets a list of flags indicating the motor status. Possible
        flags are `running` and `ramping`. `running` indicates that the motor is
        powered. `ramping` indicates that the motor has not yet reached the
        `duty_cycle_sp`.
        """
        return self.get_attr_set('state')

    @property
    def stop_command(self):
        """
        Sets the stop command that will be used when the motor stops. Read
        `stop_commands` to get the list of valid values.
        """
        raise Exception("stop_command is a write-only property!")

    @stop_command.setter
    def stop_command(self, value):
        self.set_attr_string('stop_command', value)

    @property
    def stop_commands(self):
        """
        Gets a list of stop commands. Valid values are `coast`
        and `brake`.
        """
        return self.get_attr_set('stop_commands')

    @property
    def time_sp(self):
        """
        Writing specifies the amount of time the motor will run when using the
        `run-timed` command. Reading returns the current value. Units are in
        milliseconds.
        """
        return self.get_attr_int('time_sp')

    @time_sp.setter
    def time_sp(self, value):
        self.set_attr_int('time_sp', value)


# ~autogen
# ~autogen generic-property-value classes.dcMotor>currentClass

    # Run the motor until another command is sent.
    COMMAND_RUN_FOREVER = 'run-forever'

    # Run the motor for the amount of time specified in `time_sp`
    # and then stop the motor using the command specified by `stop_command`.
    COMMAND_RUN_TIMED = 'run-timed'

    # Run the motor at the duty cycle specified by `duty_cycle_sp`.
    # Unlike other run commands, changing `duty_cycle_sp` while running *will*
    # take effect immediately.
    COMMAND_RUN_DIRECT = 'run-direct'

    # Stop any of the run commands before they are complete using the
    # command specified by `stop_command`.
    COMMAND_STOP = 'stop'

    # With `normal` polarity, a positive duty cycle will
    # cause the motor to rotate clockwise.
    POLARITY_NORMAL = 'normal'

    # With `inversed` polarity, a positive duty cycle will
    # cause the motor to rotate counter-clockwise.
    POLARITY_INVERSED = 'inversed'

    # Power will be removed from the motor and it will freely coast to a stop.
    STOP_COMMAND_COAST = 'coast'

    # Power will be removed from the motor and a passive electrical load will
    # be placed on the motor. This is usually done by shorting the motor terminals
    # together. This load will absorb the energy from the rotation of the motors and
    # cause the motor to stop more quickly than coasting.
    STOP_COMMAND_BRAKE = 'brake'


# ~autogen
# ~autogen motor_commands classes.dcMotor>currentClass

    def run_forever(self, **kwargs):
        """Run the motor until another command is sent.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-forever'

    def run_timed(self, **kwargs):
        """Run the motor for the amount of time specified in `time_sp`
        and then stop the motor using the command specified by `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-timed'

    def run_direct(self, **kwargs):
        """Run the motor at the duty cycle specified by `duty_cycle_sp`.
        Unlike other run commands, changing `duty_cycle_sp` while running *will*
        take effect immediately.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-direct'

    def stop(self, **kwargs):
        """Stop any of the run commands before they are complete using the
        command specified by `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'stop'


# ~autogen
# ~autogen generic-class classes.servoMotor>currentClass

class ServoMotor(Device):

    """
    The servo motor class provides a uniform interface for using hobby type
    servo motors.
    """

    SYSTEM_CLASS_NAME = 'servo-motor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'motor*'

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)


# ~autogen

    def __del__(self):
        self.float()

# ~autogen generic-get-set classes.servoMotor>currentClass

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
        self.set_attr_string('command', value)

    @property
    def driver_name(self):
        """
        Returns the name of the motor driver that loaded this device. See the list
        of [supported devices] for a list of drivers.
        """
        return self.get_attr_string('driver_name')

    @property
    def max_pulse_sp(self):
        """
        Used to set the pulse size in milliseconds for the signal that tells the
        servo to drive to the maximum (clockwise) position_sp. Default value is 2400.
        Valid values are 2300 to 2700. You must write to the position_sp attribute for
        changes to this attribute to take effect.
        """
        return self.get_attr_int('max_pulse_sp')

    @max_pulse_sp.setter
    def max_pulse_sp(self, value):
        self.set_attr_int('max_pulse_sp', value)

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
        return self.get_attr_int('mid_pulse_sp')

    @mid_pulse_sp.setter
    def mid_pulse_sp(self, value):
        self.set_attr_int('mid_pulse_sp', value)

    @property
    def min_pulse_sp(self):
        """
        Used to set the pulse size in milliseconds for the signal that tells the
        servo to drive to the miniumum (counter-clockwise) position_sp. Default value
        is 600. Valid values are 300 to 700. You must write to the position_sp
        attribute for changes to this attribute to take effect.
        """
        return self.get_attr_int('min_pulse_sp')

    @min_pulse_sp.setter
    def min_pulse_sp(self, value):
        self.set_attr_int('min_pulse_sp', value)

    @property
    def polarity(self):
        """
        Sets the polarity of the servo. Valid values are `normal` and `inversed`.
        Setting the value to `inversed` will cause the position_sp value to be
        inversed. i.e `-100` will correspond to `max_pulse_sp`, and `100` will
        correspond to `min_pulse_sp`.
        """
        return self.get_attr_string('polarity')

    @polarity.setter
    def polarity(self, value):
        self.set_attr_string('polarity', value)

    @property
    def port_name(self):
        """
        Returns the name of the port that the motor is connected to.
        """
        return self.get_attr_string('port_name')

    @property
    def position_sp(self):
        """
        Reading returns the current position_sp of the servo. Writing instructs the
        servo to move to the specified position_sp. Units are percent. Valid values
        are -100 to 100 (-100% to 100%) where `-100` corresponds to `min_pulse_sp`,
        `0` corresponds to `mid_pulse_sp` and `100` corresponds to `max_pulse_sp`.
        """
        return self.get_attr_int('position_sp')

    @position_sp.setter
    def position_sp(self, value):
        self.set_attr_int('position_sp', value)

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
        return self.get_attr_int('rate_sp')

    @rate_sp.setter
    def rate_sp(self, value):
        self.set_attr_int('rate_sp', value)

    @property
    def state(self):
        """
        Returns a list of flags indicating the state of the servo.
        Possible values are:
        * `running`: Indicates that the motor is powered.
        """
        return self.get_attr_set('state')


# ~autogen
# ~autogen generic-property-value classes.servoMotor>currentClass

    # Drive servo to the position set in the `position_sp` attribute.
    COMMAND_RUN = 'run'

    # Remove power from the motor.
    COMMAND_FLOAT = 'float'

    # With `normal` polarity, a positive duty cycle will
    # cause the motor to rotate clockwise.
    POLARITY_NORMAL = 'normal'

    # With `inversed` polarity, a positive duty cycle will
    # cause the motor to rotate counter-clockwise.
    POLARITY_INVERSED = 'inversed'


# ~autogen
# ~autogen motor_commands classes.servoMotor>currentClass

    def run(self, **kwargs):
        """Drive servo to the position set in the `position_sp` attribute.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run'

    def float(self, **kwargs):
        """Remove power from the motor.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'float'


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
    that a sensor is plugged in to, you must look at the `port_name` attribute if
    you need to know which port a sensor is plugged in to. However, if you don't
    have more than one sensor of each type, you can just look for a matching
    `driver_name`. Then it will not matter which port a sensor is plugged in to - your
    program will still work.
    """

    SYSTEM_CLASS_NAME = 'lego-sensor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'sensor*'

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)


# ~autogen
# ~autogen generic-get-set classes.sensor>currentClass

    @property
    def command(self):
        """
        Sends a command to the sensor.
        """
        raise Exception("command is a write-only property!")

    @command.setter
    def command(self, value):
        self.set_attr_string('command', value)

    @property
    def commands(self):
        """
        Returns a list of the valid commands for the sensor.
        Returns -EOPNOTSUPP if no commands are supported.
        """
        return self.get_attr_set('commands')

    @property
    def decimals(self):
        """
        Returns the number of decimal places for the values in the `value<N>`
        attributes of the current mode.
        """
        return self.get_attr_int('decimals')

    @property
    def driver_name(self):
        """
        Returns the name of the sensor device/driver. See the list of [supported
        sensors] for a complete list of drivers.
        """
        return self.get_attr_string('driver_name')

    @property
    def mode(self):
        """
        Returns the current mode. Writing one of the values returned by `modes`
        sets the sensor to that mode.
        """
        return self.get_attr_string('mode')

    @mode.setter
    def mode(self, value):
        self.set_attr_string('mode', value)

    @property
    def modes(self):
        """
        Returns a list of the valid modes for the sensor.
        """
        return self.get_attr_set('modes')

    @property
    def num_values(self):
        """
        Returns the number of `value<N>` attributes that will return a valid value
        for the current mode.
        """
        return self.get_attr_int('num_values')

    @property
    def port_name(self):
        """
        Returns the name of the port that the sensor is connected to, e.g. `ev3:in1`.
        I2C sensors also include the I2C address (decimal), e.g. `ev3:in1:i2c8`.
        """
        return self.get_attr_string('port_name')

    @property
    def units(self):
        """
        Returns the units of the measured value for the current mode. May return
        empty string
        """
        return self.get_attr_string('units')


# ~autogen

    def value(self, n=0):
        if isinstance(n, numbers.Integral):
            n = '{0:d}'.format(n)
        elif isinstance(n, numbers.Real):
            n = '{0:.0f}'.format(n)

        if isinstance(n, str):
            return self.get_attr_int('value'+n)
        else:
            return 0

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
        return self.get_attr_string('bin_data_format')

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

        if '_bin_data_size' not in self.__dict__:
            self._bin_data_size = {
                    "u8":     1,
                    "s8":     1,
                    "u16":    2,
                    "s16":    2,
                    "s16_be": 2,
                    "s32":    4,
                    "float":  4
                }.get(self.bin_data_format, 1) * self.num_values

        f = self._attribute_cache.file_handle(abspath(self._path + '/bin_data'), binary=True)
        f.seek(0)
        raw = bytearray(f.read(self._bin_data_size))

        if fmt is None: return raw

        return unpack(fmt, raw)


# ~autogen generic-class classes.i2cSensor>currentClass

class I2cSensor(Sensor):

    """
    A generic interface to control I2C-type EV3 sensors.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['nxt-i2c-sensor'], **kwargs)


# ~autogen
# ~autogen generic-get-set classes.i2cSensor>currentClass

    @property
    def fw_version(self):
        """
        Returns the firmware version of the sensor if available. Currently only
        I2C/NXT sensors support this.
        """
        return self.get_attr_string('fw_version')

    @property
    def poll_ms(self):
        """
        Returns the polling period of the sensor in milliseconds. Writing sets the
        polling period. Setting to 0 disables polling. Minimum value is hard
        coded as 50 msec. Returns -EOPNOTSUPP if changing polling is not supported.
        Currently only I2C/NXT sensors support changing the polling period.
        """
        return self.get_attr_int('poll_ms')

    @poll_ms.setter
    def poll_ms(self, value):
        self.set_attr_int('poll_ms', value)


# ~autogen
# ~autogen generic-class classes.colorSensor>currentClass

class ColorSensor(Sensor):

    """
    LEGO EV3 color sensor.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-color'], **kwargs)


# ~autogen
# ~autogen generic-property-value classes.colorSensor>currentClass

    # Reflected light. Red LED on.
    MODE_COL_REFLECT = 'COL-REFLECT'

    # Ambient light. Red LEDs off.
    MODE_COL_AMBIENT = 'COL-AMBIENT'

    # Color. All LEDs rapidly cycling, appears white.
    MODE_COL_COLOR = 'COL-COLOR'

    # Raw reflected. Red LED on
    MODE_REF_RAW = 'REF-RAW'

    # Raw Color Components. All LEDs rapidly cycling, appears white.
    MODE_RGB_RAW = 'RGB-RAW'


# ~autogen
# ~autogen generic-class classes.ultrasonicSensor>currentClass

class UltrasonicSensor(Sensor):

    """
    LEGO EV3 ultrasonic sensor.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-us', 'lego-nxt-us'], **kwargs)


# ~autogen
# ~autogen generic-property-value classes.ultrasonicSensor>currentClass

    # Continuous measurement in centimeters.
    # LEDs: On, steady
    MODE_US_DIST_CM = 'US-DIST-CM'

    # Continuous measurement in inches.
    # LEDs: On, steady
    MODE_US_DIST_IN = 'US-DIST-IN'

    # Listen.  LEDs: On, blinking
    MODE_US_LISTEN = 'US-LISTEN'

    # Single measurement in centimeters.
    # LEDs: On momentarily when mode is set, then off
    MODE_US_SI_CM = 'US-SI-CM'

    # Single measurement in inches.
    # LEDs: On momentarily when mode is set, then off
    MODE_US_SI_IN = 'US-SI-IN'


# ~autogen
# ~autogen generic-class classes.gyroSensor>currentClass

class GyroSensor(Sensor):

    """
    LEGO EV3 gyro sensor.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-gyro'], **kwargs)


# ~autogen
# ~autogen generic-property-value classes.gyroSensor>currentClass

    # Angle
    MODE_GYRO_ANG = 'GYRO-ANG'

    # Rotational speed
    MODE_GYRO_RATE = 'GYRO-RATE'

    # Raw sensor value
    MODE_GYRO_FAS = 'GYRO-FAS'

    # Angle and rotational speed
    MODE_GYRO_G_A = 'GYRO-G&A'

    # Calibration ???
    MODE_GYRO_CAL = 'GYRO-CAL'


# ~autogen
# ~autogen generic-class classes.infraredSensor>currentClass

class InfraredSensor(Sensor):

    """
    LEGO EV3 infrared sensor.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-ir'], **kwargs)


# ~autogen
# ~autogen generic-property-value classes.infraredSensor>currentClass

    # Proximity
    MODE_IR_PROX = 'IR-PROX'

    # IR Seeker
    MODE_IR_SEEK = 'IR-SEEK'

    # IR Remote Control
    MODE_IR_REMOTE = 'IR-REMOTE'

    # IR Remote Control. State of the buttons is coded in binary
    MODE_IR_REM_A = 'IR-REM-A'

    # Calibration ???
    MODE_IR_CAL = 'IR-CAL'


# ~autogen
# ~autogen generic-class classes.soundSensor>currentClass

class SoundSensor(Sensor):

    """
    LEGO NXT Sound Sensor
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-nxt-sound'], **kwargs)


# ~autogen
# ~autogen generic-property-value classes.soundSensor>currentClass

    # Sound pressure level. Flat weighting
    MODE_DB = 'DB'

    # Sound pressure level. A weighting
    MODE_DBA = 'DBA'


# ~autogen
# ~autogen generic-class classes.lightSensor>currentClass

class LightSensor(Sensor):

    """
    LEGO NXT Light Sensor
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-nxt-light'], **kwargs)


# ~autogen
# ~autogen generic-property-value classes.lightSensor>currentClass

    # Reflected light. LED on
    MODE_REFLECT = 'REFLECT'

    # Ambient light. LED off
    MODE_AMBIENT = 'AMBIENT'


# ~autogen
# ~autogen generic-class classes.touchSensor>currentClass

class TouchSensor(Sensor):

    """
    Touch Sensor
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-touch', 'lego-nxt-touch'], **kwargs)


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

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)


# ~autogen
# ~autogen generic-get-set classes.led>currentClass

    @property
    def max_brightness(self):
        """
        Returns the maximum allowable brightness value.
        """
        return self.get_attr_int('max_brightness')

    @property
    def brightness(self):
        """
        Sets the brightness level. Possible values are from 0 to `max_brightness`.
        """
        return self.get_attr_int('brightness')

    @brightness.setter
    def brightness(self, value):
        self.set_attr_int('brightness', value)

    @property
    def triggers(self):
        """
        Returns a list of available triggers.
        """
        return self.get_attr_set('trigger')

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
        return self.get_attr_from_set('trigger')

    @trigger.setter
    def trigger(self, value):
        self.set_attr_string('trigger', value)

    @property
    def delay_on(self):
        """
        The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `on` time can
        be specified via `delay_on` attribute in milliseconds.
        """
        return self.get_attr_int('delay_on')

    @delay_on.setter
    def delay_on(self, value):
        self.set_attr_int('delay_on', value)

    @property
    def delay_off(self):
        """
        The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `off` time can
        be specified via `delay_off` attribute in milliseconds.
        """
        return self.get_attr_int('delay_off')

    @delay_off.setter
    def delay_off(self, value):
        self.set_attr_int('delay_off', value)


# ~autogen

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
        self._file_cache = FileCache()
        self._buffer_cache = {}
        for b in self._buttons:
            self._button_file(self._buttons[b]['name'])
            self._button_buffer(self._buttons[b]['name'])

    def _button_file(self, name):
        return self._file_cache.file_handle(name)

    def _button_buffer(self, name):
        if name not in self._buffer_cache:
            self._buffer_cache[name] = array.array('B', [0] * self.KEY_BUF_LEN)
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
            if not bool(buf[int(bit / 8)] & 1 << bit % 8):
                pressed += [k]
        return pressed


# ~autogen remote-control classes.infraredSensor.remoteControl>currentClass
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

    on_red_up = None
    on_red_down = None
    on_blue_up = None
    on_blue_down = None
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


# ~autogen generic-class classes.powerSupply>currentClass

class PowerSupply(Device):

    """
    A generic interface to read data from the system's power_supply class.
    Uses the built-in legoev3-battery if none is specified.
    """

    SYSTEM_CLASS_NAME = 'power_supply'
    SYSTEM_DEVICE_NAME_CONVENTION = '*'

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)


# ~autogen
# ~autogen generic-get-set classes.powerSupply>currentClass

    @property
    def measured_current(self):
        """
        The measured current that the battery is supplying (in microamps)
        """
        return self.get_attr_int('current_now')

    @property
    def measured_voltage(self):
        """
        The measured voltage that the battery is supplying (in microvolts)
        """
        return self.get_attr_int('voltage_now')

    @property
    def max_voltage(self):
        """
        """
        return self.get_attr_int('voltage_max_design')

    @property
    def min_voltage(self):
        """
        """
        return self.get_attr_int('voltage_min_design')

    @property
    def technology(self):
        """
        """
        return self.get_attr_string('technology')

    @property
    def type(self):
        """
        """
        return self.get_attr_string('type')


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
    related to the actual port at all - use the `port_name` attribute to find
    a specific port.
    """

    SYSTEM_CLASS_NAME = 'lego_port'
    SYSTEM_DEVICE_NAME_CONVENTION = '*'

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)


# ~autogen
# ~autogen generic-get-set classes.legoPort>currentClass

    @property
    def driver_name(self):
        """
        Returns the name of the driver that loaded this device. You can find the
        complete list of drivers in the [list of port drivers].
        """
        return self.get_attr_string('driver_name')

    @property
    def modes(self):
        """
        Returns a list of the available modes of the port.
        """
        return self.get_attr_set('modes')

    @property
    def mode(self):
        """
        Reading returns the currently selected mode. Writing sets the mode.
        Generally speaking when the mode changes any sensor or motor devices
        associated with the port will be removed new ones loaded, however this
        this will depend on the individual driver implementing this class.
        """
        return self.get_attr_string('mode')

    @mode.setter
    def mode(self, value):
        self.set_attr_string('mode', value)

    @property
    def port_name(self):
        """
        Returns the name of the port. See individual driver documentation for
        the name that will be returned.
        """
        return self.get_attr_string('port_name')

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
        self.set_attr_string('set_device', value)

    @property
    def status(self):
        """
        In most cases, reading status will return the same value as `mode`. In
        cases where there is an `auto` mode additional values may be returned,
        such as `no-device` or `error`. See individual port driver documentation
        for the full list of possible values.
        """
        return self.get_attr_string('status')


# ~autogen

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
        FbMem.__init__(self)

        self._img = Image.new(
                self.var_info.bits_per_pixel == 1 and "1" or "RGB",
                (self.fix_info.line_length * 8 / self.var_info.bits_per_pixel, self.yres),
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
    """

    @staticmethod
    def beep(args=''):
        """
        Call beep command with the provided arguments (if any).
        See `beep man page`_ and google 'linux beep music' for inspiration.

        .. _`beep man page`: http://manpages.debian.org/cgi-bin/man.cgi?query=beep
        """
        with open(os.devnull, 'w') as n:
            return Popen('/usr/bin/beep %s' % args, stdout=n, shell=True)

    @staticmethod
    def tone(*args):
        """
        tone(tone_sequence):

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

        tone(frequency, duration):

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
            return Popen('/usr/bin/aplay -q "%s"' % wav_file, stdout=n, shell=True)

    @staticmethod
    def speak(text):
        """
        Speak the given text aloud.
        """
        with open(os.devnull, 'w') as n:
            return Popen('/usr/bin/espeak -a 200 --stdout "%s" | /usr/bin/aplay -q' % text, stdout=n, shell=True)
