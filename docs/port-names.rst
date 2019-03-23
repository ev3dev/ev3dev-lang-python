.. _port-names:

Port names
==========

Classes such as :py:class:`ev3dev2.motor.Motor` and those based on
:py:class:`ev3dev2.sensor.Sensor` accept parameters to specify which port the
target device is connected to. This parameter is typically caled ``address``.

The following constants are available on all platforms:

.. rubric:: Output

- ``ev3dev2.motor.OUTPUT_A``
- ``ev3dev2.motor.OUTPUT_B``
- ``ev3dev2.motor.OUTPUT_C``
- ``ev3dev2.motor.OUTPUT_D``

.. rubric:: Input

- ``ev3dev2.sensor.INPUT_1``
- ``ev3dev2.sensor.INPUT_2``
- ``ev3dev2.sensor.INPUT_3``
- ``ev3dev2.sensor.INPUT_4``

Additionally, on BrickPi3, the ports of up to four stacked BrickPi's can be
referenced as `OUTPUT_E` through `OUTPUT_P` and `INPUT_5` through `INPUT_16`.

.. rubric:: Example

.. code-block:: python

   from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_B
   from ev3dev2.sensor import INPUT_1
   from ev3dev2.sensor.lego import TouchSensor

   m = LargeMotor(OUTPUT_A)
   s = TouchSensor(INPUT_1)