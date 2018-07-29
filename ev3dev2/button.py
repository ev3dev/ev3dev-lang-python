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

import array
import time
import logging
from . import get_current_platform, library_load_warning_message

log = logging.getLogger(__name__)

try:
    # This is a linux-specific module.
    # It is required by the Button class, but failure to import it may be
    # safely ignored if one just needs to run API tests on Windows.
    import fcntl
except ImportError:
    log.warning(library_load_warning_message("fcntl", "Button"))

try:
    # This is a linux-specific module.
    # It is required by the Button class, but failure to import it may be
    # safely ignored if one just needs to run API tests on Windows.
    import evdev
except ImportError:
    log.warning(library_load_warning_message("evdev", "Button"))


# Import the button filenames, this is platform specific
platform = get_current_platform()

if platform == 'ev3':
    from ._platform.ev3 import BUTTONS_FILENAME, EVDEV_DEVICE_NAME

elif platform == 'evb':
    from ._platform.evb import BUTTONS_FILENAME, EVDEV_DEVICE_NAME

elif platform == 'pistorms':
    from ._platform.pistorms import BUTTONS_FILENAME, EVDEV_DEVICE_NAME

elif platform == 'brickpi':
    from ._platform.brickpi import BUTTONS_FILENAME, EVDEV_DEVICE_NAME

elif platform == 'brickpi3':
    from ._platform.brickpi3 import BUTTONS_FILENAME, EVDEV_DEVICE_NAME

elif platform == 'fake':
    from ._platform.fake import BUTTONS_FILENAME, EVDEV_DEVICE_NAME

else:
    raise Exception("Unsupported platform '%s'" % platform)


class MissingButton(Exception):
    pass


class ButtonBase(object):
    """
    Abstract button interface.
    """
    _state = set([])

    def __str__(self):
        return self.__class__.__name__

    @staticmethod
    def on_change(changed_buttons):
        """
        This handler is called by `process()` whenever state of any button has
        changed since last `process()` call. `changed_buttons` is a list of
        tuples of changed button names and their states.
        """
        pass

    def any(self):
        """
        Checks if any button is pressed.
        """
        return bool(self.buttons_pressed)

    def check_buttons(self, buttons=[]):
        """
        Check if currently pressed buttons exactly match the given list.
        """
        return set(self.buttons_pressed) == set(buttons)

    @property
    def evdev_device(self):
        """
        Return our corresponding evdev device object
        """
        devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]

        for device in devices:
            if device.name == self.evdev_device_name:
                return device

        raise Exception("%s: could not find evdev device '%s'" % (self, self.evdev_device_name))

    def process(self, new_state=None):
        """
        Check for currenly pressed buttons. If the new state differs from the
        old state, call the appropriate button event handlers.
        """
        if new_state is None:
            new_state = set(self.buttons_pressed)
        old_state = self._state
        self._state = new_state

        state_diff = new_state.symmetric_difference(old_state)
        for button in state_diff:
            handler = getattr(self, 'on_' + button)

            if handler is not None:
                handler(button in new_state)

        if self.on_change is not None and state_diff:
            self.on_change([(button, button in new_state) for button in state_diff])

    def process_forever(self):
        for event in self.evdev_device.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                self.process()

    @property
    def buttons_pressed(self):
        raise NotImplementedError()

    def _wait(self, wait_for_button_press, wait_for_button_release, timeout_ms):
        tic = time.time()

        # wait_for_button_press/release can be a list of buttons or a string
        # with the name of a single button.  If it is a string of a single
        # button convert that to a list.
        if isinstance(wait_for_button_press, str):
            wait_for_button_press = [wait_for_button_press, ]

        if isinstance(wait_for_button_release, str):
            wait_for_button_release = [wait_for_button_release, ]

        for event in self.evdev_device.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                all_pressed = True
                all_released = True
                pressed = self.buttons_pressed

                for button in wait_for_button_press:
                    if button not in pressed:
                        all_pressed = False
                        break

                for button in wait_for_button_release:
                    if button in pressed:
                        all_released = False
                        break

                if all_pressed and all_released:
                    return True

                if timeout_ms is not None and time.time() >= tic + timeout_ms / 1000:
                    return False

    def wait_for_pressed(self, buttons, timeout_ms=None):
        return self._wait(buttons, [], timeout_ms)

    def wait_for_released(self, buttons, timeout_ms=None):
        return self._wait([], buttons, timeout_ms)

    def wait_for_bump(self, buttons, timeout_ms=None):
        """
        Wait for the button to be pressed down and then released.
        Both actions must happen within timeout_ms.
        """
        start_time = time.time()

        if self.wait_for_pressed(buttons, timeout_ms):
            if timeout_ms is not None:
                timeout_ms -= int((time.time() - start_time) * 1000)
            return self.wait_for_released(buttons, timeout_ms)

        return False


class ButtonEVIO(ButtonBase):
    """
    Provides a generic button reading mechanism that works with event interface
    and may be adapted to platform specific implementations.

    This implementation depends on the availability of the EVIOCGKEY ioctl
    to be able to read the button state buffer. See Linux kernel source
    in /include/uapi/linux/input.h for details.
    """

    KEY_MAX = 0x2FF
    KEY_BUF_LEN = int((KEY_MAX + 7) / 8)
    EVIOCGKEY = (2 << (14 + 8 + 8) | KEY_BUF_LEN << (8 + 8) | ord('E') << 8 | 0x18)

    _buttons = {}

    def __init__(self):
        ButtonBase.__init__(self)
        self._file_cache = {}
        self._buffer_cache = {}

        for b in self._buttons:
            name = self._buttons[b]['name']

            if name is None:
                raise MissingButton("Button '%s' is not available on this platform" % b)

            if name not in self._file_cache:
                self._file_cache[name] = open(name, 'rb', 0)
                self._buffer_cache[name] = array.array('B', [0] * self.KEY_BUF_LEN)

    def _button_file(self, name):
        return self._file_cache[name]

    def _button_buffer(self, name):
        return self._buffer_cache[name]

    @property
    def buttons_pressed(self):
        """
        Returns list of names of pressed buttons.
        """
        for b in self._buffer_cache:
            fcntl.ioctl(self._button_file(b), self.EVIOCGKEY, self._buffer_cache[b])

        pressed = []
        for k, v in self._buttons.items():
            buf = self._buffer_cache[v['name']]
            bit = v['value']

            if bool(buf[int(bit / 8)] & 1 << bit % 8):
                pressed.append(k)

        return pressed


class Button(ButtonEVIO):
    """
    EVB Buttons
    """

    _buttons = {
            'up': {'name': BUTTONS_FILENAME, 'value': 103},
            'down': {'name': BUTTONS_FILENAME, 'value': 108},
            'left': {'name': BUTTONS_FILENAME, 'value': 105},
            'right': {'name': BUTTONS_FILENAME, 'value': 106},
            'enter': {'name': BUTTONS_FILENAME, 'value': 28},
            'backspace': {'name': BUTTONS_FILENAME, 'value': 14},
        }
    evdev_device_name = EVDEV_DEVICE_NAME

    '''
    These handlers are called by `process()` whenever state of 'up', 'down',
    etc buttons have changed since last `process()` call
    '''
    on_up = None
    on_down = None
    on_left = None
    on_right = None
    on_enter = None
    on_backspace = None

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
