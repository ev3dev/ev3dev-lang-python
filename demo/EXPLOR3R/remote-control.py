#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# Copyright (c) 2015 Denis Demidov <dennis.demidov@gmail.com>
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

# This demo shows how to remote control an Explor3r robot with touch sensor
# attachment.
#
# Red buttons control left motor, blue buttons control right motor.
# Leds are used to indicate movement direction.
# Whenever an obstacle is bumped, robot backs away and apologises.

from time import sleep
from ev3dev.auto import *

# Connect two large motors on output ports B and C
lmotor, rmotor = [LargeMotor(address) for address in (OUTPUT_B, OUTPUT_C)]

# Check that the motors are actually connected
assert lmotor.connected
assert rmotor.connected

# Connect touch sensor and remote control
ts = TouchSensor();   assert ts.connected
rc = RemoteControl(); assert rc.connected

# Initialize button handler
button = Button()

# Turn leds off
Leds.all_off()

def roll(motor, led_group, direction):
    """
    Generate remote control event handler. It rolls given motor into given
    direction (1 for forward, -1 for backward). When motor rolls forward, the
    given led group flashes green, when backward -- red. When motor stops, the
    leds are turned off.

    The on_press function has signature required by RemoteControl class.
    It takes boolean state parameter; True when button is pressed, False
    otherwise.
    """
    def on_press(state):
        if state:
            # Roll when button is pressed
            motor.run_forever(speed_sp=600*direction)
            Leds.set_color(led_group, direction > 0 and Leds.GREEN or Leds.RED)
        else:
            # Stop otherwise
            motor.stop(stop_action='brake')
            Leds.set(led_group, brightness_pct=0)

    return on_press

# Assign event handler to each of the remote buttons
rc.on_red_up    = roll(lmotor, Leds.LEFT,   1)
rc.on_red_down  = roll(lmotor, Leds.LEFT,  -1)
rc.on_blue_up   = roll(rmotor, Leds.RIGHT,  1)
rc.on_blue_down = roll(rmotor, Leds.RIGHT, -1)

# Enter event processing loop
while not button.any():
    rc.process()

    # Backup when bumped an obstacle
    if ts.is_pressed:
        Sound.speak('Oops, excuse me!')

        for motor in (lmotor, rmotor):
            motor.stop(stop_action='brake')

        # Turn red lights on
        for led in (Leds.LEFT, Leds.RIGHT):
            Leds.set_color(led, Leds.RED)

        # Run both motors backwards for 0.5 seconds
        for motor in (lmotor, rmotor):
            motor.run_timed(speed_sp=-600, time_sp=500)

        # Wait 0.5 seconds while motors are rolling
        sleep(0.5)

        Leds.all_off()

    sleep(0.01)
