#!/usr/bin/env micropython
from time import sleep
from sys import stderr, stdin
from os import listdir
from ev3dev2.display import Display

"""
Used to iterate over the system console fonts (in /usr/share/consolefonts) and calculate the max row/col
position by moving the cursor at max-row/max-column and asking the LCD for the actual cursor position
where it ends up (the EV3 LCD screen driver prevents the cursor from positioning off-screen).

The font specification consists of three parameters - codeset, font face and font size. The codeset specifies
what characters will be supported by the font. The font face determines the general look of the font. Each
font face is available in certain possible sizes.

For Codeset clarity, see https://www.systutorials.com/docs/linux/man/5-console-setup/#lbAP

    Lat15: Covers entirely ISO-8859-1, ISO-8859-9 and ISO-8859-15. Suitable for the so called Latin1 and
    Latin5 languages - Afar, Afrikaans, Albanian, Aragonese, Asturian, Aymara, Basque, Bislama, Breton, Catalan,
    Chamorro, Danish, Dutch, English, Estonian, Faroese, Fijian, Finnish, French, Frisian, Friulian, Galician,
    German, Hiri Motu, Icelandic, Ido, Indonesian, Interlingua, Interlingue, Italian, Low Saxon, Lule Sami,
    Luxembourgish, Malagasy, Manx Gaelic, Norwegian Bokmal, Norwegian Nynorsk, Occitan, Oromo or Galla,
    Portuguese, Rhaeto-Romance (Romansch), Scots Gaelic, Somali, South Sami, Spanish, Swahili, Swedish, Tswana,
    Turkish, Volapuk, Votic, Walloon, Xhosa, Yapese and Zulu. Completely covered by the following font faces:
    Fixed (all sizes), Terminus (all sizes), TerminusBold (all sizes), TerminusBoldVGA (all sizes),
    VGA (sizes 8x16 and 16x32).

    Lat2: Covers entirely ISO-8859-2. The Euro sign and the Romanian letters with comma below are also supported.
    Suitable for the so called Latin2 languages - Bosnian, Croatian, Czech, Hungarian, Polish, Romanian,
    Slovak, Slovenian and Sorbian (lower and upper). Completely covered by the following font faces:
    Fixed (all sizes), Terminus (all sizes), TerminusBold (all sizes), TerminusBoldVGA (all sizes),
    VGA (sizes 8x16 and 16x32).

    Lat38: Covers entirely ISO-8859-3 and ISO-8859-14. Suitable for Chichewa Esperanto, Irish, Maltese and Welsh.
    Completely covered by the following font faces: Fixed (all sizes) and VGA (sizes 8x16 and 16x32).

    Lat7: Covers entirely ISO-8859-13. Suitable for Lithuanian, Latvian, Maori and Marshallese.
    Completely covered by the following font faces: Fixed (all sizes), Terminus (all sizes),
    TerminusBold (all sizes), TerminusBoldVGA (all sizes), VGA (sizes 8x16 and 16x32).
"""


def calc_fonts():
    """
    Iterate through all the Latin "1 & 5" fonts, and use ANSI escape sequences to see how many rows/columns
    the EV3 LCD screen can accommodate for each font
    """
    lcd = Display()

    files = [f for f in listdir("/usr/share/consolefonts/") if f.startswith("Lat15") and f.endswith(".psf.gz")]
    files.sort()
    for font in files:
        lcd.set_font(font)

        # position cursor at 50, 50, and ask the console to report its actual cursor position
        lcd.text_grid("\x1b[6n", False, 50, 50)
        lcd.text_grid(font + " ", False, 1, 1, True)

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
        print("(%s, %s, \"%s\")," % (rows, cols, font), file=stderr)
        sleep(.5)


def test_fonts():
    """
    Iterate over the known Latin "1 & 5" fonts and display each on the EV3 LCD panel.
    Note: Terminus fonts are "thinner"; TerminusBold and VGA offer more contrast on the LCD screen
    and are thus more readable; the TomThumb font is waaaaay too small to read!
    """
    lcd = Display()

    # Create a list of tuples with calulated rows, columns, font filename
    fonts = [
        ( 4, 11, "Lat15-Terminus32x16.psf.gz"),
        ( 4, 11, "Lat15-TerminusBold32x16.psf.gz"),
        ( 4, 11, "Lat15-VGA28x16.psf.gz"),
        ( 4, 11, "Lat15-VGA32x16.psf.gz"),
        ( 4, 12, "Lat15-Terminus28x14.psf.gz"),
        ( 4, 12, "Lat15-TerminusBold28x14.psf.gz"),
        ( 5, 14, "Lat15-Terminus24x12.psf.gz"),
        ( 5, 14, "Lat15-TerminusBold24x12.psf.gz"),
        ( 5, 16, "Lat15-Terminus22x11.psf.gz"),
        ( 5, 16, "Lat15-TerminusBold22x11.psf.gz"),
        ( 6, 17, "Lat15-Terminus20x10.psf.gz"),
        ( 6, 17, "Lat15-TerminusBold20x10.psf.gz"),
        ( 7, 22, "Lat15-Fixed18.psf.gz"),
        ( 8, 22, "Lat15-Fixed15.psf.gz"),
        ( 8, 22, "Lat15-Fixed16.psf.gz"),
        ( 8, 22, "Lat15-Terminus16.psf.gz"),
        ( 8, 22, "Lat15-TerminusBold16.psf.gz"),
        ( 8, 22, "Lat15-TerminusBoldVGA16.psf.gz"),
        ( 8, 22, "Lat15-VGA16.psf.gz"),
        ( 9, 22, "Lat15-Fixed13.psf.gz"),
        ( 9, 22, "Lat15-Fixed14.psf.gz"),
        ( 9, 22, "Lat15-Terminus14.psf.gz"),
        ( 9, 22, "Lat15-TerminusBold14.psf.gz"),
        ( 9, 22, "Lat15-TerminusBoldVGA14.psf.gz"),
        ( 9, 22, "Lat15-VGA14.psf.gz"),
        (10, 29, "Lat15-Terminus12x6.psf.gz"),
        (16, 22, "Lat15-VGA8.psf.gz"),
        (21, 44, "Lat15-TomThumb4x6.psf.gz")
    ]
   
    # Paint the screen full of numbers that represent the column number, reversing the even rows
    for rows, cols, font in fonts:
        print(rows, cols, font, file=stderr)
        lcd.set_font(font)
        for row in range(1, rows+1):
            for col in range(1, cols+1):
                lcd.text_grid("%d" % (col % 10), False, col, row, (row % 2 == 0))
        lcd.text_grid(font.split(".")[0] + " ", False, 1, 1, True)
        sleep(.5)


# calc_fonts()
test_fonts()

sleep(5)
