#------------------------------------------------------------------------------
# Copyright (c) 2015 Ralph Hempel
# Copyright (c) 2015 Anton Vanhoucke
# Copyright (c) 2015 Denis Demidov
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

#~autogen autogen-header
# Sections of the following code were auto-generated based on spec v0.9.3-pre, rev 2

#~autogen

import os.path
import fnmatch
import numbers

#------------------------------------------------------------------------------
# Define the base class from which all other ev3dev classes are defined.

class Device(object):
    """The ev3dev device base class"""

    DEVICE_ROOT_PATH = '/sys/class'

    def __init__(self, class_name, name='*', **kwargs ):
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

        Example:
            d = ev3dev.Device('tacho-motor', port_name='outA')
            s = ev3dev.Device('lego-sensor', driver_name=['lego-ev3-us', 'lego-nxt-us'])

        When connected succesfully, the `connected` attribute is set to True.
        """

        classpath = os.path.abspath( Device.DEVICE_ROOT_PATH + '/' + class_name )
        self.filehandle_cache = {}
        self.connected = False

        for file in os.listdir( classpath ):
            if fnmatch.fnmatch(file, name):
                self._path = os.path.abspath( classpath + '/' + file )

                # See if requested attributes match:
                if all([self._matches(k, kwargs[k]) for k in kwargs]):
                    self.connected = True
                    return

    def _matches(self, attribute, pattern):
        """Test if attribute value matches pattern (that is, if pattern is a
        substring of attribute value).  If pattern is a list, then a match with
        any one entry is enough.
        """
        value = self._get_attribute(attribute)
        return any([value.find(pat) >= 0 for pat in list(pattern)])

    def _attribute_file( self, attribute, mode, reopen=False ):
        """Manages the file handle cache and opening the files in the correct mode"""

        attribute_name = os.path.abspath( self._path + '/' + attribute )

        if attribute_name not in self.filehandle_cache:
            f = open( attribute_name, mode )
            self.filehandle_cache[attribute_name] = f
        elif reopen == True:
            self.filehandle_cache[attribute_name].close()
            f = open( attribute_name, mode )
            self.filehandle_cache[attribute_name] = f
        else:
            f = self.filehandle_cache[attribute_name]
        return f

    def _get_attribute( self, attribute ):
        """Device attribute getter"""
        f = self._attribute_file( attribute, 'r' )
        try:
            f.seek(0)
            value = f.read()
        except IOError:
            f = self._attribute_file( attribute, 'w+', True )
            value = f.read()
        return value.strip()

    def _set_attribute( self, attribute, value ):
        """Device attribute setter"""
        f = self._attribute_file( attribute, 'w' )
        try:
            f.seek(0)
            f.write( value )
            f.flush()
        except IOError:
            f = self._attribute_file( attribute, 'w+', True )
            f.write( value )
            f.flush()

    def get_attr_int( self, attribute ):
        return int( self._get_attribute( attribute ) )

    def set_attr_int( self, attribute, value ):
        self._set_attribute( attribute, '{0:d}'.format( int(value) ) )

    def get_attr_string( self, attribute ):
        return self._get_attribute( attribute )

    def set_attr_string( self, attribute, value ):
        self._set_attribute( attribute, "{0}".format(value) )

    def get_attr_line( self, attribute ):
        return self._get_attribute( attribute )

    def get_attr_set( self, attribute ):
        return [v.strip('[]') for v in self.get_attr_line( attribute ).split()]

    def get_attr_from_set( self, attribute ):
        for a in self.get_attr_line( attribute ).split():
            v = a.strip( '[]' )
            if v != a:
                return v
        return ""

#~autogen python_generic-class classes.motor>currentClass


class Motor(Device):

    """
    The motor class provides a uniform interface for using motors with
    positional and directional feedback such as the EV3 and NXT motors.
    This feedback allows for precise control of the motors. This is the
    most common type of motor, so we just call it `motor`.
    """

    SYSTEM_CLASS_NAME = 'tacho-motor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'motor*'

    def __init__(self, port='', name='*', **kwargs ):
        Device.__init__( self, self.SYSTEM_CLASS_NAME, name, port_name=port, **kwargs )

#~autogen
#~autogen python_generic-get-set classes.motor>currentClass


    def _set_command(self, value):
        self.set_attr_string( 'command', value )

    _doc_command = """
        Sends a command to the motor controller. See `commands` for a list of
        possible values.
        """

    command = property( None, _set_command, None, _doc_command )

    def _get_commands(self):
        return self.get_attr_set( 'commands' )

    _doc_commands = """
        Returns a list of commands that are supported by the motor
        controller. Possible values are `run-forever`, `run-to-abs-pos`, `run-to-rel-pos`,
        `run-timed`, `run-direct`, `stop` and `reset`. Not all commands may be supported.
        `run-forever` will cause the motor to run until another command is sent.
        `run-to-abs-pos` will run to an absolute position specified by `position_sp`
        and then stop using the command specified in `stop_command`.
        `run-to-rel-pos` will run to a position relative to the current `position` value.
        The new position will be current `position` + `position_sp`. When the new
        position is reached, the motor will stop using the command specified by `stop_command`.
        `run-timed` will run the motor for the amount of time specified in `time_sp`
        and then stop the motor using the command specified by `stop_command`.
        `run-direct` will run the motor at the duty cycle specified by `duty_cycle_sp`.
        Unlike other run commands, changing `duty_cycle_sp` while running *will*
        take effect immediately.
        `stop` will stop any of the run commands before they are complete using the
        command specified by `stop_command`.
        `reset` will reset all of the motor parameter attributes to their default value.
        This will also have the effect of stopping the motor.
        """

    commands = property( _get_commands, None, None, _doc_commands )

    def _get_count_per_rot(self):
        return self.get_attr_int( 'count_per_rot' )

    _doc_count_per_rot = """
        Returns the number of tacho counts in one rotation of the motor. Tacho counts
        are used by the position and speed attributes, so you can use this value
        to convert rotations or degrees to tacho counts. In the case of linear
        actuators, the units here will be counts per centimeter.
        """

    count_per_rot = property( _get_count_per_rot, None, None, _doc_count_per_rot )

    def _get_driver_name(self):
        return self.get_attr_string( 'driver_name' )

    _doc_driver_name = """
        Returns the name of the driver that provides this tacho motor device.
        """

    driver_name = property( _get_driver_name, None, None, _doc_driver_name )

    def _get_duty_cycle(self):
        return self.get_attr_int( 'duty_cycle' )

    _doc_duty_cycle = """
        Returns the current duty cycle of the motor. Units are percent. Values
        are -100 to 100.
        """

    duty_cycle = property( _get_duty_cycle, None, None, _doc_duty_cycle )

    def _get_duty_cycle_sp(self):
        return self.get_attr_int( 'duty_cycle_sp' )

    def _set_duty_cycle_sp(self, value):
        self.set_attr_int( 'duty_cycle_sp', value )

    _doc_duty_cycle_sp = """
        Writing sets the duty cycle setpoint. Reading returns the current value.
        Units are in percent. Valid values are -100 to 100. A negative value causes
        the motor to rotate in reverse. This value is only used when `speed_regulation`
        is off.
        """

    duty_cycle_sp = property( _get_duty_cycle_sp, _set_duty_cycle_sp, None, _doc_duty_cycle_sp )

    def _get_encoder_polarity(self):
        return self.get_attr_string( 'encoder_polarity' )

    def _set_encoder_polarity(self, value):
        self.set_attr_string( 'encoder_polarity', value )

    _doc_encoder_polarity = """
        Sets the polarity of the rotary encoder. This is an advanced feature to all
        use of motors that send inversed encoder signals to the EV3. This should
        be set correctly by the driver of a device. It You only need to change this
        value if you are using a unsupported device. Valid values are `normal` and
        `inversed`.
        """

    encoder_polarity = property( _get_encoder_polarity, _set_encoder_polarity, None, _doc_encoder_polarity )

    def _get_polarity(self):
        return self.get_attr_string( 'polarity' )

    def _set_polarity(self, value):
        self.set_attr_string( 'polarity', value )

    _doc_polarity = """
        Sets the polarity of the motor. With `normal` polarity, a positive duty
        cycle will cause the motor to rotate clockwise. With `inversed` polarity,
        a positive duty cycle will cause the motor to rotate counter-clockwise.
        Valid values are `normal` and `inversed`.
        """

    polarity = property( _get_polarity, _set_polarity, None, _doc_polarity )

    def _get_port_name(self):
        return self.get_attr_string( 'port_name' )

    _doc_port_name = """
        Returns the name of the port that the motor is connected to.
        """

    port_name = property( _get_port_name, None, None, _doc_port_name )

    def _get_position(self):
        return self.get_attr_int( 'position' )

    def _set_position(self, value):
        self.set_attr_int( 'position', value )

    _doc_position = """
        Returns the current position of the motor in pulses of the rotary
        encoder. When the motor rotates clockwise, the position will increase.
        Likewise, rotating counter-clockwise causes the position to decrease.
        Writing will set the position to that value.
        """

    position = property( _get_position, _set_position, None, _doc_position )

    def _get_position_p(self):
        return self.get_attr_int( 'hold_pid/Kp' )

    def _set_position_p(self, value):
        self.set_attr_int( 'hold_pid/Kp', value )

    _doc_position_p = """
        The proportional constant for the position PID.
        """

    position_p = property( _get_position_p, _set_position_p, None, _doc_position_p )

    def _get_position_i(self):
        return self.get_attr_int( 'hold_pid/Ki' )

    def _set_position_i(self, value):
        self.set_attr_int( 'hold_pid/Ki', value )

    _doc_position_i = """
        The integral constant for the position PID.
        """

    position_i = property( _get_position_i, _set_position_i, None, _doc_position_i )

    def _get_position_d(self):
        return self.get_attr_int( 'hold_pid/Kd' )

    def _set_position_d(self, value):
        self.set_attr_int( 'hold_pid/Kd', value )

    _doc_position_d = """
        The derivative constant for the position PID.
        """

    position_d = property( _get_position_d, _set_position_d, None, _doc_position_d )

    def _get_position_sp(self):
        return self.get_attr_int( 'position_sp' )

    def _set_position_sp(self, value):
        self.set_attr_int( 'position_sp', value )

    _doc_position_sp = """
        Writing specifies the target position for the `run-to-abs-pos` and `run-to-rel-pos`
        commands. Reading returns the current value. Units are in tacho counts. You
        can use the value returned by `counts_per_rot` to convert tacho counts to/from
        rotations or degrees.
        """

    position_sp = property( _get_position_sp, _set_position_sp, None, _doc_position_sp )

    def _get_speed(self):
        return self.get_attr_int( 'speed' )

    _doc_speed = """
        Returns the current motor speed in tacho counts per second. Not, this is
        not necessarily degrees (although it is for LEGO motors). Use the `count_per_rot`
        attribute to convert this value to RPM or deg/sec.
        """

    speed = property( _get_speed, None, None, _doc_speed )

    def _get_speed_sp(self):
        return self.get_attr_int( 'speed_sp' )

    def _set_speed_sp(self, value):
        self.set_attr_int( 'speed_sp', value )

    _doc_speed_sp = """
        Writing sets the target speed in tacho counts per second used when `speed_regulation`
        is on. Reading returns the current value.  Use the `count_per_rot` attribute
        to convert RPM or deg/sec to tacho counts per second.
        """

    speed_sp = property( _get_speed_sp, _set_speed_sp, None, _doc_speed_sp )

    def _get_ramp_up_sp(self):
        return self.get_attr_int( 'ramp_up_sp' )

    def _set_ramp_up_sp(self, value):
        self.set_attr_int( 'ramp_up_sp', value )

    _doc_ramp_up_sp = """
        Writing sets the ramp up setpoint. Reading returns the current value. Units
        are in milliseconds. When set to a value > 0, the motor will ramp the power
        sent to the motor from 0 to 100% duty cycle over the span of this setpoint
        when starting the motor. If the maximum duty cycle is limited by `duty_cycle_sp`
        or speed regulation, the actual ramp time duration will be less than the setpoint.
        """

    ramp_up_sp = property( _get_ramp_up_sp, _set_ramp_up_sp, None, _doc_ramp_up_sp )

    def _get_ramp_down_sp(self):
        return self.get_attr_int( 'ramp_down_sp' )

    def _set_ramp_down_sp(self, value):
        self.set_attr_int( 'ramp_down_sp', value )

    _doc_ramp_down_sp = """
        Writing sets the ramp down setpoint. Reading returns the current value. Units
        are in milliseconds. When set to a value > 0, the motor will ramp the power
        sent to the motor from 100% duty cycle down to 0 over the span of this setpoint
        when stopping the motor. If the starting duty cycle is less than 100%, the
        ramp time duration will be less than the full span of the setpoint.
        """

    ramp_down_sp = property( _get_ramp_down_sp, _set_ramp_down_sp, None, _doc_ramp_down_sp )

    def _get_speed_regulation_enabled(self):
        return self.get_attr_string( 'speed_regulation' )

    def _set_speed_regulation_enabled(self, value):
        self.set_attr_string( 'speed_regulation', value )

    _doc_speed_regulation_enabled = """
        Turns speed regulation on or off. If speed regulation is on, the motor
        controller will vary the power supplied to the motor to try to maintain the
        speed specified in `speed_sp`. If speed regulation is off, the controller
        will use the power specified in `duty_cycle_sp`. Valid values are `on` and
        `off`.
        """

    speed_regulation_enabled = property( _get_speed_regulation_enabled, _set_speed_regulation_enabled, None, _doc_speed_regulation_enabled )

    def _get_speed_regulation_p(self):
        return self.get_attr_int( 'speed_pid/Kp' )

    def _set_speed_regulation_p(self, value):
        self.set_attr_int( 'speed_pid/Kp', value )

    _doc_speed_regulation_p = """
        The proportional constant for the speed regulation PID.
        """

    speed_regulation_p = property( _get_speed_regulation_p, _set_speed_regulation_p, None, _doc_speed_regulation_p )

    def _get_speed_regulation_i(self):
        return self.get_attr_int( 'speed_pid/Ki' )

    def _set_speed_regulation_i(self, value):
        self.set_attr_int( 'speed_pid/Ki', value )

    _doc_speed_regulation_i = """
        The integral constant for the speed regulation PID.
        """

    speed_regulation_i = property( _get_speed_regulation_i, _set_speed_regulation_i, None, _doc_speed_regulation_i )

    def _get_speed_regulation_d(self):
        return self.get_attr_int( 'speed_pid/Kd' )

    def _set_speed_regulation_d(self, value):
        self.set_attr_int( 'speed_pid/Kd', value )

    _doc_speed_regulation_d = """
        The derivative constant for the speed regulation PID.
        """

    speed_regulation_d = property( _get_speed_regulation_d, _set_speed_regulation_d, None, _doc_speed_regulation_d )

    def _get_state(self):
        return self.get_attr_set( 'state' )

    _doc_state = """
        Reading returns a list of state flags. Possible flags are
        `running`, `ramping` `holding` and `stalled`.
        """

    state = property( _get_state, None, None, _doc_state )

    def _get_stop_command(self):
        return self.get_attr_string( 'stop_command' )

    def _set_stop_command(self, value):
        self.set_attr_string( 'stop_command', value )

    _doc_stop_command = """
        Reading returns the current stop command. Writing sets the stop command.
        The value determines the motors behavior when `command` is set to `stop`.
        Also, it determines the motors behavior when a run command completes. See
        `stop_commands` for a list of possible values.
        """

    stop_command = property( _get_stop_command, _set_stop_command, None, _doc_stop_command )

    def _get_stop_commands(self):
        return self.get_attr_set( 'stop_commands' )

    _doc_stop_commands = """
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

    stop_commands = property( _get_stop_commands, None, None, _doc_stop_commands )

    def _get_time_sp(self):
        return self.get_attr_int( 'time_sp' )

    def _set_time_sp(self, value):
        self.set_attr_int( 'time_sp', value )

    _doc_time_sp = """
        Writing specifies the amount of time the motor will run when using the
        `run-timed` command. Reading returns the current value. Units are in
        milliseconds.
        """

    time_sp = property( _get_time_sp, _set_time_sp, None, _doc_time_sp )


