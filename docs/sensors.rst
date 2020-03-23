Sensor classes
==============

.. contents:: :local:

*Note:* If you are using a BrickPi rather than an EV3, you will need to manually
configure the ports before interacting with your sensors. See the example
`here <https://github.com/ev3dev/ev3dev-lang-python-demo/blob/stretch/platform/brickpi3-motor-and-sensor.py>`_.


Dedicated sensor classes
------------------------

These classes derive from :py:class:`ev3dev2.sensor.Sensor` and provide helper functions
specific to the corresponding sensor type. Each provides sensible property
accessors for the main functionality of the sensor.

..

.. currentmodule:: ev3dev2.sensor.lego

Touch Sensor
############

.. autoclass:: TouchSensor
    :members:
    :show-inheritance:



Color Sensor
############

.. autoclass:: ColorSensor
    :members:
    :show-inheritance:



Ultrasonic Sensor
#################

.. autoclass:: UltrasonicSensor
    :members:
    :show-inheritance:



Gyro Sensor
###########

.. autoclass:: GyroSensor
    :members:
    :show-inheritance:



Infrared Sensor
###############

.. autoclass:: InfraredSensor
    :members:
    :show-inheritance:



Sound Sensor
############

.. autoclass:: SoundSensor
    :members:
    :show-inheritance:



Light Sensor
############

.. autoclass:: LightSensor
    :members:
    :show-inheritance:



Base "Sensor"
-------------

This is the base class all the other sensor classes are derived from. You
generally want to use one of the other classes instead, but if your sensor
doesn't have a dedicated class, this is will let you interface with it as a
generic device.

.. currentmodule:: ev3dev2.sensor

.. autoclass:: Sensor
    :members:


..

