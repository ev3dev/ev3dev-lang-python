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
