#!/usr/bin/env python

"""
Stop all motors
"""
from ev3dev.auto import list_motors

for motor in list_motors():
    motor.stop()
