# -----------------------------------------------------------------------------
# Copyright (c) 2015 Ralph Hempel <rhempel@hempeldesigngroup.com>
# Copyright (c) 2015 Anton Vanhoucke <antonvh@gmail.com>
# Copyright (c) 2015 Denis Demidov <dennis.demidov@gmail.com>
# Copyright (c) 2015 Eric Pascual <eric@pobot.org>
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

import sys

if sys.version_info < (3,4):
    raise SystemError('Must be using Python 3.4 or higher')

from ev3dev2 import Device


class PowerSupply(Device):
    """
    A generic interface to read data from the system's power_supply class.
    Uses the built-in legoev3-battery if none is specified.
    """

    SYSTEM_CLASS_NAME = 'power_supply'
    SYSTEM_DEVICE_NAME_CONVENTION = '*'
    __slots__ = [
    '_measured_current',
    '_measured_voltage',
    '_max_voltage',
    '_min_voltage',
    '_technology',
    '_type',
    ]

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):

        if address is not None:
            kwargs['address'] = address
        super(PowerSupply, self).__init__(self.SYSTEM_CLASS_NAME, name_pattern, name_exact, **kwargs)

        self._measured_current = None
        self._measured_voltage = None
        self._max_voltage = None
        self._min_voltage = None
        self._technology = None
        self._type = None

    @property
    def measured_current(self):
        """
        The measured current that the battery is supplying (in microamps)
        """
        self._measured_current, value = self.get_attr_int(self._measured_current, 'current_now')
        return value

    @property
    def measured_voltage(self):
        """
        The measured voltage that the battery is supplying (in microvolts)
        """
        self._measured_voltage, value = self.get_attr_int(self._measured_voltage, 'voltage_now')
        return value

    @property
    def max_voltage(self):
        """
        """
        self._max_voltage, value = self.get_attr_int(self._max_voltage, 'voltage_max_design')
        return value

    @property
    def min_voltage(self):
        """
        """
        self._min_voltage, value = self.get_attr_int(self._min_voltage, 'voltage_min_design')
        return value

    @property
    def technology(self):
        """
        """
        self._technology, value = self.get_attr_string(self._technology, 'technology')
        return value

    @property
    def type(self):
        """
        """
        self._type, value = self.get_attr_string(self._type, 'type')
        return value

    @property
    def measured_amps(self):
        """
        The measured current that the battery is supplying (in amps)
        """
        return self.measured_current / 1e6

    @property
    def measured_volts(self):
        """
        The measured voltage that the battery is supplying (in volts)
        """
        return self.measured_voltage / 1e6
