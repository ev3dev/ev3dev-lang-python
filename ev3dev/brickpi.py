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
import smbus


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

    @staticmethod
    def mix_colors(blue):
        Leds.blue_one.brightness_pct = blue
        Leds.blue_two.brightness_pct = blue

    @staticmethod
    def set_blue(pct):
        Leds.mix_colors(blue=1 * pct)

    @staticmethod
    def blue_on():
        Leds.set_blue(1)

    @staticmethod
    def all_off():
        Leds.blue_one.brightness = 0
        Leds.blue_two.brightness = 0


# ~autogen


class PowerSupply(object):

    @property
    def measured_voltage(self):
        """
        The measured voltage that the battery is supplying (in microvolts)

        Reads the digital output code of the MCP3021 chip on the BrickPi+ over i2c.
        Some bit operation magic to get a voltage floating number.

        If this doesnt work try this on the command line: i2cdetect -y 1
        The 1 in there is the bus number, same as in bus = smbus.SMBus(1)
        Google the resulting error.

        :return int: voltage in microvolts
        """

        try:
                bus = smbus.SMBus(1)            # SMBUS 1 because we're using greater than V1.
                address = 0x48
                # time.sleep(0.1) #Is this necessary?

                # read data from i2c bus. the 0 command is mandatory for the protocol but not used in this chip.
                data = bus.read_word_data(address, 0)

                # from this data we need the last 4 bites and the first 6.
                last_4 = data & 0b1111 # using a byte mask
                first_6 = data >> 10 # left shift 10 because data is 16 bits

                # together they make the voltage conversion ratio
                # to make it all easier the last_4 bits are most significant :S
                vdata = ((last_4 << 6) | first_6)

                # Now we can calculate the battery voltage like so:
                voltage = vdata * 0.0179 * 1000000    # This is an empirical number for voltage conversion.

                return voltage

        except:
                return 0