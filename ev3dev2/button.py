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

from ev3dev2 import is_micropython
from logging import getLogger

log = getLogger(__name__)

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


if is_micropython():
    import logging
    import signal  # causes keyboard interupt to go to main thread
    import _thread

    from errno import EINTR
    from fcntl import ioctl

    from micropython import const
    from uctypes import addressof
    from uctypes import INT32
    from uctypes import sizeof
    from uctypes import struct
    from uctypes import UINT16
    from uctypes import UINT64


    log = logging.getLogger(__name__)

    # Button key codes
    UP = const(103)
    CENTER = const(28)  # ENTER
    DOWN = const(108)
    RIGHT = const(106)
    LEFT = const(105)
    BACK = const(14)

    # Note, this order is intentional and comes from the EV3-G software
    _BUTTONS = (UP, CENTER, DOWN, RIGHT, LEFT, BACK)

    _BUTTON_DEV = '/dev/input/by-path/platform-gpio_keys-event'


    # stuff from linux/input.h and linux/input-event-codes.h

    _EV_KEY = 0x01
    _KEY_MAX = 0x2FF
    _KEY_BUF_LEN = (_KEY_MAX + 7) // 8
    _EVIOCGKEY = 2 << (14 + 8 + 8) | _KEY_BUF_LEN << (8 + 8) | ord('E') << 8 | 0x18

    _input_event = {
        'time': UINT64 | 0,  # struct timeval
        'type': UINT16 | 8,
        'code': UINT16 | 10,
        'value': INT32 | 12,
    }


    def _test_bit(buf, index):
        byte = buf[int(index >> 3)]
        bit = byte & (1 << (index % 8))
        return bool(bit)


    class State():
        """
        State constants for use in :py:meth:`Buttons.test` and
        :py:meth:`Button.wait`.
        """

        # The button is currently released (not pressed)
        RELEASED = 0

        # The button is currently pressed
        PRESSED = 1

        # The button was pressed and released since the last time we checked the
        # bumped state (or since the beginning of the program on the first check)
        BUMPED = 2


    class ButtonBase(object):
        """
        Object that represents the buttons on the EV3
        """

        def __init__(self):
            self._devnode = open(_BUTTON_DEV, 'b')
            self._fd = self._devnode.fileno()
            self._buffer = bytearray(_KEY_BUF_LEN)
            self._lock = _thread.allocate_lock()
            self._state = {
                UP: 0,
                DOWN: 0,
                LEFT: 0,
                RIGHT: 0,
                CENTER: 0,
                BACK: 0,
            }
            self._bumped = {
                UP: False,
                DOWN: False,
                LEFT: False,
                RIGHT: False,
                CENTER: False,
                BACK: False,
            }

            # taking advantage of the fact that micropython kills thread on exit
            _thread.start_new_thread(self._read_event, ())

        # dwalton
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
            """
            Returns list of pressed buttons
            """
            ioctl(self._fd, _EVIOCGKEY, self._buffer, mut=True)

            pressed = []
            for b in _BUTTONS:
                if _test_bit(self._buffer, b):
                    pressed.append(b)
            return pressed

        # ===========
        # dlech start
        # ===========
        def _read_event(self):
            data = bytearray(sizeof(_input_event))
            event = struct(addressof(data), _input_event)
            while True:
                try:
                    self._devnode.readinto(data)
                except OSError as err:
                    if err.args[0] == EINTR:
                        continue
                    raise err
                if event.type != _EV_KEY:
                    continue
                if event.code in _BUTTONS:
                    with self._lock:
                        self._state[event.code] = event.value
                        if not event.value:
                            # key was released, so we have bump
                            self._bumped[event.code] = True

        def read(self):
            """
            Returns a button if any button is pressed.

            If more than one button is pressed, the order of precedence is
            :py:const:`UP`, :py:const:`CENTER`, :py:const:`DOWN`,
            :py:const:`RIGHT`, :py:const:`LEFT`, :py:const:`BACK`.
            """
            with self._lock:
                ioctl(self._fd, _EVIOCGKEY, self._buffer, mut=True)

                for b in _BUTTONS:
                    if _test_bit(self._buffer, b):
                        return b

                return None

        def test(self, buttons, state):
            """
            Compares a list of buttons to a state.

            Parameters:
                buttons (tuple): List of buttons to check
                state (State): The state

            Returns:
                The first button from the list with the given state, or ``None``
                if no button has that state

            .. note:: Since the ``buttons`` parameter expects a tuple, if you are
                only checking one button, it still must be written as a tuple. For
                example::

                    buttons.test((CENTER,), State.BUMPED)
            """
            with self._lock:
                if state == State.RELEASED:
                    for b in buttons:
                        if not self._state[b]:
                            return b
                elif state == State.PRESSED:
                    for b in buttons:
                        if self._state[b]:
                            return b
                else:
                    for b in buttons:
                        if self._bumped[b]:
                            self._bumped[b] = False
                            return b
                return None

        def wait(self, buttons, state):
            """
            Waits until at least one button matches a state.

            Parameters:
                buttons (tuple): List of buttons to check
                state (State): The state

            Returns:
                The first button from the list with the given state, or ``None``
                if no button has that state

            .. note:: Since the ``buttons`` parameter expects a tuple, if you are
                only checking one button, it still must be written as a tuple. For
                example::

                    buttons.wait((CENTER,), State.PRESSED)
            """
            while not self.test(buttons, state):
                pass
        # =========
        # dlech end
        # =========


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
            """
            Wait for the button to be pressed down.
            """
            return self._wait(buttons, [], timeout_ms)

        def wait_for_released(self, buttons, timeout_ms=None):
            """
            Wait for the button to be released.
            """
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

    # dwalton
    class Button(ButtonBase):
        """
        EV3 Buttons
        """

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
            return UP in self.buttons_pressed

        @property
        def down(self):
            """
            Check if 'down' button is pressed.
            """
            return DOWN in self.buttons_pressed

        @property
        def left(self):
            """
            Check if 'left' button is pressed.
            """
            return LEFT in self.buttons_pressed

        @property
        def right(self):
            """
            Check if 'right' button is pressed.
            """
            return RIGHT in self.buttons_pressed

        @property
        def enter(self):
            """
            Check if 'enter' button is pressed.
            """
            return CENTER in self.buttons_pressed

        @property
        def backspace(self):
            """
            Check if 'backspace' button is pressed.
            """
            return BACK in self.buttons_pressed

# dwalton
else:
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
            """
            Wait for the button to be pressed down.
            """
            return self._wait(buttons, [], timeout_ms)

        def wait_for_released(self, buttons, timeout_ms=None):
            """
            Wait for the button to be released.
            """
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
        EV3 Buttons
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