#~autogen
#~autogen python_generic-property-value classes.motor>currentClass


    _propval_command = {
      'run-forever':'Run the motor until another command is sent.' ,
      'run-to-abs-pos':'Run to an absolute position specified by `position_sp` and thenstop using the command specified in `stop_command`.' ,
      'run-to-rel-pos':'Run to a position relative to the current `position` value.The new position will be current `position` + `position_sp`.When the new position is reached, the motor will stop usingthe command specified by `stop_command`.' ,
      'run-timed':'Run the motor for the amount of time specified in `time_sp`and then stop the motor using the command specified by `stop_command`.' ,
      'run-direct':'Run the motor at the duty cycle specified by `duty_cycle_sp`.Unlike other run commands, changing `duty_cycle_sp` while running *will*take effect immediately.' ,
      'stop':'Stop any of the run commands before they are complete using thecommand specified by `stop_command`.' ,
      'reset':'Reset all of the motor parameter attributes to their default value.This will also have the effect of stopping the motor.' ,
      }

    _propval_encoder_polarity = {
      'normal':'Sets the normal polarity of the rotary encoder.' ,
      'inversed':'Sets the inversed polarity of the rotary encoder.' ,
      }

    _propval_polarity = {
      'normal':'With `normal` polarity, a positive duty cycle willcause the motor to rotate clockwise.' ,
      'inversed':'With `inversed` polarity, a positive duty cycle willcause the motor to rotate counter-clockwise.' ,
      }

    _propval_speed_regulation = {
      'on':'The motor controller will vary the power supplied to the motorto try to maintain the speed specified in `speed_sp`.' ,
      'off':'The motor controller will use the power specified in `duty_cycle_sp`.' ,
      }

    _propval_stop_command = {
      'coast':'Power will be removed from the motor and it will freely coast to a stop.' ,
      'brake':'Power will be removed from the motor and a passive electrical load willbe placed on the motor. This is usually done by shorting the motor terminalstogether. This load will absorb the energy from the rotation of the motors andcause the motor to stop more quickly than coasting.' ,
      'hold':'Does not remove power from the motor. Instead it actively try to hold the motorat the current position. If an external force tries to turn the motor, the motorwill ``push back`` to maintain its position.' ,
      }

