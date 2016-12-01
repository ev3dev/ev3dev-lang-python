#!/usr/bin/env python3

import logging
import sys
from ev3dev.auto import OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev.helper import RemoteControlledTank, MediumMotor

class EV3D4RemoteControlled(RemoteControlledTank):

    def __init__(self, medium_motor=OUTPUT_A, left_motor=OUTPUT_C, right_motor=OUTPUT_B):
        RemoteControlledTank.__init__(self, left_motor, right_motor)
        self.medium_motor = MediumMotor(medium_motor)

        if not self.medium_motor.connected:
            log.error("%s is not connected" % self.medium_motor)
            sys.exit(1)

        self.medium_motor.reset()


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)5s: %(message)s')
log = logging.getLogger(__name__)

log.info("Starting EV3D4")
ev3d4 = EV3D4RemoteControlled()
ev3d4.main()
log.info("Exiting EV3D4")
