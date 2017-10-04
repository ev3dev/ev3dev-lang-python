#!/usr/bin/env python3

"""
Stop all motors
"""
from ev3dev.motor import list_motors

for motor in list_motors():
    motor.stop(stop_action='brake')