#~autogen
#~autogen python_motor_commands classes.motor>currentClass

    def run_forever( self, **kwargs ):
        """Run the motor until another command is sent.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-forever'

    def run_to_abs_pos( self, **kwargs ):
        """Run to an absolute position specified by `position_sp` and then
        stop using the command specified in `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-to-abs-pos'

    def run_to_rel_pos( self, **kwargs ):
        """Run to a position relative to the current `position` value.
        The new position will be current `position` + `position_sp`.
        When the new position is reached, the motor will stop using
        the command specified by `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-to-rel-pos'

    def run_timed( self, **kwargs ):
        """Run the motor for the amount of time specified in `time_sp`
        and then stop the motor using the command specified by `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-timed'

    def run_direct( self, **kwargs ):
        """Run the motor at the duty cycle specified by `duty_cycle_sp`.
        Unlike other run commands, changing `duty_cycle_sp` while running *will*
        take effect immediately.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-direct'

    def stop( self, **kwargs ):
        """Stop any of the run commands before they are complete using the
        command specified by `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'stop'

    def reset( self, **kwargs ):
        """Reset all of the motor parameter attributes to their default value.
        This will also have the effect of stopping the motor.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'reset'


#~autogen
#~autogen python_generic-class classes.dcMotor>currentClass


