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

from collections import OrderedDict

OUTPUT_A = 'ev3-ports:outA'
OUTPUT_B = 'ev3-ports:outB'
OUTPUT_C = 'ev3-ports:outC'
OUTPUT_D = 'ev3-ports:outD'

INPUT_1 = 'ev3-ports:in1'
INPUT_2 = 'ev3-ports:in2'
INPUT_3 = 'ev3-ports:in3'
INPUT_4 = 'ev3-ports:in4'

BUTTONS_FILENAME = '/dev/input/by-path/platform-gpio_keys-event'
EVDEV_DEVICE_NAME = 'EV3 brick buttons'

LEDS = OrderedDict()
LEDS['red_left'] = 'led0:red:brick-status'
LEDS['red_right'] = 'led1:red:brick-status'
LEDS['green_left'] = 'led0:green:brick-status'
LEDS['green_right'] = 'led1:green:brick-status'

LED_GROUPS = OrderedDict()
LED_GROUPS['LEFT'] = ('red_left', 'green_left')
LED_GROUPS['RIGHT'] = ('red_right', 'green_right')

LED_COLORS = OrderedDict()
LED_COLORS['BLACK'] = (0, 0)
LED_COLORS['RED'] = (1, 0)
LED_COLORS['GREEN'] = (0, 1)
LED_COLORS['AMBER'] = (1, 1)
LED_COLORS['ORANGE'] = (1, 0.5)
LED_COLORS['YELLOW'] = (0.1, 1)
