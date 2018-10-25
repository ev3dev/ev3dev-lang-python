#!/usr/bin/env python3

"""
Used to adjust the position of a motor in an already assembled robot
where you can"t move the motor by hand.
"""

from ev3dev2.motor import OUTPUT_A, OUTPUT_B, MoveDifferential, SpeedRPM
from ev3dev2.wheel import EV3RubberWheel
from math import pi
import argparse
import logging
import sys

# command line args
'''
parser = argparse.ArgumentParser(description="Used to adjust the position of a motor in an already assembled robot")
parser.add_argument("motor", type=str, help="A, B, C or D")
parser.add_argument("degrees", type=int)
parser.add_argument("-s", "--speed", type=int, default=50)
args = parser.parse_args()
'''

# logging
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(levelname)5s: %(message)s")
log = logging.getLogger(__name__)

STUD_MM = 8
INCH_MM = 25.4

ONE_FOOT_CICLE_RADIUS_MM = (12 * INCH_MM) / 2
ONE_FOOT_CICLE_CIRCUMFERENCE_MM = 2 * pi * ONE_FOOT_CICLE_RADIUS_MM

# Testing with RileyRover
# http://www.damienkee.com/home/2013/8/2/rileyrover-ev3-classroom-robot-design.html
#
# The centers of the wheels are 16 studs apart but this is not the
# "effective" wheel seperation.  Test drives of circles with
# a diameter of 1-foot shows that the effective wheel seperation is
# closer to 16.3 studs. ndward has a writeup that goes into effective
# wheel seperation.
# https://sites.google.com/site/ev3basic/ev3-basic-programming/going-further/writerbot-v1/drawing-arcs
mdiff = MoveDifferential(OUTPUT_A, OUTPUT_B, EV3RubberWheel, 16.3 * STUD_MM)

# This goes crazy on brickpi3, does it do the same on ev3?
#mdiff.on_for_distance(SpeedRPM(-40), 720, brake=False)
#mdiff.on_for_distance(SpeedRPM(40), 720, brake=False)

# Test arc left/right turns
#mdiff.on_arc_right(SpeedRPM(80), ONE_FOOT_CICLE_RADIUS_MM, ONE_FOOT_CICLE_CIRCUMFERENCE_MM / 4)
mdiff.on_arc_left(SpeedRPM(80), ONE_FOOT_CICLE_RADIUS_MM, ONE_FOOT_CICLE_CIRCUMFERENCE_MM)

# Test turning in place
#mdiff.turn_right(SpeedRPM(40), 180)
#mdiff.turn_left(SpeedRPM(40), 180)
