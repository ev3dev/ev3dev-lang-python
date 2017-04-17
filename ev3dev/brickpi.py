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