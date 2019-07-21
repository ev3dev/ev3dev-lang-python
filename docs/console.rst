Console
=======

.. autoclass:: ev3dev2.console.Console
    :members:

Examples:

.. code-block:: py

    #!/usr/bin/env micropython
    from ev3dev2.console import Console

    # create a Console instance, which uses the default font, clears the screen,
    # and turns off the cursor
    console = Console()

    # display 'Hello World!' at row 5, column 1 in inverse, but clear the console first
    console.text_at('Hello World!', row=5, column=1, clear_screen=True, inverse=True)

.. code-block:: py

    #!/usr/bin/env micropython
    from time import sleep
    from ev3dev2._platform.ev3 import INPUT_1, INPUT_2, INPUT_3
    from ev3dev2.console import Console
    from ev3dev2.sensor.lego import GyroSensor, ColorSensor

    console = Console()
    gyro = GyroSensor(INPUT_1)
    gyro.mode = GyroSensor.MODE_GYRO_ANG
    color_sensor_left = ColorSensor(INPUT_2)
    color_sensor_right = ColorSensor(INPUT_3)

    # show the gyro angle and reflected light intensity for both of our color sensors
    while True:
        angle = gyro.angle
        left = color_sensor_left.reflected_light_intensity
        right = color_sensor_right.reflected_light_intensity

        # show angle in inverse color when pointing at 0
        console.text_at("G: %03d" % (angle), column=5, row=1, clear_screen=True, text_color=(angle == 0))

        # show light intensity values in inverse when 'dark'
        console.text_at("L: %02d" % (left), column=0, row=3, clear_screen=False, inverse=(left < 10))
        console.text_at("R: %02d" % (right), clear_screen=False, x=10, y=3, inverse=(right < 10))

        sleep(0.5)

Console fonts
-------------

The :py:class:`ev3dev2.console.Console` class displays text on the LCD console
using ANSI codes in various system console fonts. The system console fonts are
located in `/usr/share/consolefonts`.

Font filenames consist of the codeset, font face and font size. The codeset
specifies the characters supported. The font face determines the look of the
font. Each font face is available in multiple sizes.

For Codeset information, see
`<https://www.systutorials.com/docs/linux/man/5-console-setup/#lbAP>`.

- Lat15: Covers entirely ISO-8859-1, ISO-8859-9 and ISO-8859-15. Suitable for
  the so called Latin1 and Latin5 languages - Afar, Afrikaans, Albanian,
  Aragonese, Asturian, Aymara, Basque, Bislama, Breton, Catalan, Chamorro,
  Danish, Dutch, English, Estonian, Faroese, Fijian, Finnish, French, Frisian,
  Friulian, Galician, German, Hiri Motu, Icelandic, Ido, Indonesian,
  Interlingua, Interlingue, Italian, Low Saxon, Lule Sami, Luxembourgish,
  Malagasy, Manx Gaelic, Norwegian Bokmal, Norwegian Nynorsk, Occitan, Oromo
  or Galla, Portuguese, Rhaeto-Romance (Romansch), Scots Gaelic, Somali,
  South Sami, Spanish, Swahili, Swedish, Tswana, Turkish, Volapuk, Votic,
  Walloon, Xhosa, Yapese and Zulu. Completely covered by the following font
  faces: Fixed (all sizes), Terminus (all sizes), TerminusBold (all sizes),
  TerminusBoldVGA (all sizes), VGA (sizes 8x16 and 16x32).

- Lat2: Covers entirely ISO-8859-2. The Euro sign and the Romanian letters with
  comma below are also supported. Suitable for the so called Latin2 languages:
  Bosnian, Croatian, Czech, Hungarian, Polish, Romanian, Slovak, Slovenian and
  Sorbian (lower and upper). Completely covered by the following font faces:
  Fixed (all sizes), Terminus (all sizes), TerminusBold (all sizes),
  TerminusBoldVGA (all sizes), VGA (sizes 8x16 and 16x32).

- Lat38: Covers entirely ISO-8859-3 and ISO-8859-14. Suitable for Chichewa
  Esperanto, Irish, Maltese and Welsh. Completely covered by the following font
  faces: Fixed (all sizes) and VGA (sizes 8x16 and 16x32).

- Lat7: Covers entirely ISO-8859-13. Suitable for Lithuanian, Latvian, Maori
  and Marshallese. Completely covered by the following font faces: Fixed (all
  sizes), Terminus (all sizes), TerminusBold (all sizes), TerminusBoldVGA (all
  sizes), VGA (sizes 8x16 and 16x32).

