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

import os


class Console():
    """
    A class that represents the EV3 LCD console, which implements ANSI codes
    for cursor positioning, text color, and clearing the screen. Supports changing
    the console font using standard system fonts.
    """

    def __init__(self, font="Lat15-TerminusBold24x12"):
        """
        Construct the Console instance, optionally with a font name specified.
        This also resets the console: clearing it and turning off the cursor.
        Parameter:

        - `font` (string): Font name, as found in `/usr/share/consolefonts/`

        """
        self._font = None
        self.set_font(font)

    def text_at(self, text, column=1, row=1, clear_screen=False, inverse=False):
        """
        Display 'text' (string) starting at grid (column, row).
        Note that the grid locations are 1-based (not 0-based).

        Depending on the font, the EV3 LCD console can show text within 4 to 21 rows, and 11 to 44 columns.
        The default font results in a grid that is 14 columns wide and 5 rows tall.

        Parameters:

        - `text` (string): Text to display
        - `column` (int): LCD column position to start the text (1 = left column);
          text will wrap when it reaches the right edge
        - `row` (int): LCD row position to start the text (1 = top row)
        - `clear_screen` (bool): ``True`` to clear the screen before showing the text; default is ``False``
        - `inverse` (bool): ``True`` for white, otherwise black; default is ``False``

        """

        if clear_screen:
            self.reset_screen()

        if inverse:
            text = "\x1b[7m%s\x1b[m" % (text)

        print("\x1b[%d;%dH%s" % (row, column, text), end='')

    def set_font(self, font):
        """
        Set the LCD console font, clear the screen and turn off the cursor.
        Parameter:

        - `font` (string): Font name, as found in `/usr/share/consolefonts/`

        """
        if font is not None and font != self._font:
            self._font = font
            os.system("setfont %s" % (font))
        self.reset_screen()

    def set_cursor(self, on=False):
        """
        Use ANSI codes to turn LCD console cursor on or off
        Parameter:

        - `on` (bool): ``True`` to turn on the screen cursor; default is ``False``

        """
        # use escape code to turn cursor on or off
        print("\x1b[?25%s" % ('h' if on else 'l'), end='')

    def reset_screen(self):
        """
        Clear the EV3 LCD console using ANSI codes and turn off the cursor.
        """
        print("\x1b[2J\x1b[H", end='')
        self.set_cursor(False)
