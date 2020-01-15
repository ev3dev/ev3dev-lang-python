#!/usr/bin/env python3
"""
Wheel and Rim classes

A great reference when adding new wheels is http://wheels.sariel.pl/
"""
from math import pi


class Wheel(object):
    """
    A base class for various types of wheels, tires, etc.  All units are in mm.

    One scenario where one of the child classes below would be used is when the
    user needs their robot to drive at a specific speed or drive for a specific
    distance. Both of those calculations require the circumference of the wheel
    of the robot.

    Example:

    .. code:: python

        from ev3dev2.wheel import EV3Tire

        tire = EV3Tire()

        # calculate the number of rotations needed to travel forward 500 mm
        rotations_for_500mm = 500 / tire.circumference_mm
    """
    def __init__(self, diameter_mm, width_mm):
        self.diameter_mm = float(diameter_mm)
        self.width_mm = float(width_mm)
        self.circumference_mm = diameter_mm * pi

    @property
    def radius_mm(self):
        return float(self.diameter_mm / 2)


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
