API reference
=============

Device interfaces
-----------------

.. rubric:: Contents:

.. toctree::
    :maxdepth: 2

    motors
    sensors
    button
    leds
    power-supply
    sound
    display
    ports
    port-names
    wheels


Other APIs
----------

Each class in ev3dev module inherits from the base :py:class:`ev3dev2.Device` class.

.. autoclass:: ev3dev2.Device

.. autofunction:: ev3dev2.list_device_names

.. autofunction:: ev3dev2.list_devices

.. autofunction:: ev3dev2.motor.list_motors

.. autofunction:: ev3dev2.sensor.list_sensors