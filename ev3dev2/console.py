# -----------------------------------------------------------------------------
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
    for cursor positioning, text color, and resetting the screen. Supports changing
    the console font using standard system fonts.
    """

    def __init__(self, font="Lat15-TerminusBold24x12"):
        """
        Construct the Console instance, optionally with a font name specified.

        Parameter:

        - `font` (string): Font name, as found in `/usr/share/consolefonts/`

        """
        self._font = None
        self.set_font(font, False)  # don't reset the screen during construction

    def text_at(self, text, column=1, row=1, reset_console=False, inverse=False, alignment="L"):
        """
        Display `text` (string) at grid position (`column`, `row`).
        Note that the grid locations are 1-based (not 0-based).

        Depending on the font, the number of columns and rows supported by the EV3 LCD console
        can vary. Large fonts support as few as 11 columns and 4 rows, while small fonts support
        44 columns and 21 rows. The default font for the Console() class results in a grid that
        is 14 columns and 5 rows.

        Using the `inverse=True` parameter will display the `text` with more emphasis and contrast,
        as the background of the text will be black, and the foreground is white. Using inverse
        can help in certain situations, such as to indicate when a color sensor senses
        black, or the gyro sensor is pointing to zero.

        Use the `alignment` parameter to enable the function to align the `text` differently to the
        column/row values passed-in. Use `L` for left-alignment (default), where the first character
        in the `text` will show at the column/row position. Use `R` for right-alignment, where the
        last character will show at the column/row position. Use `C` for center-alignment, where the
        text string will centered at the column/row position (as close as possible using integer
        division--odd-length text string will center better than even-length).

        Parameters:

        - `text` (string): Text to display
        - `column` (int): LCD column position to start the text (1 = left column);
          text will wrap when it reaches the right edge
        - `row` (int): LCD row position to start the text (1 = top row)
        - `reset_console` (bool): ``True`` to reset the EV3 LCD console before showing
          the text; default is ``False``
        - `inverse` (bool): ``True`` for white on black, otherwise black on white;
          default is ``False``
        - `alignment` (string): Align the `text` horizontally. Use `L` for left-alignment (default),
          `R` for right-alignment, or `C` for center-alignment

        """

        if reset_console:
            self.reset_console()

        if alignment == "R":
            column = column - len(text) + 1
        elif alignment == "C":
            column -= len(text) // 2

        if inverse:
            text = "\x1b[7m{}\x1b[m".format(text)

        print("\x1b[{};{}H{}".format(row, column, text), end='')

    def set_font(self, font, reset_console=True):
        """
        Set the EV3 LCD console font and optionally reset the EV3 LCD console
        to clear it and turn off the cursor.

        Parameters:

        - `font` (string): Font name, as found in `/usr/share/consolefonts/`
        - `reset_console` (bool): ``True`` to reset the EV3 LCD console
          after the font change; default is ``True``

        """
        if font is not None and font != self._font:
            self._font = font
            os.system("setfont {}".format(font))

        if reset_console:
            self.reset_console()

    def show_cursor(self, on=False):
        """
        Use ANSI codes to turn the EV3 LCD console cursor on or off.

        Parameter:

        - `on` (bool): ``True`` to turn on the cursor; default is ``False``

        """
        print("\x1b[?25{}".format('h' if on else 'l'), end='')

    def clear_to_eol(self, column=None, row=None):
        """
        Clear to the end of line from the `column` and `row` position
        on the EV3 LCD console. Default to current cursor position.

        Parameters:

        - `column` (int): LCD column position to move to before clearing
        - `row` (int): LCD row position to move to before clearing

        """
        if column is not None and row is not None:
            print("\x1b[{};{}H".format(row, column), end='')
        print("\x1b[K", end='')

    def reset_console(self):
        """
        Use ANSI codes to clear the EV3 LCD console, move the cursor to 1,1, then turn off the cursor.
        """
        print("\x1b[2J\x1b[H", end='')
        self.show_cursor(False)
