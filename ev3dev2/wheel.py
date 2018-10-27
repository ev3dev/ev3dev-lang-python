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


class EV3Rim(Wheel):
    """
    part number 56145
    comes in set 31313
    """
    def __init__(self):
        Wheel.__init__(self, 30, 20)


class EV3Tire(Wheel):
    """
    part number 44309
    comes in set 31313
    """

    def __init__(self):
        Wheel.__init__(self, 43.2, 21)


class EV3EducationSetRim(Wheel):
    """
    part number 56908
    comes in set 45544
    """

    def __init__(self):
        Wheel.__init__(self, 43, 26)


class EV3EducationSetTire(Wheel):
    """
    part number 41897
    comes in set 45544
    """

    def __init__(self):
        Wheel.__init__(self, 56, 28)