class DcMotor(Device):

    """
    The DC motor class provides a uniform interface for using regular DC motors
    with no fancy controls or feedback. This includes LEGO MINDSTORMS RCX motors
    and LEGO Power Functions motors.
    """

    SYSTEM_CLASS_NAME = 'dc-motor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'motor*'

    def __init__(self, port='', name='*', **kwargs ):
        Device.__init__( self, self.SYSTEM_CLASS_NAME, name, port_name=port, **kwargs )

#~autogen
#~autogen python_generic-get-set classes.dcMotor>currentClass


    def _set_command(self, value):
        self.set_attr_string( 'command', value )

    _doc_command = """
        Sets the command for the motor. Possible values are `run-forever`, `run-timed` and
        `stop`. Not all commands may be supported, so be sure to check the contents
        of the `commands` attribute.
        """

    command = property( None, _set_command, None, _doc_command )

    def _get_commands(self):
        return self.get_attr_set( 'commands' )

    _doc_commands = """
        Returns a list of commands supported by the motor
        controller.
        """

    commands = property( _get_commands, None, None, _doc_commands )

    def _get_driver_name(self):
        return self.get_attr_string( 'driver_name' )

    _doc_driver_name = """
        Returns the name of the motor driver that loaded this device. See the list
        of [supported devices] for a list of drivers.
        """

    driver_name = property( _get_driver_name, None, None, _doc_driver_name )

    def _get_duty_cycle(self):
        return self.get_attr_int( 'duty_cycle' )

    _doc_duty_cycle = """
        Shows the current duty cycle of the PWM signal sent to the motor. Values
        are -100 to 100 (-100% to 100%).
        """

    duty_cycle = property( _get_duty_cycle, None, None, _doc_duty_cycle )

    def _get_duty_cycle_sp(self):
        return self.get_attr_int( 'duty_cycle_sp' )

    def _set_duty_cycle_sp(self, value):
        self.set_attr_int( 'duty_cycle_sp', value )

    _doc_duty_cycle_sp = """
        Writing sets the duty cycle setpoint of the PWM signal sent to the motor.
        Valid values are -100 to 100 (-100% to 100%). Reading returns the current
        setpoint.
        """

    duty_cycle_sp = property( _get_duty_cycle_sp, _set_duty_cycle_sp, None, _doc_duty_cycle_sp )

    def _get_polarity(self):
        return self.get_attr_string( 'polarity' )

    def _set_polarity(self, value):
        self.set_attr_string( 'polarity', value )

    _doc_polarity = """
        Sets the polarity of the motor. Valid values are `normal` and `inversed`.
        """

    polarity = property( _get_polarity, _set_polarity, None, _doc_polarity )

    def _get_port_name(self):
        return self.get_attr_string( 'port_name' )

    _doc_port_name = """
        Returns the name of the port that the motor is connected to.
        """

    port_name = property( _get_port_name, None, None, _doc_port_name )

    def _get_ramp_down_sp(self):
        return self.get_attr_int( 'ramp_down_sp' )

    def _set_ramp_down_sp(self, value):
        self.set_attr_int( 'ramp_down_sp', value )

    _doc_ramp_down_sp = """
        Sets the time in milliseconds that it take the motor to ramp down from 100%
        to 0%. Valid values are 0 to 10000 (10 seconds). Default is 0.
        """

    ramp_down_sp = property( _get_ramp_down_sp, _set_ramp_down_sp, None, _doc_ramp_down_sp )

    def _get_ramp_up_sp(self):
        return self.get_attr_int( 'ramp_up_sp' )

    def _set_ramp_up_sp(self, value):
        self.set_attr_int( 'ramp_up_sp', value )

    _doc_ramp_up_sp = """
        Sets the time in milliseconds that it take the motor to up ramp from 0% to
        100%. Valid values are 0 to 10000 (10 seconds). Default is 0.
        """

    ramp_up_sp = property( _get_ramp_up_sp, _set_ramp_up_sp, None, _doc_ramp_up_sp )

    def _get_state(self):
        return self.get_attr_set( 'state' )

    _doc_state = """
        Gets a list of flags indicating the motor status. Possible
        flags are `running` and `ramping`. `running` indicates that the motor is
        powered. `ramping` indicates that the motor has not yet reached the
        `duty_cycle_sp`.
        """

    state = property( _get_state, None, None, _doc_state )

    def _set_stop_command(self, value):
        self.set_attr_string( 'stop_command', value )

    _doc_stop_command = """
        Sets the stop command that will be used when the motor stops. Read
        `stop_commands` to get the list of valid values.
        """

    stop_command = property( None, _set_stop_command, None, _doc_stop_command )

    def _get_stop_commands(self):
        return self.get_attr_set( 'stop_commands' )

    _doc_stop_commands = """
        Gets a list of stop commands. Valid values are `coast`
        and `brake`.
        """

    stop_commands = property( _get_stop_commands, None, None, _doc_stop_commands )

    def _get_time_sp(self):
        return self.get_attr_int( 'time_sp' )

    def _set_time_sp(self, value):
        self.set_attr_int( 'time_sp', value )

    _doc_time_sp = """
        Writing specifies the amount of time the motor will run when using the
        `run-timed` command. Reading returns the current value. Units are in
        milliseconds.
        """

    time_sp = property( _get_time_sp, _set_time_sp, None, _doc_time_sp )


