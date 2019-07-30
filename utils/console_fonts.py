#!/usr/bin/env micropython
from time import sleep
from sys import stderr, stdin
from os import listdir
from ev3dev2.console import Console

"""
Used to iterate over the system console fonts (in /usr/share/consolefonts) and calculate the max row/col
position by moving the cursor to 50, 50 and asking the LCD for the actual cursor position
where it ends up (the EV3 LCD console driver prevents the cursor from positioning off-screen).

The font specification consists of three parameters - codeset, font face and font size. The codeset specifies
what characters will be supported by the font. The font face determines the general look of the font. Each
font face is available in certain possible sizes.

For Codeset clarity, see https://www.systutorials.com/docs/linux/man/5-console-setup/#lbAP

"""


def calc_fonts():
    """
    Iterate through all the Latin "1 & 5" fonts, and use ANSI escape sequences to see how many rows/columns
    the EV3 LCD console can accommodate for each font
    """
    console = Console()

    files = [f for f in listdir("/usr/share/consolefonts/") if f.startswith("Lat15") and f.endswith(".psf.gz")]
    files.sort()
    for font in files:
        console.set_font(font, True)

        # position cursor at 50, 50, and ask the console to report its actual cursor position
        console.text_at("\x1b[6n", 50, 50, False)
        console.text_at(font, 1, 1, False, True)
        console.clear_to_eol()

        # now, read the console response of the actual cursor position, in the form of esc[rr;ccR
        # requires pressing the center button on the EV3 for each read
        dims = ''
        while True:
            ch = stdin.read(1)
            if ch == '\x1b' or ch == '[' or ch == '\r' or ch == '\n':
                continue
            if ch == 'R':
                break
            dims += str(ch)
        (rows, cols) = dims.split(";")
        print("({}, {}, \"{}\"),".format(rows, cols, font), file=stderr)
        sleep(.5)


def show_fonts():
    """
    Iterate over the known Latin "1 & 5" fonts and display each on the EV3 LCD console.
    Note: `Terminus` fonts are "thinner"; `TerminusBold` and `VGA` offer more contrast on the LCD console
    and are thus more readable; the `TomThumb` font is waaaaay too small to read!
    """
    # Create a list of tuples with calulated rows, columns, font filename
    fonts = [
        (4, 11, "Lat15-Terminus32x16.psf.gz"),
        (4, 11, "Lat15-TerminusBold32x16.psf.gz"),
        (4, 11, "Lat15-VGA28x16.psf.gz"),
        (4, 11, "Lat15-VGA32x16.psf.gz"),
        (4, 12, "Lat15-Terminus28x14.psf.gz"),
        (4, 12, "Lat15-TerminusBold28x14.psf.gz"),
        (5, 14, "Lat15-Terminus24x12.psf.gz"),
        (5, 14, "Lat15-TerminusBold24x12.psf.gz"),
        (5, 16, "Lat15-Terminus22x11.psf.gz"),
        (5, 16, "Lat15-TerminusBold22x11.psf.gz"),
        (6, 17, "Lat15-Terminus20x10.psf.gz"),
        (6, 17, "Lat15-TerminusBold20x10.psf.gz"),
        (7, 22, "Lat15-Fixed18.psf.gz"),
        (8, 22, "Lat15-Fixed15.psf.gz"),
        (8, 22, "Lat15-Fixed16.psf.gz"),
        (8, 22, "Lat15-Terminus16.psf.gz"),
        (8, 22, "Lat15-TerminusBold16.psf.gz"),
        (8, 22, "Lat15-TerminusBoldVGA16.psf.gz"),
        (8, 22, "Lat15-VGA16.psf.gz"),
        (9, 22, "Lat15-Fixed13.psf.gz"),
        (9, 22, "Lat15-Fixed14.psf.gz"),
        (9, 22, "Lat15-Terminus14.psf.gz"),
        (9, 22, "Lat15-TerminusBold14.psf.gz"),
        (9, 22, "Lat15-TerminusBoldVGA14.psf.gz"),
        (9, 22, "Lat15-VGA14.psf.gz"),
        (10, 29, "Lat15-Terminus12x6.psf.gz"),
        (16, 22, "Lat15-VGA8.psf.gz"),
        (21, 44, "Lat15-TomThumb4x6.psf.gz")
    ]

    # Paint the screen full of numbers that represent the column number, reversing the even rows
    console = Console()
    for rows, cols, font in fonts:
        print(rows, cols, font, file=stderr)
        console.set_font(font, True)
        for row in range(1, rows+1):
            for col in range(1, cols+1):
                console.text_at("{}".format(col % 10), col, row, False, (row % 2 == 0))
        console.text_at(font.split(".")[0], 1, 1, False, True)
        console.clear_to_eol()
        sleep(.5)


# Uncomment the calc_fonts() call to iterate through each system font
# and use ANSI codes to find the max row/column the screen will accommodate for
# each font. Remember to press the center EV3 button for each font.
# Also, you may want to adjust the `startswith` filter to show other codesets.
# calc_fonts()


# show the fonts
show_fonts()

sleep(5)