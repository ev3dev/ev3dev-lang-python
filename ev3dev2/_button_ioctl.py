"""LEGO MINDSTORMS EV3 buttons"""

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


class Button():
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

    def _pressed(self):
        """
        Returns list of pressed buttons
        """
        ioctl(self._fd, _EVIOCGKEY, self._buffer, mut=True)

        pressed = []
        for b in _BUTTONS:
            if _test_bit(self._buffer, b):
                pressed.append(b)
        return pressed
