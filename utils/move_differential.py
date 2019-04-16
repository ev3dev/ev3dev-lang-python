#!/usr/bin/env python3

"""
Used to experiment with the MoveDifferential class
"""

from ev3dev2.motor import OUTPUT_A, OUTPUT_B, MoveDifferential, SpeedRPM
from ev3dev2.wheel import EV3Tire
from math import pi
import logging
import sys

# logging
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(levelname)5s: %(message)s")
log = logging.getLogger(__name__)

STUD_MM = 8
INCH_MM = 25.4

ONE_FOOT_CICLE_RADIUS_MM = (12 * INCH_MM) / 2
ONE_FOOT_CICLE_CIRCUMFERENCE_MM = 2 * pi * ONE_FOOT_CICLE_RADIUS_MM

# Testing with RileyRover
# http://www.damienkee.com/rileyrover-ev3-classroom-robot-design/
#
# The centers of the wheels are 16 studs apart but this is not the
# "effective" wheel seperation.  Test drives of circles with
# a diameter of 1-foot shows that the effective wheel seperation is
# closer to 16.3 studs. ndward has a writeup that goes into effective
# wheel seperation.
# https://sites.google.com/site/ev3basic/ev3-basic-programming/going-further/writerbot-v1/drawing-arcs
mdiff = MoveDifferential(OUTPUT_A, OUTPUT_B, EV3Tire, 16.3 * STUD_MM)

# This goes crazy on brickpi3, does it do the same on ev3?
#mdiff.on_for_distance(SpeedRPM(-40), 720, brake=False)
#mdiff.on_for_distance(SpeedRPM(40), 720, brake=False)

# Test arc left/right turns
#mdiff.on_arc_right(SpeedRPM(80), ONE_FOOT_CICLE_RADIUS_MM, ONE_FOOT_CICLE_CIRCUMFERENCE_MM / 4)
#mdiff.on_arc_left(SpeedRPM(80), ONE_FOOT_CICLE_RADIUS_MM, ONE_FOOT_CICLE_CIRCUMFERENCE_MM)

# Test turning in place
#mdiff.turn_right(SpeedRPM(40), 180)
#mdiff.turn_left(SpeedRPM(40), 180)

# Test odometry
mdiff.odometry_start()
mdiff.odometry_coordinates_log()

#mdiff.turn_to_angle(SpeedRPM(40), 0)
#mdiff.on_for_distance(SpeedRPM(40), DistanceFeet(2).mm)
#mdiff.turn_right(SpeedRPM(40), 180)
#mdiff.turn_left(SpeedRPM(30), 90)
#mdiff.on_arc_left(SpeedRPM(80), ONE_FOOT_CICLE_RADIUS_MM, ONE_FOOT_CICLE_CIRCUMFERENCE_MM)

log.info("turn on arc to the right")
mdiff.on_arc_right(SpeedRPM(40), ONE_FOOT_CICLE_RADIUS_MM, ONE_FOOT_CICLE_CIRCUMFERENCE_MM / 4)
mdiff.odometry_coordinates_log()

log.info("\n\n\n\n")
log.info("go back to (0, 0)")
mdiff.odometry_coordinates_log()
mdiff.on_to_coordinates(SpeedRPM(40), 0, 0)

mdiff.turn_to_angle(SpeedRPM(40), 90)
mdiff.odometry_coordinates_log()
mdiff.odometry_stop()
