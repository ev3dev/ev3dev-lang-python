#!/usr/bin/env python3

"""
Wheel and Rim classes

A great reference when adding new wheels is http://wheels.sariel.pl/
"""
from math import pi


class Wheel(object):
    """
    A base class for various types of wheels, tires, etc
    All units are in mm
    """

    def __init__(self, diameter_mm, width_mm):
        self.diameter_mm = float(diameter_mm)
        self.width_mm = float(width_mm)
        self.radius_mm = float(diameter_mm / 2)
        self.circumference_mm = diameter_mm * pi


class EV3RubberWheel(Wheel):

    def __init__(self):
        Wheel.__init__(self, 43.2, 21)
