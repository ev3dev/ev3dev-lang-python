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

    red_left = Led(name='ev3-left0:red:ev3dev')
    red_right = Led(name='ev3-right0:red:ev3dev')
    green_left = Led(name='ev3-left1:green:ev3dev')
    green_right = Led(name='ev3-right1:green:ev3dev')

    @staticmethod
    def mix_colors(red, green):
        Leds.red_left.brightness_pct = red
        Leds.red_right.brightness_pct = red
        Leds.green_left.brightness_pct = green
        Leds.green_right.brightness_pct = green

    @staticmethod
    def set_red(pct):
        Leds.mix_colors(red=1 * pct, green=0 * pct)

    @staticmethod
    def red_on():
        Leds.set_red(1)

    @staticmethod
    def set_green(pct):
        Leds.mix_colors(red=0 * pct, green=1 * pct)

    @staticmethod
    def green_on():
        Leds.set_green(1)

    @staticmethod
    def set_amber(pct):
        Leds.mix_colors(red=1 * pct, green=1 * pct)

    @staticmethod
    def amber_on():
        Leds.set_amber(1)

    @staticmethod
    def set_orange(pct):
        Leds.mix_colors(red=1 * pct, green=0.5 * pct)

    @staticmethod
    def orange_on():
        Leds.set_orange(1)

    @staticmethod
    def set_yellow(pct):
        Leds.mix_colors(red=0.5 * pct, green=1 * pct)

    @staticmethod
    def yellow_on():
        Leds.set_yellow(1)

    @staticmethod
    def all_off():
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

    on_up = None
    on_down = None
    on_left = None
    on_right = None
    on_enter = None
    on_backspace = None

    _buttons = {
            'up': {'name': '/dev/input/by-path/platform-gpio-keys.0-event', 'value': 103},
            'down': {'name': '/dev/input/by-path/platform-gpio-keys.0-event', 'value': 108},
            'left': {'name': '/dev/input/by-path/platform-gpio-keys.0-event', 'value': 105},
            'right': {'name': '/dev/input/by-path/platform-gpio-keys.0-event', 'value': 106},
            'enter': {'name': '/dev/input/by-path/platform-gpio-keys.0-event', 'value': 28},
            'backspace': {'name': '/dev/input/by-path/platform-gpio-keys.0-event', 'value': 14},
        }

    @property
    def up(self):
        return 'up' in self.buttons_pressed

    @property
    def down(self):
        return 'down' in self.buttons_pressed

    @property
    def left(self):
        return 'left' in self.buttons_pressed

    @property
    def right(self):
        return 'right' in self.buttons_pressed

    @property
    def enter(self):
        return 'enter' in self.buttons_pressed

    @property
    def backspace(self):
        return 'backspace' in self.buttons_pressed


# ~autogen