#~autogen
#~autogen python_generic-property-value classes.dcMotor>currentClass


    _propval_command = {
      'run-forever':'Run the motor until another command is sent.' ,
      'run-timed':'Run the motor for the amount of time specified in `time_sp`and then stop the motor using the command specified by `stop_command`.' ,
      'run-direct':'Run the motor at the duty cycle specified by `duty_cycle_sp`.Unlike other run commands, changing `duty_cycle_sp` while running *will*take effect immediately.' ,
      'stop':'Stop any of the run commands before they are complete using thecommand specified by `stop_command`.' ,
      }

    _propval_polarity = {
      'normal':'With `normal` polarity, a positive duty cycle willcause the motor to rotate clockwise.' ,
      'inversed':'With `inversed` polarity, a positive duty cycle willcause the motor to rotate counter-clockwise.' ,
      }

    _propval_stop_command = {
      'coast':'Power will be removed from the motor and it will freely coast to a stop.' ,
      'brake':'Power will be removed from the motor and a passive electrical load willbe placed on the motor. This is usually done by shorting the motor terminalstogether. This load will absorb the energy from the rotation of the motors andcause the motor to stop more quickly than coasting.' ,
      }

#~autogen

#~autogen python_motor_commands classes.dcMotor>currentClass

    def run_forever( self, **kwargs ):
        """Run the motor until another command is sent.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-forever'

    def run_timed( self, **kwargs ):
        """Run the motor for the amount of time specified in `time_sp`
        and then stop the motor using the command specified by `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-timed'

    def run_direct( self, **kwargs ):
        """Run the motor at the duty cycle specified by `duty_cycle_sp`.
        Unlike other run commands, changing `duty_cycle_sp` while running *will*
        take effect immediately.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-direct'

    def stop( self, **kwargs ):
        """Stop any of the run commands before they are complete using the
        command specified by `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'stop'


#~autogen

#~autogen python_generic-class classes.servoMotor>currentClass


class ServoMotor(Device):

    """
    The servo motor class provides a uniform interface for using hobby type
    servo motors.
    """

    SYSTEM_CLASS_NAME = 'servo-motor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'motor*'

    def __init__(self, port='', name='*', **kwargs ):
        Device.__init__( self, self.SYSTEM_CLASS_NAME, name, port_name=port, **kwargs )

#~autogen
#~autogen python_generic-get-set classes.servoMotor>currentClass


    def _set_command(self, value):
        self.set_attr_string( 'command', value )

    _doc_command = """
        Sets the command for the servo. Valid values are `run` and `float`. Setting
        to `run` will cause the servo to be driven to the position_sp set in the
        `position_sp` attribute. Setting to `float` will remove power from the motor.
        """

    command = property( None, _set_command, None, _doc_command )

    def _get_driver_name(self):
        return self.get_attr_string( 'driver_name' )

    _doc_driver_name = """
        Returns the name of the motor driver that loaded this device. See the list
        of [supported devices] for a list of drivers.
        """

    driver_name = property( _get_driver_name, None, None, _doc_driver_name )

    def _get_max_pulse_sp(self):
        return self.get_attr_int( 'max_pulse_sp' )

    def _set_max_pulse_sp(self, value):
        self.set_attr_int( 'max_pulse_sp', value )

    _doc_max_pulse_sp = """
        Used to set the pulse size in milliseconds for the signal that tells the
        servo to drive to the maximum (clockwise) position_sp. Default value is 2400.
        Valid values are 2300 to 2700. You must write to the position_sp attribute for
        changes to this attribute to take effect.
        """

    max_pulse_sp = property( _get_max_pulse_sp, _set_max_pulse_sp, None, _doc_max_pulse_sp )

    def _get_mid_pulse_sp(self):
        return self.get_attr_int( 'mid_pulse_sp' )

    def _set_mid_pulse_sp(self, value):
        self.set_attr_int( 'mid_pulse_sp', value )

    _doc_mid_pulse_sp = """
        Used to set the pulse size in milliseconds for the signal that tells the
        servo to drive to the mid position_sp. Default value is 1500. Valid
        values are 1300 to 1700. For example, on a 180 degree servo, this would be
        90 degrees. On continuous rotation servo, this is the 'neutral' position_sp
        where the motor does not turn. You must write to the position_sp attribute for
        changes to this attribute to take effect.
        """

    mid_pulse_sp = property( _get_mid_pulse_sp, _set_mid_pulse_sp, None, _doc_mid_pulse_sp )

    def _get_min_pulse_sp(self):
        return self.get_attr_int( 'min_pulse_sp' )

    def _set_min_pulse_sp(self, value):
        self.set_attr_int( 'min_pulse_sp', value )

    _doc_min_pulse_sp = """
        Used to set the pulse size in milliseconds for the signal that tells the
        servo to drive to the miniumum (counter-clockwise) position_sp. Default value
        is 600. Valid values are 300 to 700. You must write to the position_sp
        attribute for changes to this attribute to take effect.
        """

    min_pulse_sp = property( _get_min_pulse_sp, _set_min_pulse_sp, None, _doc_min_pulse_sp )

    def _get_polarity(self):
        return self.get_attr_string( 'polarity' )

    def _set_polarity(self, value):
        self.set_attr_string( 'polarity', value )

    _doc_polarity = """
        Sets the polarity of the servo. Valid values are `normal` and `inversed`.
        Setting the value to `inversed` will cause the position_sp value to be
        inversed. i.e `-100` will correspond to `max_pulse_sp`, and `100` will
        correspond to `min_pulse_sp`.
        """

    polarity = property( _get_polarity, _set_polarity, None, _doc_polarity )

    def _get_port_name(self):
        return self.get_attr_string( 'port_name' )

    _doc_port_name = """
        Returns the name of the port that the motor is connected to.
        """

    port_name = property( _get_port_name, None, None, _doc_port_name )

    def _get_position_sp(self):
        return self.get_attr_int( 'position_sp' )

    def _set_position_sp(self, value):
        self.set_attr_int( 'position_sp', value )

    _doc_position_sp = """
        Reading returns the current position_sp of the servo. Writing instructs the
        servo to move to the specified position_sp. Units are percent. Valid values
        are -100 to 100 (-100% to 100%) where `-100` corresponds to `min_pulse_sp`,
        `0` corresponds to `mid_pulse_sp` and `100` corresponds to `max_pulse_sp`.
        """

    position_sp = property( _get_position_sp, _set_position_sp, None, _doc_position_sp )

    def _get_rate_sp(self):
        return self.get_attr_int( 'rate_sp' )

    def _set_rate_sp(self, value):
        self.set_attr_int( 'rate_sp', value )

    _doc_rate_sp = """
        Sets the rate_sp at which the servo travels from 0 to 100.0% (half of the full
        range of the servo). Units are in milliseconds. Example: Setting the rate_sp
        to 1000 means that it will take a 180 degree servo 2 second to move from 0
        to 180 degrees. Note: Some servo controllers may not support this in which
        case reading and writing will fail with `-EOPNOTSUPP`. In continuous rotation
        servos, this value will affect the rate_sp at which the speed ramps up or down.
        """

    rate_sp = property( _get_rate_sp, _set_rate_sp, None, _doc_rate_sp )

    def _get_state(self):
        return self.get_attr_set( 'state' )

    _doc_state = """
        Returns a list of flags indicating the state of the servo.
        Possible values are:
        * `running`: Indicates that the motor is powered.
        """

    state = property( _get_state, None, None, _doc_state )


