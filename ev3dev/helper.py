#!/usr/bin/env python3

import logging
import math
import os
import re
import sys
import time
import ev3dev.auto
from collections import OrderedDict
from ev3dev.auto import (RemoteControl, list_motors,
                         INPUT_1, INPUT_2, INPUT_3, INPUT_4,
                         OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D)
from time import sleep

log = logging.getLogger(__name__)

INPUTS = (INPUT_1, INPUT_2, INPUT_3, INPUT_4)
OUTPUTS = (OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D)


# =============
# Motor classes
# =============
class MotorStartFail(Exception):
    pass


class MotorStopFail(Exception):
    pass


class MotorPositionFail(Exception):
    pass


class MotorStall(Exception):
    pass


class MotorMixin(object):
    shutdown = False

    def running(self):
        prev_pos = self.position
        time.sleep(0.01)
        pos = self.position
        return True if pos != prev_pos else False

    def wait_for_running(self, timeout=5):
        """
        timeout is in seconds
        """
        tic = time.time() + timeout
        prev_pos = None

        while time.time() < tic:

            if self.shutdown:
                break

            pos = self.position

            if prev_pos is not None and pos != prev_pos:
                break
            else:
                prev_pos = pos
                time.sleep(0.001)
        else:
            raise MotorStartFail("%s: failed to start within %ds" % (self, timeout))

    def wait_for_stop(self, timeout=60):
        """
        timeout is in seconds
        """
        tic = time.time() + timeout
        prev_pos = None
        stall_count = 0

        while time.time() < tic:
            if self.shutdown:
                break

            pos = self.position
            log.debug("%s: wait_for_stop() pos %s, prev_pos %s, stall_count %d" % (self, pos, prev_pos, stall_count))

            if prev_pos is not None and pos == prev_pos:
                stall_count += 1
            else:
                stall_count = 0

            prev_pos = pos

            if stall_count >= 5:
                break
            else:
                time.sleep(0.001)
        else:
            raise MotorStopFail("%s: failed to stop within %ds" % (self, timeout))

    def wait_for_position(self, target_position, delta=2, timeout=10, stall_ok=False):
        """
        delta is in degrees
        timeout is in seconds
        """
        min_pos = target_position - delta
        max_pos = target_position + delta
        time_cutoff = time.time() + timeout
        prev_pos = None
        stall_count = 0

        while time.time() < time_cutoff:

            if self.shutdown:
                break

            pos = self.position
            log.debug("%s: wait_for_pos() pos %d/%d, min_pos %d, max_pos %d" % (self, pos, target_position, min_pos, max_pos))

            if pos >= min_pos and pos <= max_pos:
                break

            if prev_pos is not None and pos == prev_pos:
                stall_count += 1
            else:
                stall_count = 0

            if stall_count == 50:
                if stall_ok:
                    log.warning("%s: stalled at position %d, target was %d" % (self, pos, target_position))
                    break
                else:
                    raise MotorStall("%s: stalled at position %d, target was %d" % (self, pos, target_position))

            prev_pos = pos
            time.sleep(0.001)
        else:
            raise MotorPositionFail("%s: failed to reach %s within %ss, current position %d" %
                                    (self, target_position, timeout, pos))


class LargeMotor(ev3dev.auto.LargeMotor, MotorMixin):
    pass


class MediumMotor(ev3dev.auto.MediumMotor, MotorMixin):
    pass


