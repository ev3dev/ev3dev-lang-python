
"""
An assortment of classes modeling specific features of the EVB.
"""

from .core import *


OUTPUT_A = 'outA'
OUTPUT_B = 'outB'
OUTPUT_C = 'outC'
OUTPUT_D = 'outD'

INPUT_1 = 'in1'
INPUT_2 = 'in2'
INPUT_3 = 'in3'
INPUT_4 = 'in4'


class Button(ButtonEVIO):
    """
    EVB Buttons
    """

    _buttons_filename = '/dev/input/by-path/platform-evb-buttons-event'
    _buttons = {
            'up': {'name': _buttons_filename, 'value': 103},
            'down': {'name': _buttons_filename, 'value': 108},
            'left': {'name': _buttons_filename, 'value': 105},
            'right': {'name': _buttons_filename, 'value': 106},
            'enter': {'name': _buttons_filename, 'value': 28},
            'backspace': {'name': _buttons_filename, 'value': 14},
        }

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
