Sensor classes
==============

Sensor
------

This is the base class all the other sensor classes are derived from.

.. currentmodule:: ev3dev.core

.. autoclass:: Sensor
    :members:

Special sensor classes
----------------------

The classes derive from :py:class:`Sensor` and provide helper functions
specific to the corresponding sensor type. Each of the functions makes
sure the sensor is in the required mode and then returns the specified value.

.. ~autogen doc-special-sensor-classes

Touch Sensor
########################

.. autoclass:: TouchSensor
    :members:
    :show-inheritance:



Color Sensor
########################

.. autoclass:: ColorSensor
    :members:
    :show-inheritance:



Ultrasonic Sensor
########################

.. autoclass:: UltrasonicSensor
    :members:
    :show-inheritance:



Gyro Sensor
########################

.. autoclass:: GyroSensor
    :members:
    :show-inheritance:



Infrared Sensor
########################

.. autoclass:: InfraredSensor
    :members:
    :show-inheritance:



Sound Sensor
########################

.. autoclass:: SoundSensor
    :members:
    :show-inheritance:



Light Sensor
########################

.. autoclass:: LightSensor
    :members:
    :show-inheritance:




.. ~autogen

