#!/usr/bin/env micropython
"""
Stop all motors
"""
from ev3dev2.motor import list_motors

for motor in list_motors():
    motor.stop(stop_action='brake')
