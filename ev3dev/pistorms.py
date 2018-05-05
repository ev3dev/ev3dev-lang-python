# ------------------------------------------------------------------------------
# Copyright (c) 2018 David Lechner <david@lechnology.com>
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
An assortment of classes modeling specific features of the EV3 brick.
"""

from .core import *


OUTPUT_A = 'pistorms:BAM1'
OUTPUT_B = 'pistorms:BAM2'
OUTPUT_C = 'pistorms:BBM1'
OUTPUT_D = 'pistorms:BBM2'

INPUT_1 = 'pistorms:BAS1'
INPUT_2 = 'pistorms:BAS2'
INPUT_3 = 'pistorms:BBS1'
INPUT_4 = 'pistorms:BBS2'


class Leds(object):
    """
    The PiStorms LEDs.
    """

    red_left = Led(name_pattern='pistorms:BB:red:brick-status')
    red_right = Led(name_pattern='pistorms:BA:red:brick-status')
    green_left = Led(name_pattern='pistorms:BB:green:brick-status')
    green_right = Led(name_pattern='pistorms:BA:green:brick-status')
    blue_left = Led(name_pattern='pistorms:BB:blue:brick-status')
    blue_right = Led(name_pattern='pistorms:BA:blue:brick-status')

    LEFT = (red_left, green_left, blue_left)
    RIGHT = (red_right, green_right, blue_right)

    BLACK = (0, 0, 0)
    RED = (1, 0, 0)
    GREEN = (0, 1, 0)
    BLUE = (0, 0, 1)
    YELLOW = (1, 1, 0)
    CYAN = (0, 1, 1)
    MAGENTA = (1, 0, 1)

    @staticmethod
    def set_color(group, color, pct=1):
        """
        Sets brightness of leds in the given group to the values specified in
        color tuple. When percentage is specified, brightness of each led is
        reduced proportionally.

        Example::

            Leds.set_color(LEFT, MAGENTA)
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
        Leds.red_left.brightness = 0
        Leds.red_right.brightness = 0
        Leds.green_left.brightness = 0
        Leds.green_right.brightness = 0
        Leds.blue_left.brightness = 0
        Leds.blue_right.brightness = 0


class Button(ButtonEVIO):
    """
    PiStorms Buttons
    """

    @staticmethod
    def on_go(state):
        """
        This handler is called by `process()` whenever state of 'enter' button
        has changed since last `process()` call. `state` parameter is the new
        state of the button.
        """
        pass

    _buttons = {
        'go': {
            'name': '/dev/input/by-path/platform-3f804000.i2c-event',
            'value': 103,
        },
    }

    @property
    def go(self):
        """
        Check if 'go' button is pressed.
        """
        return 'go' in self.buttons_pressed
