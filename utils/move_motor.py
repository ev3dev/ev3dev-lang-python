#!/usr/bin/env python

"""
Used to adjust the position of a motor in an already assembled robot
where you can"t move the motor by hand.
"""

from ev3dev.auto import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev.helper import LargeMotor
import argparse
import logging
import sys

# command line args
parser = argparse.ArgumentParser(description="Used to adjust the position of a motor in an already assembled robot")
parser.add_argument("motor", type=str, help="A, B, C or D")
parser.add_argument("degrees", type=int)
parser.add_argument("-s", "--speed", type=int, default=50)
args = parser.parse_args()

# logging
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(levelname)5s: %(message)s")
log = logging.getLogger(__name__)

# For this it doesn't really matter if it is a LargeMotor or a MediumMotor
if args.motor == "A":
    motor = LargeMotor(OUTPUT_A)
elif args.motor == "B":
    motor = LargeMotor(OUTPUT_B)
elif args.motor == "C":
    motor = LargeMotor(OUTPUT_C)
elif args.motor == "D":
    motor = LargeMotor(OUTPUT_D)
else:
    raise Exception("%s is invalid, options are A, B, C, D")

if not motor.connected:
    log.error("%s is not connected" % motor)
    sys.exit(1)

motor.reset()
log.info("Motor %s, move to position %d" % (args.motor, args.degrees))
motor.run_to_rel_pos(speed_sp=args.speed,
                     # ramp_down_sp=200,
                     position_sp=args.degrees)
motor.wait_for_running()
log.info("Motor %s is running" % args.motor)
motor.wait_for_stop()
log.info("Motor %s stopped, final position %d" % (args.motor, motor.position))
