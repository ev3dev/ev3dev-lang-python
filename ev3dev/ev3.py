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
An assortment of classes modeling specific features of the EV3 brick.
"""

from .core import *


OUTPUT_A = 'outA'
OUTPUT_B = 'outB'
OUTPUT_C = 'outC'
OUTPUT_D = 'outD'

INPUT_1 = 'in1'
INPUT_2 = 'in2'
INPUT_3 = 'in3'
INPUT_4 = 'in4'


class Leds(object):
    """
    The EV3 LEDs.
    """

# ~autogen led-colors platforms.ev3.led>currentClass

    red_left = Led(name_pattern='led0:red:brick-status')
    red_right = Led(name_pattern='led1:red:brick-status')
    green_left = Led(name_pattern='led0:green:brick-status')
    green_right = Led(name_pattern='led1:green:brick-status')

    LEFT = ( red_left, green_left, )
    RIGHT = ( red_right, green_right, )

    BLACK = ( 0, 0, )
    RED = ( 1, 0, )
    GREEN = ( 0, 1, )
    AMBER = ( 1, 1, )
    ORANGE = ( 1, 0.5, )
    YELLOW = ( 0.1, 1, )

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
        Leds.red_left.brightness = 0
        Leds.red_right.brightness = 0
        Leds.green_left.brightness = 0
        Leds.green_right.brightness = 0


# ~autogen

class Button(ButtonEVIO):
    """
    EV3 Buttons
    """

# ~autogen button-property platforms.ev3.button>currentClass

    @staticmethod
    def on_up(state):
        """
        This handler is called by `process()` whenever state of 'up' button
        has changed since last `process()` call. `state` parameter is the new
        state of the button.
        """
        pass

    @staticmethod
    def on_down(state):
        """
        This handler is called by `process()` whenever state of 'down' button
        has changed since last `process()` call. `state` parameter is the new
        state of the button.
        """
        pass

    @staticmethod
    def on_left(state):
        """
        This handler is called by `process()` whenever state of 'left' button
        has changed since last `process()` call. `state` parameter is the new
        state of the button.
        """
        pass

    @staticmethod
    def on_right(state):
        """
        This handler is called by `process()` whenever state of 'right' button
        has changed since last `process()` call. `state` parameter is the new
        state of the button.
        """
        pass

    @staticmethod
    def on_enter(state):
        """
        This handler is called by `process()` whenever state of 'enter' button
        has changed since last `process()` call. `state` parameter is the new
        state of the button.
        """
        pass

    @staticmethod
    def on_backspace(state):
        """
        This handler is called by `process()` whenever state of 'backspace' button
        has changed since last `process()` call. `state` parameter is the new
        state of the button.
        """
        pass


    _buttons = {
            'up': {'name': '/dev/input/by-path/platform-gpio_keys-event', 'value': 103},
            'down': {'name': '/dev/input/by-path/platform-gpio_keys-event', 'value': 108},
            'left': {'name': '/dev/input/by-path/platform-gpio_keys-event', 'value': 105},
            'right': {'name': '/dev/input/by-path/platform-gpio_keys-event', 'value': 106},
            'enter': {'name': '/dev/input/by-path/platform-gpio_keys-event', 'value': 28},
            'backspace': {'name': '/dev/input/by-path/platform-gpio_keys-event', 'value': 14},
        }

    @property
    def up(self):
        """
        Check if 'up' button is pressed.
        """
        return 'up' in self.buttons_pressed

    @property
    def down(self):
        """
        Check if 'down' button is pressed.
        """
        return 'down' in self.buttons_pressed

    @property
    def left(self):
        """
        Check if 'left' button is pressed.
        """
        return 'left' in self.buttons_pressed

    @property
    def right(self):
        """
        Check if 'right' button is pressed.
        """
        return 'right' in self.buttons_pressed

    @property
    def enter(self):
        """
        Check if 'enter' button is pressed.
        """
        return 'enter' in self.buttons_pressed

    @property
    def backspace(self):
        """
        Check if 'backspace' button is pressed.
        """
        return 'backspace' in self.buttons_pressed


# ~autogen
