Sensor classes
==============

Sensor
------

This is the base class all the other sensor classes are derived from.

.. currentmodule:: ev3dev.sensor

.. autoclass:: Sensor
    :members:

Special sensor classes
----------------------

The classes derive from :py:class:`Sensor` and provide helper functions
specific to the corresponding sensor type. Each of the functions makes
sure the sensor is in the required mode and then returns the specified value.

..

Touch Sensor
########################

.. autoclass:: lego.TouchSensor
    :members:
    :show-inheritance:



Color Sensor
########################

.. autoclass:: lego.ColorSensor
    :members:
    :show-inheritance:



Ultrasonic Sensor
########################

.. autoclass:: lego.UltrasonicSensor
    :members:
    :show-inheritance:



Gyro Sensor
########################

.. autoclass:: lego.GyroSensor
    :members:
    :show-inheritance:



Infrared Sensor
########################

.. autoclass:: lego.InfraredSensor
    :members:
    :show-inheritance:



Sound Sensor
########################

.. autoclass:: lego.SoundSensor
    :members:
    :show-inheritance:



Light Sensor
########################

.. autoclass:: lego.LightSensor
    :members:
    :show-inheritance:




..

