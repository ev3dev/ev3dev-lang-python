#!/usr/bin/env micropython
from time import sleep
from sys import stderr
from os import listdir
from ev3dev2.console import Console
"""
Used to iterate over the system console fonts (in /usr/share/consolefonts) and show the max row/col.

Font names consist of three parameters - codeset, font face and font size. The codeset specifies
what characters will be supported by the font. The font face determines the general look of the font. Each
font face is available in certain possible sizes.

For Codeset clarity, see https://www.systutorials.com/docs/linux/man/5-console-setup/#lbAP

"""


def show_fonts():
    """
    Iterate through all the Latin "1 & 5" fonts, and see how many rows/columns
    the EV3 LCD console can accommodate for each font.
    Note: ``Terminus`` fonts are "thinner"; ``TerminusBold`` and ``VGA`` offer more contrast on the LCD console
    and are thus more readable; the ``TomThumb`` font is waaaaay too small to read!
    """
    console = Console()
    files = [f for f in listdir("/usr/share/consolefonts/") if f.startswith("Lat15") and f.endswith(".psf.gz")]
    files.sort()
    fonts = []
    for font in files:
        console.set_font(font, True)
        console.text_at(font, 1, 1, False, True)
        console.clear_to_eol()
        console.text_at("{}, {}".format(console.columns, console.rows),
                        column=2,
                        row=4,
                        reset_console=False,
                        inverse=False)
        print("{}, {}, \"{}\"".format(console.columns, console.rows, font), file=stderr)
        fonts.append((console.columns, console.rows, font))

    fonts.sort(key=lambda f: (f[0], f[1], f[2]))

    # Paint the screen full of numbers that represent the column number, reversing the even rows
    for cols, rows, font in fonts:
        print(cols, rows, font, file=stderr)
        console.set_font(font, True)
        for row in range(1, rows + 1):
            for col in range(1, cols + 1):
                console.text_at("{}".format(col % 10), col, row, False, (row % 2 == 0))
        console.text_at(font.split(".")[0], 1, 1, False, True)
        console.clear_to_eol()


# Show the fonts; you may want to adjust the ``startswith`` filter to show other codesets.
show_fonts()

sleep(5)
