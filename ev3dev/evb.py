
"""
An assortment of classes modeling specific features of the EV3 brick.
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

    _buttons = {
            'up': {'name': '/dev/input/by-path/platform-evb-buttons-event', 'value': 103},
            'down': {'name': '/dev/input/by-path/platform-evb-buttons-event', 'value': 108},
            'left': {'name': '/dev/input/by-path/platform-evb-buttons-event', 'value': 105},
            'right': {'name': '/dev/input/by-path/platform-evb-buttons-event', 'value': 106},
            'enter': {'name': '/dev/input/by-path/platform-evb-buttons-event', 'value': 28},
            'backspace': {'name': '/dev/input/by-path/platform-evb-buttons-event', 'value': 14},
        }

    @property
    @staticmethod
    def on_up(state):
        """
        This handler is called by `process()` whenever state of 'up' button
        has changed since last `process()` call. `state` parameter is the new
        state of the button.
        """
        pass

    @staticmethod
    def on_down(state):
        """
        This handler is called by `process()` whenever state of 'down' button
        has changed since last `process()` call. `state` parameter is the new
        state of the button.
        """
        pass

    @staticmethod
    def on_left(state):
        """
        This handler is called by `process()` whenever state of 'left' button
        has changed since last `process()` call. `state` parameter is the new
        state of the button.
        """
        pass

    @staticmethod
    def on_right(state):
        """
        This handler is called by `process()` whenever state of 'right' button
        has changed since last `process()` call. `state` parameter is the new
        state of the button.
        """
        pass

    @staticmethod
    def on_enter(state):
        """
        This handler is called by `process()` whenever state of 'enter' button
        has changed since last `process()` call. `state` parameter is the new
        state of the button.
        """
        pass

    @staticmethod
    def on_backspace(state):
        """
        This handler is called by `process()` whenever state of 'backspace' button
        has changed since last `process()` call. `state` parameter is the new
        state of the button.
        """
        pass

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