#~autogen
#~autogen python_generic-property-value classes.servoMotor>currentClass


    _propval_command = {
      'run':'Drive servo to the position set in the `position_sp` attribute.' ,
      'float':'Remove power from the motor.' ,
      }

    _propval_polarity = {
      'normal':'With `normal` polarity, a positive duty cycle willcause the motor to rotate clockwise.' ,
      'inversed':'With `inversed` polarity, a positive duty cycle willcause the motor to rotate counter-clockwise.' ,
      }

#~autogen

#~autogen python_motor_commands classes.servoMotor>currentClass

    def run( self, **kwargs ):
        """Drive servo to the position set in the `position_sp` attribute.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run'

    def float( self, **kwargs ):
        """Remove power from the motor.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'float'


#~autogen

#~autogen python_generic-class classes.sensor>currentClass


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

    def __init__(self, port='', name='*', **kwargs ):
        Device.__init__( self, self.SYSTEM_CLASS_NAME, name, port_name=port, **kwargs )

#~autogen
#~autogen python_generic-get-set classes.sensor>currentClass


    def _set_command(self, value):
        self.set_attr_string( 'command', value )

    _doc_command = """
        Sends a command to the sensor.
        """

    command = property( None, _set_command, None, _doc_command )

    def _get_commands(self):
        return self.get_attr_set( 'commands' )

    _doc_commands = """
        Returns a list of the valid commands for the sensor.
        Returns -EOPNOTSUPP if no commands are supported.
        """

    commands = property( _get_commands, None, None, _doc_commands )

    def _get_decimals(self):
        return self.get_attr_int( 'decimals' )

    _doc_decimals = """
        Returns the number of decimal places for the values in the `value<N>`
        attributes of the current mode.
        """

    decimals = property( _get_decimals, None, None, _doc_decimals )

    def _get_driver_name(self):
        return self.get_attr_string( 'driver_name' )

    _doc_driver_name = """
        Returns the name of the sensor device/driver. See the list of [supported
        sensors] for a complete list of drivers.
        """

    driver_name = property( _get_driver_name, None, None, _doc_driver_name )

    def _get_mode(self):
        return self.get_attr_string( 'mode' )

    def _set_mode(self, value):
        self.set_attr_string( 'mode', value )

    _doc_mode = """
        Returns the current mode. Writing one of the values returned by `modes`
        sets the sensor to that mode.
        """

    mode = property( _get_mode, _set_mode, None, _doc_mode )

    def _get_modes(self):
        return self.get_attr_set( 'modes' )

    _doc_modes = """
        Returns a list of the valid modes for the sensor.
        """

    modes = property( _get_modes, None, None, _doc_modes )

    def _get_num_values(self):
        return self.get_attr_int( 'num_values' )

    _doc_num_values = """
        Returns the number of `value<N>` attributes that will return a valid value
        for the current mode.
        """

    num_values = property( _get_num_values, None, None, _doc_num_values )

    def _get_port_name(self):
        return self.get_attr_string( 'port_name' )

    _doc_port_name = """
        Returns the name of the port that the sensor is connected to, e.g. `ev3:in1`.
        I2C sensors also include the I2C address (decimal), e.g. `ev3:in1:i2c8`.
        """

    port_name = property( _get_port_name, None, None, _doc_port_name )

    def _get_units(self):
        return self.get_attr_string( 'units' )

    _doc_units = """
        Returns the units of the measured value for the current mode. May return
        empty string
        """

    units = property( _get_units, None, None, _doc_units )


#~autogen

    def value(self, n):
        if True == isinstance( n, numbers.Integral ):
            n = '{0:d}'.format( n )
        elif True == isinstance( n, numbers.Real ):
            n = '{0:.0f}'.format( n )

        if True == isinstance( n, str ):
            return self._device._get_int_attribute( 'value'+n, 'value'+n )
        else:
            return 0

#~autogen python_generic-class classes.i2cSensor>currentClass


class I2cSensor(Device):

    """
    A generic interface to control I2C-type EV3 sensors.
    """

    SYSTEM_CLASS_NAME = 'lego-sensor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'sensor*'

    def __init__(self, port='', name='*', **kwargs ):
        Device.__init__( self, self.SYSTEM_CLASS_NAME, name, port_name=port, **kwargs )

