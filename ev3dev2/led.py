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

import os
import stat
import time
from collections import OrderedDict
from ev3dev2 import get_current_platform, Device

# Import the LED settings, this is platform specific
platform = get_current_platform()

if platform == 'ev3':
    from ev3dev2._platform.ev3 import LEDS, LED_GROUPS, LED_COLORS

elif platform == 'evb':
    from ev3dev2._platform.evb import LEDS, LED_GROUPS, LED_COLORS

elif platform == 'pistorms':
    from ev3dev2._platform.pistorms import LEDS, LED_GROUPS, LED_COLORS

elif platform == 'brickpi':
    from ev3dev2._platform.brickpi import LEDS, LED_GROUPS, LED_COLORS

elif platform == 'brickpi3':
    from ev3dev2._platform.brickpi3 import LEDS, LED_GROUPS, LED_COLORS

elif platform == 'fake':
    from ev3dev2._platform.fake import LEDS, LED_GROUPS, LED_COLORS

else:
    raise Exception("Unsupported platform '%s'" % platform)


class Led(Device):
    """
    Any device controlled by the generic LED driver.
    See https://www.kernel.org/doc/Documentation/leds/leds-class.txt
    for more details.
    """

    SYSTEM_CLASS_NAME = 'leds'
    SYSTEM_DEVICE_NAME_CONVENTION = '*'
    __slots__ = [
    '_max_brightness',
    '_brightness',
    '_triggers',
    '_trigger',
    '_delay_on',
    '_delay_off',
    'desc',
    ]

    def __init__(self,
                 name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False,
                 desc=None, **kwargs):
        super(Led, self).__init__(self.SYSTEM_CLASS_NAME, name_pattern, name_exact, **kwargs)

        self._max_brightness = None
        self._brightness = None
        self._triggers = None
        self._trigger = None
        self._delay_on = None
        self._delay_off = None
        self.desc = desc

    def __str__(self):
        if self.desc:
            return self.desc
        else:
            return Device.__str__(self)

    @property
    def max_brightness(self):
        """
        Returns the maximum allowable brightness value.
        """
        self._max_brightness, value = self.get_attr_int(self._max_brightness, 'max_brightness')
        return value

    @property
    def brightness(self):
        """
        Sets the brightness level. Possible values are from 0 to `max_brightness`.
        """
        self._brightness, value = self.get_attr_int(self._brightness, 'brightness')
        return value

    @brightness.setter
    def brightness(self, value):
        self._brightness = self.set_attr_int(self._brightness, 'brightness', value)

    @property
    def triggers(self):
        """
        Returns a list of available triggers.
        """
        self._triggers, value = self.get_attr_set(self._triggers, 'trigger')
        return value

    @property
    def trigger(self):
        """
        Sets the led trigger. A trigger
        is a kernel based source of led events. Triggers can either be simple or
        complex. A simple trigger isn't configurable and is designed to slot into
        existing subsystems with minimal additional code. Examples are the `ide-disk` and
        `nand-disk` triggers.

        Complex triggers whilst available to all LEDs have LED specific
        parameters and work on a per LED basis. The `timer` trigger is an example.
        The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `on` and `off` time can
        be specified via `delay_{on,off}` attributes in milliseconds.
        You can change the brightness value of a LED independently of the timer
        trigger. However, if you set the brightness value to 0 it will
        also disable the `timer` trigger.
        """
        self._trigger, value = self.get_attr_from_set(self._trigger, 'trigger')
        return value

    @trigger.setter
    def trigger(self, value):
        self._trigger = self.set_attr_string(self._trigger, 'trigger', value)

        # Workaround for ev3dev/ev3dev#225.
        # When trigger is set to 'timer', we need to wait for 'delay_on' and
        # 'delay_off' attributes to appear with correct permissions.
        if value == 'timer':
            for attr in ('delay_on', 'delay_off'):
                path = self._path + '/' + attr

                # Make sure the file has been created:
                for _ in range(5):
                    if os.path.exists(path):
                        break
                    time.sleep(0.2)
                else:
                    raise Exception('"{}" attribute has not been created'.format(attr))

                # Make sure the file has correct permissions:
                for _ in range(5):
                    mode = stat.S_IMODE(os.stat(path)[stat.ST_MODE])
                    if mode & stat.S_IRGRP and mode & stat.S_IWGRP:
                        break
                    time.sleep(0.2)
                else:
                    raise Exception('"{}" attribute has wrong permissions'.format(attr))

    @property
    def delay_on(self):
        """
        The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `on` time can
        be specified via `delay_on` attribute in milliseconds.
        """

        # Workaround for ev3dev/ev3dev#225.
        # 'delay_on' and 'delay_off' attributes are created when trigger is set
        # to 'timer', and destroyed when it is set to anything else.
        # This means the file cache may become outdated, and we may have to
        # reopen the file.
        for retry in (True, False):
            try:
                self._delay_on, value = self.get_attr_int(self._delay_on, 'delay_on')
                return value
            except OSError:
                if retry:
                    self._delay_on = None
                else:
                    raise

    @delay_on.setter
    def delay_on(self, value):
        # Workaround for ev3dev/ev3dev#225.
        # 'delay_on' and 'delay_off' attributes are created when trigger is set
        # to 'timer', and destroyed when it is set to anything else.
        # This means the file cache may become outdated, and we may have to
        # reopen the file.
        for retry in (True, False):
            try:
                self._delay_on = self.set_attr_int(self._delay_on, 'delay_on', value)
                return
            except OSError:
                if retry:
                    self._delay_on = None
                else:
                    raise

    @property
    def delay_off(self):
        """
        The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `off` time can
        be specified via `delay_off` attribute in milliseconds.
        """

        # Workaround for ev3dev/ev3dev#225.
        # 'delay_on' and 'delay_off' attributes are created when trigger is set
        # to 'timer', and destroyed when it is set to anything else.
        # This means the file cache may become outdated, and we may have to
        # reopen the file.
        for retry in (True, False):
            try:
                self._delay_off, value = self.get_attr_int(self._delay_off, 'delay_off')
                return value
            except OSError:
                if retry:
                    self._delay_off = None
                else:
                    raise

    @delay_off.setter
    def delay_off(self, value):
        # Workaround for ev3dev/ev3dev#225.
        # 'delay_on' and 'delay_off' attributes are created when trigger is set
        # to 'timer', and destroyed when it is set to anything else.
        # This means the file cache may become outdated, and we may have to
        # reopen the file.
        for retry in (True, False):
            try:
                self._delay_off = self.set_attr_int(self._delay_off, 'delay_off', value)
                return
            except OSError:
                if retry:
                    self._delay_off = None
                else:
                    raise

    @property
    def brightness_pct(self):
        """
        Returns led brightness as a fraction of max_brightness
        """
        return float(self.brightness) / self.max_brightness

    @brightness_pct.setter
    def brightness_pct(self, value):
        self.brightness = value * self.max_brightness


