# -----------------------------------------------------------------------------
# Copyright (c) 2015 Ralph Hempel
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -----------------------------------------------------------------------------

import sys

if sys.version_info < (3, 4):
    raise SystemError('Must be using Python 3.4 or higher')

CENTIMETER_MM = 10
DECIMETER_MM = 100
METER_MM = 1000
INCH_MM = 25.4
FOOT_MM = 304.8
YARD_MM = 914.4
STUD_MM = 8


class DistanceValue(object):
    """
    A base class for other unit types. Don't use this directly; instead, see
    :class:`DistanceMillimeters`, :class:`DistanceCentimeters`, :class:`DistanceDecimeters``, :class:`DistanceMeters`,
    :class:`DistanceInches`, :class:`DistanceFeet`, :class:`DistanceYards` and :class:`DistanceStuds`.
    """

    # This allows us to sort lists of DistanceValue objects
    def __lt__(self, other):
        return self.mm < other.mm

    def __rmul__(self, other):
        return self.__mul__(other)


class DistanceMillimeters(DistanceValue):
    """
    Distance in millimeters
    """
    def __init__(self, millimeters):
        self.millimeters = millimeters

    def __str__(self):
        return str(self.millimeters) + "mm"

    def __mul__(self, other):
        assert isinstance(other, (float, int)), "{} can only be multiplied by an int or float".format(self)
        return DistanceMillimeters(self.millimeters * other)

    @property
    def mm(self):
        return self.millimeters


class DistanceCentimeters(DistanceValue):
    """
    Distance in centimeters
    """
    def __init__(self, centimeters):
        self.centimeters = centimeters

    def __str__(self):
        return str(self.centimeters) + "cm"

    def __mul__(self, other):
        assert isinstance(other, (float, int)), "{} can only be multiplied by an int or float".format(self)
        return DistanceCentimeters(self.centimeters * other)

    @property
    def mm(self):
        return self.centimeters * CENTIMETER_MM


class DistanceDecimeters(DistanceValue):
    """
    Distance in decimeters
    """
    def __init__(self, decimeters):
        self.decimeters = decimeters

    def __str__(self):
        return str(self.decimeters) + "dm"

    def __mul__(self, other):
        assert isinstance(other, (float, int)), "{} can only be multiplied by an int or float".format(self)
        return DistanceDecimeters(self.decimeters * other)

    @property
    def mm(self):
        return self.decimeters * DECIMETER_MM


class DistanceMeters(DistanceValue):
    """
    Distance in meters
    """
    def __init__(self, meters):
        self.meters = meters

    def __str__(self):
        return str(self.meters) + "m"

    def __mul__(self, other):
        assert isinstance(other, (float, int)), "{} can only be multiplied by an int or float".format(self)
        return DistanceMeters(self.meters * other)

    @property
    def mm(self):
        return self.meters * METER_MM


class DistanceInches(DistanceValue):
    """
    Distance in inches
    """
    def __init__(self, inches):
        self.inches = inches

    def __str__(self):
        return str(self.inches) + "in"

    def __mul__(self, other):
        assert isinstance(other, (float, int)), "{} can only be multiplied by an int or float".format(self)
        return DistanceInches(self.inches * other)

    @property
    def mm(self):
        return self.inches * INCH_MM


class DistanceFeet(DistanceValue):
    """
    Distance in feet
    """
    def __init__(self, feet):
        self.feet = feet

    def __str__(self):
        return str(self.feet) + "ft"

    def __mul__(self, other):
        assert isinstance(other, (float, int)), "{} can only be multiplied by an int or float".format(self)
        return DistanceFeet(self.feet * other)

    @property
    def mm(self):
        return self.feet * FOOT_MM


class DistanceYards(DistanceValue):
    """
    Distance in yards
    """
    def __init__(self, yards):
        self.yards = yards

    def __str__(self):
        return str(self.yards) + "yd"

    def __mul__(self, other):
        assert isinstance(other, (float, int)), "{} can only be multiplied by an int or float".format(self)
        return DistanceYards(self.yards * other)

    @property
    def mm(self):
        return self.yards * YARD_MM


class DistanceStuds(DistanceValue):
    """
    Distance in studs
    """
    def __init__(self, studs):
        self.studs = studs

    def __str__(self):
        return str(self.studs) + "stud"

    def __mul__(self, other):
        assert isinstance(other, (float, int)), "{} can only be multiplied by an int or float".format(self)
        return DistanceStuds(self.studs * other)

    @property
    def mm(self):
        return self.studs * STUD_MM
