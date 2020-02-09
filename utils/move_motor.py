#!/usr/bin/env python3
"""
Used to adjust the position of a motor in an already assembled robot
where you can"t move the motor by hand.
"""

from ev3dev2.motor import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D, Motor
import argparse
import logging

# command line args
parser = argparse.ArgumentParser(description="Used to adjust the position of a motor in an already assembled robot")
parser.add_argument("motor", type=str, help="A, B, C or D")
parser.add_argument("degrees", type=int)
parser.add_argument("-s", "--speed", type=int, default=50)
args = parser.parse_args()

# logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)5s: %(message)s")
log = logging.getLogger(__name__)

if args.motor == "A":
    motor = Motor(OUTPUT_A)
elif args.motor == "B":
    motor = Motor(OUTPUT_B)
elif args.motor == "C":
    motor = Motor(OUTPUT_C)
elif args.motor == "D":
    motor = Motor(OUTPUT_D)
else:
    raise Exception("%s is invalid, options are A, B, C, D")

if args.degrees:
    log.info("Motor %s, current position %d, move to position %d, max speed %d" %
             (args.motor, motor.position, args.degrees, motor.max_speed))
    motor.run_to_rel_pos(speed_sp=args.speed, position_sp=args.degrees, stop_action='hold')