#~autogen
#~autogen python_generic-get-set classes.i2cSensor>currentClass


    def _get_fw_version(self):
        return self.get_attr_string( 'fw_version' )

    _doc_fw_version = """
        Returns the firmware version of the sensor if available. Currently only
        I2C/NXT sensors support this.
        """

    fw_version = property( _get_fw_version, None, None, _doc_fw_version )

    def _get_poll_ms(self):
        return self.get_attr_int( 'poll_ms' )

    def _set_poll_ms(self, value):
        self.set_attr_int( 'poll_ms', value )

    _doc_poll_ms = """
        Returns the polling period of the sensor in milliseconds. Writing sets the
        polling period. Setting to 0 disables polling. Minimum value is hard
        coded as 50 msec. Returns -EOPNOTSUPP if changing polling is not supported.
        Currently only I2C/NXT sensors support changing the polling period.
        """

    poll_ms = property( _get_poll_ms, _set_poll_ms, None, _doc_poll_ms )


#~autogen
#~autogen python_generic-class classes.colorSensor>currentClass


class ColorSensor(Device):

    """
    LEGO EV3 color sensor.
    """

    SYSTEM_CLASS_NAME = 'lego-sensor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'sensor*'

    def __init__(self, port='', name='*', **kwargs ):
        Device.__init__( self, self.SYSTEM_CLASS_NAME, name, port_name=port, **kwargs )

#~autogen
#~autogen python_generic-property-value classes.colorSensor>currentClass


    _propval_mode = {
      'COL-REFLECT':'Reflected light. Red LED on.' ,
      'COL-AMBIENT':'Ambient light. Red LEDs off.' ,
      'COL-COLOR':'Color. All LEDs rapidly cycling, appears white.' ,
      'REF-RAW':'Raw reflected. Red LED on' ,
      'RGB-RAW':'Raw Color Components. All LEDs rapidly cycling, appears white.' ,
      }

#~autogen
#~autogen python_generic-class classes.ultrasonicSensor>currentClass


class UltrasonicSensor(Device):

    """
    LEGO EV3 ultrasonic sensor.
    """

    SYSTEM_CLASS_NAME = 'lego-sensor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'sensor*'

    def __init__(self, port='', name='*', **kwargs ):
        Device.__init__( self, self.SYSTEM_CLASS_NAME, name, port_name=port, **kwargs )

#~autogen
#~autogen python_generic-property-value classes.ultrasonicSensor>currentClass


    _propval_mode = {
      'US-DIST-CM':'Continuous measurement in centimeters.LEDs: On, steady' ,
      'US-DIST-IN':'Continuous measurement in inches.LEDs: On, steady' ,
      'US-LISTEN':'Listen.  LEDs: On, blinking' ,
      'US-SI-CM':'Single measurement in centimeters.LEDs: On momentarily when mode is set, then off' ,
      'US-SI-IN':'Single measurement in inches.LEDs: On momentarily when mode is set, then off' ,
      }

#~autogen
#~autogen python_generic-class classes.gyroSensor>currentClass


class GyroSensor(Device):

    """
    LEGO EV3 gyro sensor.
    """

    SYSTEM_CLASS_NAME = 'lego-sensor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'sensor*'

    def __init__(self, port='', name='*', **kwargs ):
        Device.__init__( self, self.SYSTEM_CLASS_NAME, name, port_name=port, **kwargs )

#~autogen
#~autogen python_generic-property-value classes.gyroSensor>currentClass


    _propval_mode = {
      'GYRO-ANG':'Angle' ,
      'GYRO-RATE':'Rotational speed' ,
      'GYRO-FAS':'Raw sensor value' ,
      'GYRO-G&A':'Angle and rotational speed' ,
      'GYRO-CAL':'Calibration ???' ,
      }

#~autogen
#~autogen python_generic-class classes.infraredSensor>currentClass


class InfraredSensor(Device):

    """
    LEGO EV3 infrared sensor.
    """

    SYSTEM_CLASS_NAME = 'lego-sensor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'sensor*'

    def __init__(self, port='', name='*', **kwargs ):
        Device.__init__( self, self.SYSTEM_CLASS_NAME, name, port_name=port, **kwargs )

#~autogen
#~autogen python_generic-property-value classes.infraredSensor>currentClass


    _propval_mode = {
      'IR-PROX':'Proximity' ,
      'IR-SEEK':'IR Seeker' ,
      'IR-REMOTE':'IR Remote Control' ,
      'IR-REM-A':'IR Remote Control. State of the buttons is coded in binary' ,
      'IR-CAL':'Calibration ???' ,
      }

#~autogen


#~autogen python_generic-class classes.soundSensor>currentClass


class SoundSensor(Device):

    """
    LEGO NXT Sound Sensor
    """

    SYSTEM_CLASS_NAME = 'lego-nxt-sound'
    SYSTEM_DEVICE_NAME_CONVENTION = 'sensor*'

    def __init__(self, port='', name='*', **kwargs ):
        Device.__init__( self, self.SYSTEM_CLASS_NAME, name, port_name=port, **kwargs )

#~autogen
#~autogen python_generic-property-value classes.soundSensor>currentClass


    _propval_mode = {
      'DB':'Sound pressure level. Flat weighting' ,
      'DBA':'Sound pressure level. A weighting' ,
      }

#~autogen
#~autogen python_generic-class classes.lightSensor>currentClass


class LightSensor(Device):

    """
    LEGO NXT Light Sensor
    """

    SYSTEM_CLASS_NAME = 'lego-nxt-light'
    SYSTEM_DEVICE_NAME_CONVENTION = 'sensor*'

    def __init__(self, port='', name='*', **kwargs ):
        Device.__init__( self, self.SYSTEM_CLASS_NAME, name, port_name=port, **kwargs )

#~autogen
#~autogen python_generic-property-value classes.lightSensor>currentClass


    _propval_mode = {
      'REFLECT':'Reflected light. LED on' ,
      'AMBIENT':'Ambient light. LED off' ,
      }

#~autogen
#~autogen python_generic-class classes.led>currentClass


class Led(Device):

    """
    Any device controlled by the generic LED driver.
    See https://www.kernel.org/doc/Documentation/leds/leds-class.txt
    for more details.
    """

    SYSTEM_CLASS_NAME = 'leds'
    SYSTEM_DEVICE_NAME_CONVENTION = ''

    def __init__(self, port='', name='*', **kwargs ):
        Device.__init__( self, self.SYSTEM_CLASS_NAME, name, port_name=port, **kwargs )

