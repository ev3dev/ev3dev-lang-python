#!/usr/bin/env python

import logging
import sys
import time
import ev3dev.auto
from ev3dev.auto import OUTPUTS, RemoteControl, list_motors
from math import pi
from time import sleep

log = logging.getLogger(__name__)


def wait_for(condition, timeout=1e5, interval=0.01):
    tic = time.time() + timeout
    done = condition()

    while time.time() < tic and not done:
        time.sleep(interval)
        done = condition()

    return done


# =============
# Motor classes
# =============
class MotorMixin(object):

    def wait_for_running(self):
        return wait_for(lambda: 'running' in self.state, 1)

    def wait_for_stop(self):
        return wait_for(lambda: 'running' not in self.state, 1)


class LargeMotor(ev3dev.auto.LargeMotor, MotorMixin):
    pass


class MediumMotor(ev3dev.auto.MediumMotor, MotorMixin):
    pass


# ============
# Tank classes
# ============
class Tank(object):

    def __init__(self, left_motor, right_motor, polarity='normal'):

        for motor in (left_motor, right_motor):
            if motor not in OUTPUTS:
                log.error("%s in an invalid motor, choices are %s" % (motor, ', '.join(OUTPUTS)))
                sys.exit(1)

        self.left_motor = LargeMotor(left_motor)
        self.right_motor = LargeMotor(right_motor)

        for x in (self.left_motor, self.right_motor):
            if not x.connected:
                log.error("%s is not connected" % x)
                sys.exit(1)

        self.left_motor.reset()
        self.right_motor.reset()
        self.duty_cycle_sp = 90
        self.left_motor.duty_cycle_sp = self.duty_cycle_sp
        self.right_motor.duty_cycle_sp = self.duty_cycle_sp
        self.set_polarity(polarity)

    def set_polarity(self, polarity):
        valid_choices = ('normal', 'inversed')
        assert polarity in valid_choices,\
            "%s is an invalid polarity choice, must be %s" % (polarity, ', '.join(valid_choices))

        self.left_motor.polarity = polarity
        self.right_motor.polarity = polarity


class RemoteControlledTank(Tank):

    def __init__(self, left_motor, right_motor, polarity='inversed'):
        Tank.__init__(self, left_motor, right_motor, polarity)
        self.remote = RemoteControl(channel=1)

        if not self.remote.connected:
            log.error("%s is not connected" % self.remote)
            sys.exit(1)

        self.remote.on_red_up = self.make_move(self.left_motor, self.duty_cycle_sp)
        self.remote.on_red_down = self.make_move(self.left_motor, self.duty_cycle_sp * -1)
        self.remote.on_blue_up = self.make_move(self.right_motor, self.duty_cycle_sp)
        self.remote.on_blue_down = self.make_move(self.right_motor, self.duty_cycle_sp * -1)

    def make_move(self, motor, dc_sp):
        def move(state):
            if state:
                motor.run_forever(duty_cycle_sp=dc_sp)
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

            for motor in list_motors():
                motor.stop()


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
        self.circumference = diameter * pi


# A great reference when adding new wheels is http://wheels.sariel.pl/
class EV3RubberWheel(Wheel):

    def __init__(self):
        Wheel.__init__(self, 43.2, 21)
