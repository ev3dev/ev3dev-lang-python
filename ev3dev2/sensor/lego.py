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

import time
from ev3dev2.button import ButtonBase
from ev3dev2.sensor import Sensor


class TouchSensor(Sensor):
    """
    Touch Sensor
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    #: Button state
    MODE_TOUCH = 'TOUCH'
    MODES = (MODE_TOUCH,)

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(TouchSensor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-touch', 'lego-nxt-touch'], **kwargs)

    @property
    def is_pressed(self):
        """
        A boolean indicating whether the current touch sensor is being
        pressed.
        """
        self._ensure_mode(self.MODE_TOUCH)
        return self.value(0)

    @property
    def is_released(self):
        return not self.is_pressed

    def _wait(self, wait_for_press, timeout_ms, sleep_ms):
        tic = time.time()

        if sleep_ms:
            sleep_ms = float(sleep_ms/1000)

        # The kernel does not supoort POLLPRI or POLLIN for sensors so we have
        # to drop into a loop and check often
        while True:

            if self.is_pressed == wait_for_press:
                return True

            if timeout_ms is not None and time.time() >= tic + timeout_ms / 1000:
                return False

            if sleep_ms:
                time.sleep(sleep_ms)

    def wait_for_pressed(self, timeout_ms=None, sleep_ms=10):
        return self._wait(True, timeout_ms, sleep_ms)

    def wait_for_released(self, timeout_ms=None, sleep_ms=10):
        return self._wait(False, timeout_ms, sleep_ms)

    def wait_for_bump(self, timeout_ms=None, sleep_ms=10):
        """
        Wait for the touch sensor to be pressed down and then released.
        Both actions must happen within timeout_ms.
        """
        start_time = time.time()

        if self.wait_for_pressed(timeout_ms, sleep_ms):
            if timeout_ms is not None:
                timeout_ms -= int((time.time() - start_time) * 1000)
            return self.wait_for_released(timeout_ms, sleep_ms)

        return False


class ColorSensor(Sensor):
    """
    LEGO EV3 color sensor.
    """

    __slots__ = ['red_max', 'green_max', 'blue_max']

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    #: Reflected light. Red LED on.
    MODE_COL_REFLECT = 'COL-REFLECT'

    #: Ambient light. Blue LEDs on.
    MODE_COL_AMBIENT = 'COL-AMBIENT'

    #: Color. All LEDs rapidly cycling, appears white.
    MODE_COL_COLOR = 'COL-COLOR'

    #: Raw reflected. Red LED on
    MODE_REF_RAW = 'REF-RAW'

    #: Raw Color Components. All LEDs rapidly cycling, appears white.
    MODE_RGB_RAW = 'RGB-RAW'

    #: No color.
    COLOR_NOCOLOR = 0

    #: Black color.
    COLOR_BLACK = 1

    #: Blue color.
    COLOR_BLUE = 2

    #: Green color.
    COLOR_GREEN = 3

    #: Yellow color.
    COLOR_YELLOW = 4

    #: Red color.
    COLOR_RED = 5

    #: White color.
    COLOR_WHITE = 6

    #: Brown color.
    COLOR_BROWN = 7

    MODES = (
      MODE_COL_REFLECT,
      MODE_COL_AMBIENT,
      MODE_COL_COLOR,
      MODE_REF_RAW,
      MODE_RGB_RAW
    )

    COLORS = (
      'NoColor',
      'Black',
      'Blue',
      'Green',
      'Yellow',
      'Red',
      'White',
      'Brown',
    )

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(ColorSensor, self).__init__(address, name_pattern, name_exact, driver_name='lego-ev3-color', **kwargs)

        # See calibrate_white() for more details
        self.red_max = 300
        self.green_max = 300
        self.blue_max = 300

    @property
    def reflected_light_intensity(self):
        """
        Reflected light intensity as a percentage. Light on sensor is red.
        """
        self._ensure_mode(self.MODE_COL_REFLECT)
        return self.value(0)

    @property
    def ambient_light_intensity(self):
        """
        Ambient light intensity. Light on sensor is dimly lit blue.
        """
        self._ensure_mode(self.MODE_COL_AMBIENT)
        return self.value(0)

    @property
    def color(self):
        """
        Color detected by the sensor, categorized by overall value.
          - 0: No color
          - 1: Black
          - 2: Blue
          - 3: Green
          - 4: Yellow
          - 5: Red
          - 6: White
          - 7: Brown
        """
        self._ensure_mode(self.MODE_COL_COLOR)
        return self.value(0)

    @property
    def color_name(self):
        """
        Returns NoColor, Black, Blue, etc
        """
        return self.COLORS[self.color]

    @property
    def raw(self):
        """
        Red, green, and blue components of the detected color, officially in the
        range 0-1020 but the values returned will never be that high. We do not
        yet know why the values returned are low, but pointing the color sensor
        at a well lit sheet of white paper will return values in the 250-400 range.

        If this is an issue, check out the rgb() and calibrate_white() methods.
        """
        self._ensure_mode(self.MODE_RGB_RAW)
        return self.value(0), self.value(1), self.value(2)

    def calibrate_white(self):
        """
        The RGB raw values are on a scale of 0-1020 but you never see a value
        anywhere close to 1020.  This function is designed to be called when
        the sensor is placed over a white object in order to figure out what
        are the maximum RGB values the robot can expect to see.  We will use
        these maximum values to scale future raw values to a 0-255 range in
        rgb().

        If you never call this function red_max, green_max, and blue_max will
        use a default value of 300.  This default was selected by measuring
        the RGB values of a white sheet of paper in a well lit room.

        Note that there are several variables that influence the maximum RGB
        values detected by the color sensor
        - the distance of the color sensor to the white object
        - the amount of light in the room
        - shadows that the robot casts on the sensor
        """
        (self.red_max, self.green_max, self.blue_max) = self.raw

    @property
    def rgb(self):
        """
        Same as raw() but RGB values are scaled to 0-255
        """
        (red, green, blue) = self.raw

        return (min(int((red * 255) / self.red_max), 255),
                min(int((green * 255) / self.green_max), 255),
                min(int((blue * 255) / self.blue_max), 255))

    @property
    def lab(self):
        """
        Return colors in Lab color space
        """
        RGB = [0, 0, 0]
        XYZ = [0, 0, 0]

        for (num, value) in enumerate(self.rgb):
            if value > 0.04045:
                value = pow(((value + 0.055) / 1.055), 2.4)
            else:
                value = value / 12.92

            RGB[num] = value * 100.0

        # http://www.brucelindbloom.com/index.html?Eqn_RGB_XYZ_Matrix.html
        # sRGB
        # 0.4124564  0.3575761  0.1804375
        # 0.2126729  0.7151522  0.0721750
        # 0.0193339  0.1191920  0.9503041
        X = (RGB[0] * 0.4124564) + (RGB[1] * 0.3575761) + (RGB[2] * 0.1804375)
        Y = (RGB[0] * 0.2126729) + (RGB[1] * 0.7151522) + (RGB[2] * 0.0721750)
        Z = (RGB[0] * 0.0193339) + (RGB[1] * 0.1191920) + (RGB[2] * 0.9503041)

        XYZ[0] = X / 95.047   # ref_X =  95.047
        XYZ[1] = Y / 100.0    # ref_Y = 100.000
        XYZ[2] = Z / 108.883  # ref_Z = 108.883

        for (num, value) in enumerate(XYZ):
            if value > 0.008856:
                value = pow(value, (1.0 / 3.0))
            else:
                value = (7.787 * value) + (16 / 116.0)

            XYZ[num] = value

        L = (116.0 * XYZ[1]) - 16
        a = 500.0 * (XYZ[0] - XYZ[1])
        b = 200.0 * (XYZ[1] - XYZ[2])

        L = round(L, 4)
        a = round(a, 4)
        b = round(b, 4)

        return (L, a, b)

    @property
    def hsv(self):
        """
        HSV: Hue, Saturation, Value
        H: position in the spectrum
        S: color saturation ("purity")
        V: color brightness
        """
        (r, g, b) = self.rgb
        maxc = max(r, g, b)
        minc = min(r, g, b)
        v = maxc

        if minc == maxc:
            return 0.0, 0.0, v

        s = (maxc-minc) / maxc
        rc = (maxc-r) / (maxc-minc)
        gc = (maxc-g) / (maxc-minc)
        bc = (maxc-b) / (maxc-minc)

        if r == maxc:
            h = bc-gc
        elif g == maxc:
            h = 2.0+rc-bc
        else:
            h = 4.0+gc-rc

        h = (h/6.0) % 1.0

        return (h, s, v)

    @property
    def hls(self):
        """
        HLS: Hue, Luminance, Saturation
        H: position in the spectrum
        L: color lightness
        S: color saturation
        """
        (r, g, b) = self.rgb
        maxc = max(r, g, b)
        minc = min(r, g, b)
        l = (minc+maxc)/2.0

        if minc == maxc:
            return 0.0, l, 0.0

        if l <= 0.5:
            s = (maxc-minc) / (maxc+minc)
        else:
            if 2.0-maxc-minc == 0:
                s = 0
            else:
                s = (maxc-minc) / (2.0-maxc-minc)

        rc = (maxc-r) / (maxc-minc)
        gc = (maxc-g) / (maxc-minc)
        bc = (maxc-b) / (maxc-minc)

        if r == maxc:
            h = bc-gc
        elif g == maxc:
            h = 2.0+rc-bc
        else:
            h = 4.0+gc-rc

        h = (h/6.0) % 1.0

        return (h, l, s)

    @property
    def red(self):
        """
        Red component of the detected color, in the range 0-1020.
        """
        self._ensure_mode(self.MODE_RGB_RAW)
        return self.value(0)

    @property
    def green(self):
        """
        Green component of the detected color, in the range 0-1020.
        """
        self._ensure_mode(self.MODE_RGB_RAW)
        return self.value(1)

    @property
    def blue(self):
        """
        Blue component of the detected color, in the range 0-1020.
        """
        self._ensure_mode(self.MODE_RGB_RAW)
        return self.value(2)


class UltrasonicSensor(Sensor):
    """
    LEGO EV3 ultrasonic sensor.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    #: Continuous measurement in centimeters.
    MODE_US_DIST_CM = 'US-DIST-CM'

    #: Continuous measurement in inches.
    MODE_US_DIST_IN = 'US-DIST-IN'

    #: Listen.
    MODE_US_LISTEN = 'US-LISTEN'

    #: Single measurement in centimeters.
    MODE_US_SI_CM = 'US-SI-CM'

    #: Single measurement in inches.
    MODE_US_SI_IN = 'US-SI-IN'

    MODES = (
        MODE_US_DIST_CM,
        MODE_US_DIST_IN,
        MODE_US_LISTEN,
        MODE_US_SI_CM,
        MODE_US_SI_IN,
    )

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(UltrasonicSensor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-us', 'lego-nxt-us'], **kwargs)

    @property
    def distance_centimeters_continuous(self):
        """
        Measurement of the distance detected by the sensor,
        in centimeters.

        The sensor will continue to take measurements so
        they are available for future reads.

        Prefer using the equivalent :meth:`UltrasonicSensor.distance_centimeters` property.
        """
        self._ensure_mode(self.MODE_US_DIST_CM)
        return self.value(0) * self._scale('US_DIST_CM')

    @property
    def distance_centimeters_ping(self):
        """
        Measurement of the distance detected by the sensor,
        in centimeters.

        The sensor will take a single measurement then stop
        broadcasting.

        If you use this property too frequently (e.g. every
        100msec), the sensor will sometimes lock up and writing
        to the mode attribute will return an error. A delay of
        250msec between each usage seems sufficient to keep the
        sensor from locking up.
        """
        # This mode is special; setting the mode causes the sensor to send out
        # a "ping", but the mode isn't actually changed.
        self.mode = self.MODE_US_SI_CM
        return self.value(0) * self._scale('US_DIST_CM')

    @property
    def distance_centimeters(self):
        """
        Measurement of the distance detected by the sensor,
        in centimeters.

        Equivalent to :meth:`UltrasonicSensor.distance_centimeters_continuous`.
        """
        return self.distance_centimeters_continuous

    @property
    def distance_inches_continuous(self):
        """
        Measurement of the distance detected by the sensor,
        in inches.

        The sensor will continue to take measurements so
        they are available for future reads.

        Prefer using the equivalent :meth:`UltrasonicSensor.distance_inches` property.
        """
        self._ensure_mode(self.MODE_US_DIST_IN)
        return self.value(0) * self._scale('US_DIST_IN')

    @property
    def distance_inches_ping(self):
        """
        Measurement of the distance detected by the sensor,
        in inches.

        The sensor will take a single measurement then stop
        broadcasting.

        If you use this property too frequently (e.g. every
        100msec), the sensor will sometimes lock up and writing
        to the mode attribute will return an error. A delay of
        250msec between each usage seems sufficient to keep the
        sensor from locking up.
        """
        # This mode is special; setting the mode causes the sensor to send out
        # a "ping", but the mode isn't actually changed.
        self.mode = self.MODE_US_SI_IN
        return self.value(0) * self._scale('US_DIST_IN')

    @property
    def distance_inches(self):
        """
        Measurement of the distance detected by the sensor,
        in inches.

        Equivalent to :meth:`UltrasonicSensor.distance_inches_continuous`.
        """
        return self.distance_inches_continuous

    @property
    def other_sensor_present(self):
        """
        Boolean indicating whether another ultrasonic sensor could
        be heard nearby.
        """
        self._ensure_mode(self.MODE_US_LISTEN)
        return bool(self.value(0))


class GyroSensor(Sensor):
    """
    LEGO EV3 gyro sensor.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    #: Angle
    MODE_GYRO_ANG = 'GYRO-ANG'

    #: Rotational speed
    MODE_GYRO_RATE = 'GYRO-RATE'

    #: Raw sensor value
    MODE_GYRO_FAS = 'GYRO-FAS'

    #: Angle and rotational speed
    MODE_GYRO_G_A = 'GYRO-G&A'

    #: Calibration ???
    MODE_GYRO_CAL = 'GYRO-CAL'

    # Newer versions of the Gyro sensor also have an additional second axis
    # accessible via the TILT-ANGLE and TILT-RATE modes that is not usable
    # using the official EV3-G blocks
    MODE_TILT_ANG = 'TILT-ANGLE'
    MODE_TILT_RATE = 'TILT-RATE'

    MODES = (
        MODE_GYRO_ANG,
        MODE_GYRO_RATE,
        MODE_GYRO_FAS,
        MODE_GYRO_G_A,
        MODE_GYRO_CAL,
        MODE_TILT_ANG,
        MODE_TILT_RATE,
    )

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(GyroSensor, self).__init__(address, name_pattern, name_exact, driver_name='lego-ev3-gyro', **kwargs)
        self._direct = None

    @property
    def angle(self):
        """
        The number of degrees that the sensor has been rotated
        since it was put into this mode.
        """
        self._ensure_mode(self.MODE_GYRO_ANG)
        return self.value(0)

    @property
    def rate(self):
        """
        The rate at which the sensor is rotating, in degrees/second.
        """
        self._ensure_mode(self.MODE_GYRO_RATE)
        return self.value(0)

    @property
    def rate_and_angle(self):
        """
        Angle (degrees) and Rotational Speed (degrees/second).
        """
        self._ensure_mode(self.MODE_GYRO_G_A)
        return self.value(0), self.value(1)

    @property
    def tilt_angle(self):
        self._ensure_mode(self.MODE_TILT_ANG)
        return self.value(0)

    @property
    def tilt_rate(self):
        self._ensure_mode(self.MODE_TILT_RATE)
        return self.value(0)

    def reset(self):
        self._ensure_mode(self.MODE_GYRO_ANG)
        self._direct = self.set_attr_raw(self._direct, 'direct', 17)

    def wait_until_angle_changed_by(self, delta):
        """
        Wait until angle has changed by specified amount.
        """
        assert self.mode in (self.MODE_GYRO_G_A, self.MODE_GYRO_ANG,
                             self.MODE_TILT_ANG),\
            'Gyro mode should be MODE_GYRO_ANG, MODE_GYRO_G_A or MODE_TILT_ANG'
        start_angle = self.value(0)
        while abs(start_angle - self.value(0)) < delta:
            time.sleep(0.01)


class InfraredSensor(Sensor, ButtonBase):
    """
    LEGO EV3 infrared sensor.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    #: Proximity
    MODE_IR_PROX = 'IR-PROX'

    #: IR Seeker
    MODE_IR_SEEK = 'IR-SEEK'

    #: IR Remote Control
    MODE_IR_REMOTE = 'IR-REMOTE'

    #: IR Remote Control. State of the buttons is coded in binary
    MODE_IR_REM_A = 'IR-REM-A'

    #: Calibration ???
    MODE_IR_CAL = 'IR-CAL'

    MODES = (
      MODE_IR_PROX,
      MODE_IR_SEEK,
      MODE_IR_REMOTE,
      MODE_IR_REM_A,
      MODE_IR_CAL
    )

    # The following are all of the various combinations of button presses for
    # the remote control.  The key/index is the number that will be written in
    # the attribute file to indicate what combination of buttons are currently
    # pressed.
    _BUTTON_VALUES = {
            0: [],
            1: ['top_left'],
            2: ['bottom_left'],
            3: ['top_right'],
            4: ['bottom_right'],
            5: ['top_left', 'top_right'],
            6: ['top_left', 'bottom_right'],
            7: ['bottom_left', 'top_right'],
            8: ['bottom_left', 'bottom_right'],
            9: ['beacon'],
            10: ['top_left', 'bottom_left'],
            11: ['top_right', 'bottom_right']
            }

    _BUTTONS = ('top_left', 'bottom_left', 'top_right', 'bottom_right', 'beacon')

    # Button codes for doing rapid check of remote status
    NO_BUTTON = 0
    TOP_LEFT = 1
    BOTTOM_LEFT = 2
    TOP_RIGHT = 3
    BOTTOM_RIGHT = 4
    TOP_LEFT_TOP_RIGHT = 5
    TOP_LEFT_BOTTOM_RIGHT = 6
    BOTTOM_LEFT_TOP_RIGHT = 7
    BOTTOM_LEFT_BOTTOM_RIGHT = 8
    BEACON = 9
    TOP_LEFT_BOTTOM_LEFT = 10
    TOP_RIGHT_BOTTOM_RIGHT = 11

    #: Handler for top-left button events on channel 1. See :meth:`InfraredSensor.process`.
    on_channel1_top_left = None
    #: Handler for bottom-left button events on channel 1. See :meth:`InfraredSensor.process`.
    on_channel1_bottom_left = None
    #: Handler for top-right button events on channel 1. See :meth:`InfraredSensor.process`.
    on_channel1_top_right = None
    #: Handler for bottom-right button events on channel 1. See :meth:`InfraredSensor.process`.
    on_channel1_bottom_right = None
    #: Handler for beacon button events on channel 1. See :meth:`InfraredSensor.process`.
    on_channel1_beacon = None

    #: Handler for top-left button events on channel 2. See :meth:`InfraredSensor.process`.
    on_channel2_top_left = None
    #: Handler for bottom-left button events on channel 2. See :meth:`InfraredSensor.process`.
    on_channel2_bottom_left = None
    #: Handler for top-right button events on channel 2. See :meth:`InfraredSensor.process`.
    on_channel2_top_right = None
    #: Handler for bottom-right button events on channel 2. See :meth:`InfraredSensor.process`.
    on_channel2_bottom_right = None
    #: Handler for beacon button events on channel 2. See :meth:`InfraredSensor.process`.
    on_channel2_beacon = None

    #: Handler for top-left button events on channel 3. See :meth:`InfraredSensor.process`.
    on_channel3_top_left = None
    #: Handler for bottom-left button events on channel 3. See :meth:`InfraredSensor.process`.
    on_channel3_bottom_left = None
    #: Handler for top-right button events on channel 3. See :meth:`InfraredSensor.process`.
    on_channel3_top_right = None
    #: Handler for bottom-right button events on channel 3. See :meth:`InfraredSensor.process`.
    on_channel3_bottom_right = None
    #: Handler for beacon button events on channel 3. See :meth:`InfraredSensor.process`.
    on_channel3_beacon = None

    #: Handler for top-left button events on channel 4. See :meth:`InfraredSensor.process`.
    on_channel4_top_left = None
    #: Handler for bottom-left button events on channel 4. See :meth:`InfraredSensor.process`.
    on_channel4_bottom_left = None
    #: Handler for top-right button events on channel 4. See :meth:`InfraredSensor.process`.
    on_channel4_top_right = None
    #: Handler for bottom-right button events on channel 4. See :meth:`InfraredSensor.process`.
    on_channel4_bottom_right = None
    #: Handler for beacon button events on channel 4. See :meth:`InfraredSensor.process`.
    on_channel4_beacon = None

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(InfraredSensor, self).__init__(address, name_pattern, name_exact, driver_name='lego-ev3-ir', **kwargs)

    def _normalize_channel(self, channel):
        assert channel >= 1 and channel <= 4, "channel is %s, it must be 1, 2, 3, or 4" % channel
        channel = max(1, min(4, channel)) - 1
        return channel

    @property
    def proximity(self):
        """
        A measurement of the distance between the sensor and the remote,
        as a percentage. 100% is approximately 70cm/27in.
        """
        self._ensure_mode(self.MODE_IR_PROX)
        return self.value(0)

    def heading(self, channel=1):
        """
        Returns heading (-25, 25) to the beacon on the given channel.
        """
        self._ensure_mode(self.MODE_IR_SEEK)
        channel = self._normalize_channel(channel)
        return self.value(channel * 2)

    def distance(self, channel=1):
        """
        Returns distance (0, 100) to the beacon on the given channel.
        Returns None when beacon is not found.
        """
        self._ensure_mode(self.MODE_IR_SEEK)
        channel = self._normalize_channel(channel)
        ret_value = self.value((channel * 2) + 1)

        # The value will be -128 if no beacon is found, return None instead
        return None if ret_value == -128 else ret_value

    def heading_and_distance(self, channel=1):
        """
        Returns heading and distance to the beacon on the given channel as a
        tuple.
        """
        return (self.heading(channel), self.distance(channel))

    def top_left(self, channel=1):
        """
        Checks if ``top_left`` button is pressed.
        """
        return 'top_left' in self.buttons_pressed(channel)

    def bottom_left(self, channel=1):
        """
        Checks if ``bottom_left`` button is pressed.
        """
        return 'bottom_left' in self.buttons_pressed(channel)

    def top_right(self, channel=1):
        """
        Checks if ``top_right`` button is pressed.
        """
        return 'top_right' in self.buttons_pressed(channel)

    def bottom_right(self, channel=1):
        """
        Checks if ``bottom_right`` button is pressed.
        """
        return 'bottom_right' in self.buttons_pressed(channel)

    def beacon(self, channel=1):
        """
        Checks if ``beacon`` button is pressed.
        """
        return 'beacon' in self.buttons_pressed(channel)

    def buttons_pressed(self, channel=1):
        """
        Returns list of currently pressed buttons.
        """
        self._ensure_mode(self.MODE_IR_REMOTE)
        channel = self._normalize_channel(channel)
        return self._BUTTON_VALUES.get(self.value(channel), [])

    def process(self):
        """
        Check for currenly pressed buttons. If the new state differs from the
        old state, call the appropriate button event handlers.

        To use the on_channel1_top_left, etc handlers your program would do something like:
        
        .. code:: python

            def top_left_channel_1_action(state):
                print("top left on channel 1: %s" % state)

            def bottom_right_channel_4_action(state):
                print("bottom right on channel 4: %s" % state)

            ir = InfraredSensor()
            ir.on_channel1_top_left = top_left_channel_1_action
            ir.on_channel4_bottom_right = bottom_right_channel_4_action

            while True:
                ir.process()
                time.sleep(0.01)
        
        """
        new_state = []
        state_diff = []

        for channel in range(1,5):

            for button in self.buttons_pressed(channel):
                new_state.append((button, channel))

                # Key was not pressed before but now is pressed
                if (button, channel) not in self._state:
                    state_diff.append((button, channel))

            # Key was pressed but is no longer pressed
            for button in self._BUTTONS:
                if (button, channel) not in new_state and (button, channel) in self._state:
                    state_diff.append((button, channel))

        old_state = self._state
        self._state = new_state

        for (button, channel) in state_diff:
            handler = getattr(self, 'on_channel' + str(channel) + '_' + button )

            if handler is not None:
                handler((button, channel) in new_state)

        if self.on_change is not None and state_diff:
            self.on_change([(button, channel, button in new_state) for (button, channel) in state_diff])


class SoundSensor(Sensor):
    """
    LEGO NXT Sound Sensor
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    #: Sound pressure level. Flat weighting
    MODE_DB = 'DB'

    #: Sound pressure level. A weighting
    MODE_DBA = 'DBA'

    MODES = (
      MODE_DB,
      MODE_DBA,
    )

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(SoundSensor, self).__init__(address, name_pattern, name_exact, driver_name='lego-nxt-sound', **kwargs)

    @property
    def sound_pressure(self):
        """
        A measurement of the measured sound pressure level, as a
        percent. Uses a flat weighting.
        """
        self._ensure_mode(self.MODE_DB)
        return self.value(0) * self._scale('DB')

    @property
    def sound_pressure_low(self):
        """
        A measurement of the measured sound pressure level, as a
        percent. Uses A-weighting, which focuses on levels up to 55 dB.
        """
        self._ensure_mode(self.MODE_DBA)
        return self.value(0) * self._scale('DBA')


class LightSensor(Sensor):
    """
    LEGO NXT Light Sensor
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    #: Reflected light. LED on
    MODE_REFLECT = 'REFLECT'

    #: Ambient light. LED off
    MODE_AMBIENT = 'AMBIENT'

    MODES = (
      MODE_REFLECT,
      MODE_AMBIENT,
    )

    def __init__(self, address=None, name_pattern=SYSTEM_DEVICE_NAME_CONVENTION, name_exact=False, **kwargs):
        super(LightSensor, self).__init__(address, name_pattern, name_exact, driver_name='lego-nxt-light', **kwargs)

    @property
    def reflected_light_intensity(self):
        """
        A measurement of the reflected light intensity, as a percentage.
        """
        self._ensure_mode(self.MODE_REFLECT)
        return self.value(0) * self._scale('REFLECT')

    @property
    def ambient_light_intensity(self):
        """
        A measurement of the ambient light intensity, as a percentage.
        """
        self._ensure_mode(self.MODE_AMBIENT)
        return self.value(0) * self._scale('AMBIENT')
