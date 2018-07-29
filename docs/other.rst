Other classes
=============

Button
------

.. autoclass:: ev3dev2.button.Button
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

.. autoclass:: ev3dev2.led.Led
    :members:

.. autoclass:: ev3dev2.led.Leds
    :members:

LED group and color names
~~~~~~~~~~~~~~~~~~~~~~~~~

.. rubric:: EV3 platform

Led groups:

- ``LEFT``
- ``RIGHT``

Colors:

- ``BLACK``
- ``RED``
- ``GREEN``
- ``AMBER``
- ``ORANGE``
- ``YELLOW``

.. rubric:: BrickPI platform

Led groups:

- ``LED1``
- ``LED2``

Colors:

- ``BLACK``
- ``BLUE``

.. rubric:: BrickPI3 platform

Led groups:

- ``LED``

Colors:

- ``BLACK``
- ``BLUE``

.. rubric:: PiStorms platform

Led groups:

- ``LEFT``
- ``RIGHT``

Colors:

- ``BLACK``
- ``RED``
- ``GREEN``
- ``BLUE``
- ``YELLOW``
- ``CYAN``
- ``MAGENTA``

.. rubric:: EVB platform

None.
    

Power Supply
------------

.. autoclass:: ev3dev2.power.PowerSupply
    :members:

Sound
-----

.. autoclass:: ev3dev2.sound.Sound
    :members:

Display
-------

.. autoclass:: ev3dev2.display.Display
    :members:
    :show-inheritance:

Bitmap fonts
~~~~~~~~~~~~

The :py:class:`ev3dev2.display.Display` class allows to write text on the LCD using python
imaging library (PIL) interface (see description of the ``text()`` method
`here <http://pillow.readthedocs.io/en/3.1.x/reference/ImageDraw.html#PIL.ImageDraw.PIL.ImageDraw.Draw.text>`_).
The ``ev3dev2.fonts`` module contains bitmap fonts in PIL format that should
look good on a tiny EV3 screen:

.. code-block:: py

    import ev3dev2.fonts as fonts
    display.draw.text((10,10), 'Hello World!', font=fonts.load('luBS14'))

.. autofunction:: ev3dev2.fonts.available

.. autofunction:: ev3dev2.fonts.load

The following image lists all available fonts. The grid lines correspond
to EV3 screen size:

.. image:: _static/fonts.png

Lego Port
---------

.. autoclass:: ev3dev2.port.LegoPort
    :members:
