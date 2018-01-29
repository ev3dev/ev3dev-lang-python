Other classes
=============

Button
------

.. autoclass:: ev3dev.button.Button
    :members:
    :inherited-members:

    .. rubric:: Event handlers

    These will be called when state of the corresponding button is changed:

    .. py:data:: on_up
    .. py:data:: on_down
    .. py:data:: on_left
    .. py:data:: on_right
    .. py:data:: on_enter
    .. py:data:: on_backspace

    .. rubric:: Member functions and properties

Leds
----

.. autoclass:: ev3dev.led.Led
    :members:

.. autoclass:: ev3dev.led.Leds
    :members:

    .. rubric:: EV3 platform

    Led groups:

    .. py:data:: LEFT
    .. py:data:: RIGHT

    Colors:

    .. py:data:: RED
    .. py:data:: GREEN
    .. py:data:: AMBER
    .. py:data:: ORANGE
    .. py:data:: YELLOW

    .. rubric:: BrickPI platform

    Led groups:

    .. py:data:: LED1
    .. py:data:: LED2

    Colors:

    .. py:data:: BLUE

Power Supply
------------

.. autoclass:: ev3dev.power.PowerSupply
    :members:

Sound
-----

.. autoclass:: ev3dev.sound.Sound
    :members:

Screen
------

.. autoclass:: ev3dev.display.Display
    :members:
    :show-inheritance:

Bitmap fonts
^^^^^^^^^^^^

The :py:class:`Display` class allows to write text on the LCD using python
imaging library (PIL) interface (see description of the ``text()`` method
`here <http://pillow.readthedocs.io/en/3.1.x/reference/ImageDraw.html#PIL.ImageDraw.PIL.ImageDraw.Draw.text>`_).
The ``ev3dev.fonts`` module contains bitmap fonts in PIL format that should
look good on a tiny EV3 screen:

.. code-block:: py

    import ev3dev.fonts as fonts
    display.draw.text((10,10), 'Hello World!', font=fonts.load('luBS14'))

.. autofunction:: ev3dev.fonts.available

.. autofunction:: ev3dev.fonts.load

The following image lists all available fonts. The grid lines correspond
to EV3 screen size:

.. image:: _static/fonts.png

Lego Port
---------

.. autoclass:: ev3dev.port.LegoPort
    :members:
