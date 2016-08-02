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


OUTPUT_A = 'ttyAMA0:MA'
OUTPUT_B = 'ttyAMA0:MB'
OUTPUT_C = 'ttyAMA0:MC'
OUTPUT_D = 'ttyAMA0:MD'

INPUT_1 = 'ttyAMA0:S1'
INPUT_2 = 'ttyAMA0:S2'
INPUT_3 = 'ttyAMA0:S3'
INPUT_4 = 'ttyAMA0:S4'


class Leds(object):
    """
    The BrickPi LEDs.
    """

# ~autogen led-colors platforms.brickpi.led>currentClass

    blue_led1 = Led(name_pattern='brickpi:led1:blue:ev3dev')
    blue_led2 = Led(name_pattern='brickpi:led2:blue:ev3dev')

    LED1 = ( blue_led1, )
    LED2 = ( blue_led2, )

    BLACK = ( 0, )
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
        Leds.blue_led1.brightness = 0
        Leds.blue_led2.brightness = 0


# ~autogen