class MotorSet(object):
    """
    motor_specs is a dictionary such as
    {
        OUTPUT_A : LargeMotor,
        OUTPUT_B : MediumMotor,
    }
    """

    def __init__(self, motor_specs, desc=None):

        for motor_port in motor_specs.keys():
            if motor_port not in OUTPUTS:
                log.error("%s in an invalid motor, choices are %s" % (motor_port, ', '.join(OUTPUTS)))
                sys.exit(1)

        self.motors = OrderedDict()
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
                log.error("%s: %s is not connected" % (self, motor))
                sys.exit(1)

    def set_args(self, **kwargs):
        motors = kwargs.get('motors', self.motors.values())

        for motor in motors:
            for key in kwargs:
                if key != 'motors':
                    try:
                        setattr(motor, key, kwargs[key])
                    except AttributeError as e:
                        log.error("%s %s cannot set %s to %s" % (self, motor, key, kwargs[key]))
                        raise e

    def set_polarity(self, polarity, motors=None):
        valid_choices = ('normal', 'inversed')
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
                    log.debug("%s: %s set %s to %s" % (self, motor, key, kwargs[key]))
                    setattr(motor, key, kwargs[key])

        for motor in motors:
            motor.command = kwargs['command']
            log.debug("%s: %s command %s" % (self, motor, kwargs['command']))

    def run_forever(self, **kwargs):
        kwargs['command'] = ev3dev.auto.LargeMotor.COMMAND_RUN_FOREVER
        self._run_command(**kwargs)

    def run_to_abs_pos(self, **kwargs):
        kwargs['command'] = ev3dev.auto.LargeMotor.COMMAND_RUN_TO_ABS_POS
        self._run_command(**kwargs)

    def run_to_rel_pos(self, **kwargs):
        kwargs['command'] = ev3dev.auto.LargeMotor.COMMAND_RUN_TO_REL_POS
        self._run_command(**kwargs)

    def run_timed(self, **kwargs):
        kwargs['command'] = ev3dev.auto.LargeMotor.COMMAND_RUN_TIMED
        self._run_command(**kwargs)

    def run_direct(self, **kwargs):
        kwargs['command'] = ev3dev.auto.LargeMotor.COMMAND_RUN_DIRECT
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
        return self._is_state(motors, ev3dev.auto.LargeMotor.STATE_RUNNING)

    @property
    def is_ramping(self, motors=None):
        return self._is_state(motors, ev3dev.auto.LargeMotor.STATE_RAMPING)

    @property
    def is_holding(self, motors=None):
        return self._is_state(motors, ev3dev.auto.LargeMotor.STATE_HOLDING)

    @property
    def is_overloaded(self, motors=None):
        return self._is_state(motors, ev3dev.auto.LargeMotor.STATE_OVERLOADED)

    @property
    def is_stalled(self):
        return self._is_state(motors, ev3dev.auto.LargeMotor.STATE_STALLED)

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


class MotorPair(MotorSet):

    def __init__(self, motor_specs, desc=None):
        MotorSet.__init__(self, motor_specs, desc)
        (self.left_motor, self.right_motor) = self.motors.values()
        self.max_speed = self.left_motor.max_speed

    def set_speed_steering(self, direction, power=100):
        """
        Set the speed_sp for each motor in a pair to achieve the specified steering

        direction [-100, 100]:
            * -100 means turn left as fast as possible,
            *  0   means drive in a straight line, and
            *  100 means turn right as fast as possible.

        power: the power that should be applied to the outmost motor (the one
               rotating faster). The power of the other motor will be computed
               automatically.
        """

        assert direction >= -100 and direction <= 100,\
            "%s is an invalid direction, must be between -100 and 100 (inclusive)" % direction

        left_power = power
        right_power = power
        speed = (50 - abs(float(direction))) / 50

        if direction >= 0:
            right_power *= speed
        else:
            left_power *= speed

        left_power = int(left_power)
        right_power = int(right_power)
        log.debug("%s: direction %d, power %d, speed %d, left_power %d, right_power %d" %
            (self, direction, power, speed, left_power, right_power))

        self.left_motor.speed_sp = int(left_power)
        self.right_motor.speed_sp = int(right_power)

    def set_speed_percentage(self, left_motor_percentage, right_motor_percentage):
        """
        Set the speeds of the left_motor vs right_motor by percentage of
        their maximum speed.  The minimum valid percentage is -100, the
        maximum is 100.
        """

        assert left_motor_percentage >= -100 and left_motor_percentage <= 100,\
            "%s is an invalid percentage, must be between -100 and 100 (inclusive)" % left_motor_percentage

        assert right_motor_percentage >= -100 and right_motor_percentage <= 100,\
            "%s is an invalid percentage, must be between -100 and 100 (inclusive)" % right_motor_percentage

        # Convert left_motor_percentage and right_motor_percentage to fractions
        left_motor_percentage = left_motor_percentage / 100.0
        right_motor_percentage = right_motor_percentage / 100.0

        self.left_motor.speed_sp = int(self.max_speed * left_motor_percentage)
        self.right_motor.speed_sp = int(self.max_speed * right_motor_percentage)


