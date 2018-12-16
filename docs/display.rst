Display
=======

.. autoclass:: ev3dev2.display.Display
    :members:
    :show-inheritance:


Bitmap fonts
------------

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