#~autogen
#~autogen python_generic-get-set classes.led>currentClass


    def _get_max_brightness(self):
        return self.get_attr_int( 'max_brightness' )

    _doc_max_brightness = """
        Returns the maximum allowable brightness value.
        """

    max_brightness = property( _get_max_brightness, None, None, _doc_max_brightness )

    def _get_brightness(self):
        return self.get_attr_int( 'brightness' )

    def _set_brightness(self, value):
        self.set_attr_int( 'brightness', value )

    _doc_brightness = """
        Sets the brightness level. Possible values are from 0 to `max_brightness`.
        """

    brightness = property( _get_brightness, _set_brightness, None, _doc_brightness )

    def _get_triggers(self):
        return self.get_attr_set( 'trigger' )

    _doc_triggers = """
        Returns a list of available triggers.
        """

    triggers = property( _get_triggers, None, None, _doc_triggers )

    def _get_trigger(self):
        return self.get_attr_from_set( 'trigger' )

    def _set_trigger(self, value):
        self.set_attr_string( 'trigger', value )

    _doc_trigger = """
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

    trigger = property( _get_trigger, _set_trigger, None, _doc_trigger )

    def _get_delay_on(self):
        return self.get_attr_int( 'delay_on' )

    def _set_delay_on(self, value):
        self.set_attr_int( 'delay_on', value )

    _doc_delay_on = """
        The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `on` time can
        be specified via `delay_on` attribute in milliseconds.
        """

    delay_on = property( _get_delay_on, _set_delay_on, None, _doc_delay_on )

    def _get_delay_off(self):
        return self.get_attr_int( 'delay_off' )

    def _set_delay_off(self, value):
        self.set_attr_int( 'delay_off', value )

    _doc_delay_off = """
        The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `off` time can
        be specified via `delay_off` attribute in milliseconds.
        """

    delay_off = property( _get_delay_off, _set_delay_off, None, _doc_delay_off )


#~autogen
#~autogen python_generic-class classes.powerSupply>currentClass


class PowerSupply(Device):

    """
    A generic interface to read data from the system's power_supply class.
    Uses the built-in legoev3-battery if none is specified.
    """

    SYSTEM_CLASS_NAME = 'power_supply'
    SYSTEM_DEVICE_NAME_CONVENTION = ''

    def __init__(self, port='', name='*', **kwargs ):
        Device.__init__( self, self.SYSTEM_CLASS_NAME, name, port_name=port, **kwargs )

#~autogen
#~autogen python_generic-get-set classes.powerSupply>currentClass


    def _get_measured_current(self):
        return self.get_attr_int( 'current_now' )

    _doc_measured_current = """
        The measured current that the battery is supplying (in microamps)
        """

    measured_current = property( _get_measured_current, None, None, _doc_measured_current )

    def _get_measured_voltage(self):
        return self.get_attr_int( 'voltage_now' )

    _doc_measured_voltage = """
        The measured voltage that the battery is supplying (in microvolts)
        """

    measured_voltage = property( _get_measured_voltage, None, None, _doc_measured_voltage )

    def _get_max_voltage(self):
        return self.get_attr_int( 'voltage_max_design' )

    _doc_max_voltage = """
        """

    max_voltage = property( _get_max_voltage, None, None, _doc_max_voltage )

    def _get_min_voltage(self):
        return self.get_attr_int( 'voltage_min_design' )

    _doc_min_voltage = """
        """

    min_voltage = property( _get_min_voltage, None, None, _doc_min_voltage )

    def _get_technology(self):
        return self.get_attr_string( 'technology' )

    _doc_technology = """
        """

    technology = property( _get_technology, None, None, _doc_technology )

    def _get_type(self):
        return self.get_attr_string( 'type' )

    _doc_type = """
        """

    type = property( _get_type, None, None, _doc_type )


#~autogen
#~autogen python_generic-class classes.legoPort>currentClass


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
    SYSTEM_DEVICE_NAME_CONVENTION = ''

    def __init__(self, port='', name='*', **kwargs ):
        Device.__init__( self, self.SYSTEM_CLASS_NAME, name, port_name=port, **kwargs )

#~autogen
#~autogen python_generic-get-set classes.legoPort>currentClass


    def _get_driver_name(self):
        return self.get_attr_string( 'driver_name' )

    _doc_driver_name = """
        Returns the name of the driver that loaded this device. You can find the
        complete list of drivers in the [list of port drivers].
        """

    driver_name = property( _get_driver_name, None, None, _doc_driver_name )

    def _get_modes(self):
        return self.get_attr_set( 'modes' )

    _doc_modes = """
        Returns a list of the available modes of the port.
        """

    modes = property( _get_modes, None, None, _doc_modes )

    def _get_mode(self):
        return self.get_attr_string( 'mode' )

    def _set_mode(self, value):
        self.set_attr_string( 'mode', value )

    _doc_mode = """
        Reading returns the currently selected mode. Writing sets the mode.
        Generally speaking when the mode changes any sensor or motor devices
        associated with the port will be removed new ones loaded, however this
        this will depend on the individual driver implementing this class.
        """

    mode = property( _get_mode, _set_mode, None, _doc_mode )

    def _get_port_name(self):
        return self.get_attr_string( 'port_name' )

    _doc_port_name = """
        Returns the name of the port. See individual driver documentation for
        the name that will be returned.
        """

    port_name = property( _get_port_name, None, None, _doc_port_name )

    def _set_set_device(self, value):
        self.set_attr_string( 'set_device', value )

    _doc_set_device = """
        For modes that support it, writing the name of a driver will cause a new
        device to be registered for that driver and attached to this port. For
        example, since NXT/Analog sensors cannot be auto-detected, you must use
        this attribute to load the correct driver. Returns -EOPNOTSUPP if setting a
        device is not supported.
        """

    set_device = property( None, _set_set_device, None, _doc_set_device )

    def _get_status(self):
        return self.get_attr_string( 'status' )

    _doc_status = """
        In most cases, reading status will return the same value as `mode`. In
        cases where there is an `auto` mode additional values may be returned,
        such as `no-device` or `error`. See individual port driver documentation
        for the full list of possible values.
        """

    status = property( _get_status, None, None, _doc_status )


#~autogen

