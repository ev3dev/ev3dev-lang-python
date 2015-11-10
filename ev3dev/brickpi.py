# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2015 Eric Pascual
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
# FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -----------------------------------------------------------------------------

"""
An assortment of classes modeling specific features of the BrickPi.
"""

from .core import *


OUTPUT_A = 'ttyAMA0:outA'
OUTPUT_B = 'ttyAMA0:outB'
OUTPUT_C = 'ttyAMA0:outC'
OUTPUT_D = 'ttyAMA0:outD'

INPUT_1 = 'ttyAMA0:in1'
INPUT_2 = 'ttyAMA0:in2'
INPUT_3 = 'ttyAMA0:in3'
INPUT_4 = 'ttyAMA0:in4'


class Leds(object):
    """
    The BrickPi LEDs.
    """

# ~autogen led-colors platforms.brickpi.led>currentClass

    blue_one = Led(name='brickpi1:blue:ev3dev')
    blue_two = Led(name='brickpi2:blue:ev3dev')

    BLUE_ONE = ( blue_one, )
    BLUE_TWO = ( blue_two, )

    BLUE = ( 1, )

    @staticmethod
    def set_color(group, color, pct=1):
        """
        Sets brigthness of leds in the given group to the values specified in
        color tuple. When percentage is specified, brightness of each led is
        reduced proportionally.

        Example::

            Leds.set_color(LEFT, AMBER)
        """
        for l, v in zip(group, color):
            l.brightness_pct = v * pct

    @staticmethod
    def set(group, **kwargs):
        """
        Set attributes for each led in group.

        Example::

            Leds.set(LEFT, brightness_pct=0.5, trigger='timer')
        """
        for led in group:
            for k in kwargs:
                setattr(led, k, kwargs[k])

    @staticmethod
    def all_off():
        """
        Turn all leds off
        """
        Leds.blue_one.brightness = 0
        Leds.blue_two.brightness = 0


# ~autogen