class LargeMotorPair(MotorPair):

    def __init__(self, left_motor, right_motor, desc=None):
        motor_specs = {
            left_motor : LargeMotor,
            right_motor : LargeMotor,
        }
        MotorPair.__init__(self, motor_specs, desc)


class MediumMotorPair(MotorPair):

    def __init__(self, left_motor, right_motor, desc=None):
        motor_specs = {
            left_motor : MediumMotor,
            right_motor : MediumMotor,
        }
        MotorPair.__init__(self, motor_specs, desc)


class ColorSensorMixin(object):

    def rgb(self):
        """
        Note that the mode for the ColorSensor must be set to MODE_RGB_RAW
        """
        # These values are on a scale of 0-1020, convert them to a normal 0-255 scale
        red = int((self.value(0) * 255) / 1020)
        green = int((self.value(1) * 255) / 1020)
        blue = int((self.value(2) * 255) / 1020)

        return (red, green, blue)


class ColorSensor(ev3dev.auto.ColorSensor, ColorSensorMixin):
    pass


# ============
# Tank classes
# ============
class Tank(LargeMotorPair):
    """
    This class is here for backwards compatibility for anyone who was using
    this library before the days of LargeMotorPair. We wrote the Tank class
    first, then LargeMotorPair.  All future work will be in the MotorSet,
    MotorPair, etc classes
    """

    def __init__(self, left_motor_port, right_motor_port, polarity='normal', name='Tank'):
        LargeMotorPair.__init__(self, left_motor_port, right_motor_port, name)
        self.set_polarity(polarity)
        self.speed_sp = 400


class RemoteControlledTank(LargeMotorPair):

    def __init__(self, left_motor_port, right_motor_port, polarity='inversed', speed=400):
        LargeMotorPair.__init__(self, left_motor_port, right_motor_port)
        self.set_polarity(polarity)

        left_motor = self.motors[left_motor_port]
        right_motor = self.motors[right_motor_port]
        self.speed_sp = speed
        self.remote = RemoteControl(channel=1)
        self.remote.on_red_up = self.make_move(left_motor, self.speed_sp)
        self.remote.on_red_down = self.make_move(left_motor, self.speed_sp* -1)
        self.remote.on_blue_up = self.make_move(right_motor, self.speed_sp)
        self.remote.on_blue_down = self.make_move(right_motor, self.speed_sp * -1)

    def make_move(self, motor, dc_sp):
        def move(state):
            if state:
                motor.run_forever(speed_sp=dc_sp)
            else:
                motor.stop()
        return move

    def main(self):

        try:
            while True:
                self.remote.process()
                time.sleep(0.01)

        # Exit cleanly so that all motors are stopped
        except (KeyboardInterrupt, Exception) as e:
            log.exception(e)
            self.stop()


# =====================
# Wheel and Rim classes
# =====================
class Wheel(object):
    """
    A base class for various types of wheels, tires, etc
    All units are in mm
    """

    def __init__(self, diameter, width):
        self.diameter = float(diameter)
        self.width = float(width)
        self.radius = float(diameter/2)
        self.circumference = diameter * math.pi


# A great reference when adding new wheels is http://wheels.sariel.pl/
class EV3RubberWheel(Wheel):

    def __init__(self):
        Wheel.__init__(self, 43.2, 21)