- There are other codesets suitable for other languages including: Arabic,
  Armenian, CyrAsia, CyrKoi, CyrSlav, Ethiopian, Georgian, Greek, Hebrew, Lao,
  Thai, Uni1, Uni2, Uni3, and Vietnamese.

Note: Terminus fonts are "thinner"; TerminusBold and VGA offer more contrast on
the LCD console and are thus more readable; the TomThumb font is too small to
read!

Depending on the font used, the EV3 LCD console will support various maximum
rows and columns, as follows for the `Lat15` fonts. See
`utils/console_fonts.py` to discover fonts and their resulting rows/columns.
These fonts are listed in larger-to-smaller size order:

+----------+------------+--------------------------------+
| LCD Rows | LCD Columns| Font                           |
+==========+============+================================+
| 4        |     11     | Lat15-Terminus32x16.psf.gz     |
+----------+------------+--------------------------------+
| 4        |     11     | Lat15-TerminusBold32x16.psf.gz |
+----------+------------+--------------------------------+
| 4        |     11     | Lat15-VGA28x16.psf.gz          |
+----------+------------+--------------------------------+
| 4        |     11     | Lat15-VGA32x16.psf.gz          |
+----------+------------+--------------------------------+
| 4        |     12     | Lat15-Terminus28x14.psf.gz     |
+----------+------------+--------------------------------+
| 4        |     12     | Lat15-TerminusBold28x14.psf.gz |
+----------+------------+--------------------------------+
| 5        |     14     | Lat15-Terminus24x12.psf.gz     |
+----------+------------+--------------------------------+
| 5        |     14     | Lat15-TerminusBold24x12.psf.gz |
+----------+------------+--------------------------------+
| 5        |     16     | Lat15-Terminus22x11.psf.gz     |
+----------+------------+--------------------------------+
| 5        |     16     | Lat15-TerminusBold22x11.psf.gz |
+----------+------------+--------------------------------+
| 6        |     17     | Lat15-Terminus20x10.psf.gz     |
+----------+------------+--------------------------------+
| 6        |     17     | Lat15-TerminusBold20x10.psf.gz |
+----------+------------+--------------------------------+
| 7        |     22     | Lat15-Fixed18.psf.gz           |
+----------+------------+--------------------------------+
| 8        |     22     | Lat15-Fixed15.psf.gz           |
+----------+------------+--------------------------------+
| 8        |     22     | Lat15-Fixed16.psf.gz           |
+----------+------------+--------------------------------+
| 8        |     22     | Lat15-Terminus16.psf.gz        |
+----------+------------+--------------------------------+
| 8        |     22     | Lat15-TerminusBold16.psf.gz    |
+----------+------------+--------------------------------+
| 8        |     22     | Lat15-TerminusBoldVGA16.psf.gz |
+----------+------------+--------------------------------+
| 8        |     22     | Lat15-VGA16.psf.gz             |
+----------+------------+--------------------------------+
| 9        |     22     | Lat15-Fixed13.psf.gz           |
+----------+------------+--------------------------------+
| 9        |     22     | Lat15-Fixed14.psf.gz           |
+----------+------------+--------------------------------+
| 9        |     22     | Lat15-Terminus14.psf.gz        |
+----------+------------+--------------------------------+
| 9        |     22     | Lat15-TerminusBold14.psf.gz    |
+----------+------------+--------------------------------+
| 9        |     22     | Lat15-TerminusBoldVGA14.psf.gz |
+----------+------------+--------------------------------+
| 9        |     22     | Lat15-VGA14.psf.gz             |
+----------+------------+--------------------------------+
| 10       |     29     | Lat15-Terminus12x6.psf.gz      |
+----------+------------+--------------------------------+
| 16       |     22     | Lat15-VGA8.psf.gz              |
+----------+------------+--------------------------------+
| 21       |     44     | Lat15-TomThumb4x6.psf.gz       |
+----------+------------+--------------------------------+

Example:

.. code-block:: py

    #!/usr/bin/env micropython
    from ev3dev2.console import Console

    # create a Console instance, which uses the default font, clears the screen,
    # and turns off the cursor
    console = Console()

    # change the console font
    console.set_font('Lat15-TerminusBold16.psf.gz')

    # display 'Hello World!' at  column 1, row 5
    console.text_at('Hello World!', column=1, row=5)
