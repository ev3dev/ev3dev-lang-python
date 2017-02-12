#!/usr/bin/env python3
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

""" This demo illustrates how to use the two red-green LEDs of the EV3 brick.
"""

import time
import math

from ev3dev.ev3 import Leds

print(__doc__.lstrip())

print('saving current LEDs state')

# save current state
saved_state = [led.brightness_pct for led in Leds.LEFT + Leds.RIGHT]

Leds.all_off()
time.sleep(1)

# cycle LEDs like a traffic light
print('traffic light')
for _ in range(3):
    for color in (Leds.GREEN, Leds.YELLOW, Leds.RED):
        for group in (Leds.LEFT, Leds.RIGHT):
            Leds.set_color(group, color)
        time.sleep(0.5)

Leds.all_off()
time.sleep(0.5)

# blink LEDs from side to side now
print('side to side')
for _ in range(3):
    for led in (Leds.red_left, Leds.red_right, Leds.green_left, Leds.green_right):
        led.brightness_pct = 100
        time.sleep(0.5)
        led.brightness_pct = 0

Leds.all_off()
time.sleep(0.5)

# continuous mix of colors
print('colors fade')
for i in range(360):
    rd = math.radians(10 * i)
    Leds.red_left.brightness_pct = .5 * (1 + math.cos(rd))
    Leds.green_left.brightness_pct = .5 * (1 + math.sin(rd))
    Leds.red_right.brightness_pct = .5 * (1 + math.sin(rd))
    Leds.green_right.brightness_pct = .5 * (1 + math.cos(rd))
    time.sleep(0.05)

Leds.all_off()
time.sleep(0.5)

print('restoring initial LEDs state')
for led, level in zip(Leds.RIGHT + Leds.LEFT, saved_state) :
    led.brightness_pct = level