class Leds(object):

    def __init__(self):
        self.leds = OrderedDict()
        self.led_groups = OrderedDict()
        self.led_colors = LED_COLORS

        for (key, value) in LEDS.items():
            self.leds[key] = Led(name_pattern=value, desc=key)

        for (key, value) in LED_GROUPS.items():
            self.led_groups[key] = []

            for led_name in value:
                self.led_groups[key].append(self.leds[led_name])

    def __str__(self):
        return self.__class__.__name__

    def set_color(self, group, color, pct=1):
        """
        Sets brigthness of leds in the given group to the values specified in
        color tuple. When percentage is specified, brightness of each led is
        reduced proportionally.

        Example::

            my_leds = Leds()
            my_leds.set_color('LEFT', 'AMBER')
        
        With a custom color::

            my_leds = Leds()
            my_leds.set_color('LEFT', (0.5, 0.3))
        """
        # If this is a platform without LEDs there is nothing to do
        if not self.leds:
            return

        color_tuple = color
        if isinstance(color, str):
            assert color in self.led_colors, "%s is an invalid LED color, valid choices are %s" % (color, ','.join(self.led_colors.keys()))
            color_tuple = self.led_colors[color]

        assert group in self.led_groups, "%s is an invalid LED group, valid choices are %s" % (group, ','.join(self.led_groups.keys()))

        for led, value in zip(self.led_groups[group], color_tuple):
            led.brightness_pct = value * pct

    def set(self, group, **kwargs):
        """
        Set attributes for each led in group.

        Example::

            my_leds = Leds()
            my_leds.set_color('LEFT', brightness_pct=0.5, trigger='timer')
        """

        # If this is a platform without LEDs there is nothing to do
        if not self.leds:
            return

        assert group in self.led_groups, "%s is an invalid LED group, valid choices are %s" % (group, ','.join(self.led_groups.keys()))

        for led in self.led_groups[group]:
            for k in kwargs:
                setattr(led, k, kwargs[k])

    def all_off(self):
        """
        Turn all leds off
        """

        # If this is a platform without LEDs there is nothing to do
        if not self.leds:
            return

        for led in self.leds.values():
            led.brightness = 0
