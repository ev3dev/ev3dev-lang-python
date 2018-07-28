Motor classes
=============

.. currentmodule:: ev3dev2.motor

.. contents:: :local:

.. _motor-unit-classes:

Units
-----

Most methods which run motors with accept a ``speed`` or ``speed_pct`` argument. While this can be provided as an integer which will be interpreted as a percentage of max speed, you can also specify an instance of any of the following classes, each of which represents a different unit system:

.. autoclass:: SpeedInteger
.. autoclass:: SpeedPercent
.. autoclass:: SpeedNativeUnits
.. autoclass:: SpeedRPS
.. autoclass:: SpeedRPM
.. autoclass:: SpeedDPS
.. autoclass:: SpeedDPM

Example:

.. code:: python

    from ev3dev2.motor import SpeedRPM
    
    # later...

    # rotates the motor at 200 RPM (rotations-per-minute) for five seconds.
    my_motor.on_for_seconds(SpeedRPM(200), 5)



Common motors
-------------

Tacho Motor (``Motor``)
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: Motor
    :members:

Large EV3 Motor
~~~~~~~~~~~~~~~

.. autoclass:: LargeMotor
    :members:
    :show-inheritance:

Medium EV3 Motor
~~~~~~~~~~~~~~~~

.. autoclass:: MediumMotor
    :members:
    :show-inheritance:

Additional motors
-----------------

DC Motor
~~~~~~~~

.. autoclass:: DcMotor
    :members:

Servo Motor
~~~~~~~~~~~

.. autoclass:: ServoMotor
    :members:

Actuonix L12 50 Linear Servo Motor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: ActuonixL1250Motor
    :members:

Actuonix L12 100 Linear Servo Motor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: ActuonixL12100Motor
    :members:

Multiple-motor groups
---------------------

Motor Set
~~~~~~~~~

.. autoclass:: MotorSet
    :members:

Move Tank
~~~~~~~~~

.. autoclass:: MoveTank
    :members:

Move Steering
~~~~~~~~~~~~~

.. autoclass:: MoveSteering
    :members:

Move Joystick
~~~~~~~~~~~~~

.. autoclass:: MoveJoystick
    :members:
