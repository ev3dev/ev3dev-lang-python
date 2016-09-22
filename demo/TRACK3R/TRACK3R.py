#!/usr/bin/env python3

import logging
import sys
from ev3dev.auto import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev.helper import RemoteControlledTank, MediumMotor

log = logging.getLogger(__name__)


class TRACK3R(RemoteControlledTank):
    """
    Base class for all TRACK3R variations. The only difference in the child
    classes are in how the medium motor is handled.

    To enable the medium motor toggle the beacon button on the EV3 remote.
    """

    def __init__(self, medium_motor, left_motor, right_motor):
        RemoteControlledTank.__init__(self, left_motor, right_motor)
        self.medium_motor = MediumMotor(medium_motor)

        if not self.medium_motor.connected:
            log.error("%s is not connected" % self.medium_motor)
            sys.exit(1)

        self.medium_motor.reset()


class TRACK3RWithBallShooter(TRACK3R):

    def __init__(self, medium_motor=OUTPUT_A, left_motor=OUTPUT_B, right_motor=OUTPUT_C):
        TRACK3R.__init__(self, medium_motor, left_motor, right_motor)
        self.remote.on_beacon = self.fire_ball

    def fire_ball(self, state):
        if state:
            self.medium_motor.run_to_rel_pos(speed_sp=400, position_sp=3*360)
        else:
            self.medium_motor.stop()


class TRACK3RWithSpinner(TRACK3R):

    def __init__(self, medium_motor=OUTPUT_A, left_motor=OUTPUT_B, right_motor=OUTPUT_C):
        TRACK3R.__init__(self, medium_motor, left_motor, right_motor)
        self.remote.on_beacon = self.spinner

    def spinner(self, state):
        if state:
            self.medium_motor.run_forever(speed_sp=50)
        else:
            self.medium_motor.stop()


class TRACK3RWithClaw(TRACK3R):

    def __init__(self, medium_motor=OUTPUT_A, left_motor=OUTPUT_B, right_motor=OUTPUT_C):
        TRACK3R.__init__(self, medium_motor, left_motor, right_motor)
        self.remote.on_beacon = self.move_claw

    def move_claw(self, state):
        if state:
            self.medium_motor.run_to_rel_pos(speed_sp=200, position_sp=-75)
        else:
            self.medium_motor.run_to_rel_pos(speed_sp=200, position_sp=75)
