Wheel classes
=============

.. currentmodule:: ev3dev2.wheel

.. contents:: :local:

.. _wheel-unit-classes:

Units
-----
All Wheel class units are in millimeters.  The ``diameter_mm`` and ``width_mm`` of the wheel must be specified whenever a new child Wheel class is added to ``ev3dev2/wheel.py``. The diameter and width for various lego wheels can be found at http://wheels.sariel.pl/

Common wheels
-------------

Wheel
~~~~~

.. autoclass:: Wheel
    :members:

EV3 Rim
~~~~~~~

.. autoclass:: EV3Rim
    :members:
    :show-inheritance:

EV3 Tire
~~~~~~~~

.. autoclass:: EV3Tire
    :members:
    :show-inheritance:

EV3 Education Set Rim
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: EV3EducationSetRim
    :members:
    :show-inheritance:

EV3 Education Set Tire
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: EV3EducationSetTire
    :members:
    :show-inheritance:
