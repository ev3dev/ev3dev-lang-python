Sensor classes
==============

Sensor
------

This is the base class all the other sensor classes are derived from.

.. autoclass:: ev3dev.sensor.Sensor
    :members:

Special sensor classes
----------------------

The classes derive from :py:class:`Sensor` and provide helper functions
specific to the corresponding sensor type. Each of the functions makes
sure the sensor is in the required mode and then returns the specified value.

..

Touch Sensor
########################

.. autoclass:: ev3dev.sensor.lego.TouchSensor
    :members:
    :show-inheritance:



Color Sensor
########################

.. autoclass:: ev3dev.sensor.lego.ColorSensor
    :members:
    :show-inheritance:



Ultrasonic Sensor
########################

.. autoclass:: ev3dev.sensor.lego.UltrasonicSensor
    :members:
    :show-inheritance:



Gyro Sensor
########################

.. autoclass:: ev3dev.sensor.lego.GyroSensor
    :members:
    :show-inheritance:



Infrared Sensor
########################

.. autoclass:: ev3dev.sensor.lego.InfraredSensor
    :members:
    :show-inheritance:



Sound Sensor
########################

.. autoclass:: ev3dev.sensor.lego.SoundSensor
    :members:
    :show-inheritance:



Light Sensor
########################

.. autoclass:: ev3dev.sensor.lego.LightSensor
    :members:
    :show-inheritance:




..

