# Upgrading from ev3dev-jessie (library v1) to ev3dev-stretch (library v2)

With ev3dev-stretch, we have introduced some breaking changes that you must be aware of to get older scripts running with new features.

**Scripts which worked on ev3dev-jessie are still supported and will continue to work as-is on Stretch.** However, if you want to use any of the new features we have introduced, you will need to switch to using version 2 of the python-ev3dev library. You can switch to version 2 by updating your import statements.

## Updating import statements

Previously, we recommended using one of the following as your `import` declaration:

```python
import ev3dev.ev3 as ev3
import ev3dev.brickpi as ev3
import ev3dev.auto as ev3
```

We have re-arranged the library to provide more control over what gets imported. For all platforms, you will now import from individual modules for things like sensors and motors, like this:

```python
from ev3dev2.motor import Motor, OUTPUT_A
from ev3dev2.sensor.lego import TouchSensor, UltrasonicSensor
```

The platform (EV3, BrickPi, etc.) will now be automatically determined.

You can omit import statements for modules you don't need, and add any additional ones that you do require. With this style of import, members are globally available by their name, so you would now refer to the Motor class as simply `Motor` rather than `ev3.Motor`.

## Remove references to `connected` attribute

In version 1 of the library, instantiating a device such as a motor or sensor would always succeed without an error. To see if the device connected successfully you would have to check the `connected` attribute. With the new version of the module, the constructor of device classes will throw an `ev3dev2.DeviceNotConnected` exception. You will need to remove any uses of the `connected` attribute.

## `Screen` class has been renamed to `Display`

To match the name used by LEGO's "EV3-G" graphical programming tools, we have renamed the `Screen` module to `Display`.

## Reorganization of `RemoteControl`, `BeaconSeeker` and `InfraredSensor`

The `RemoteControl` and `BeaconSeeker` classes have been removed; you will now use `InfraredSensor` for all purposes.

Additionally, we have renamed many of the properties on the `InfraredSensor` class to make the meaning more obvious. Check out [the `InfraredSensor` documentation](docs/sensors#infrared-sensor) for more info.

## Re-designed `Sound` class

The names and interfaces of some of the `Sound` class methods have changed. Check out [the `Sound` class docs](docs/other#sound) for details.

# Once you've adapted to breaking changes, check out the cool new features!

```eval_rst
- New classes are available for coordinating motors: :py:class:`ev3dev2.motor.MotorSet`, :py:class:`ev3dev2.motor.MoveTank`, :py:class:`ev3dev2.motor.MoveSteering`, and :py:class:`ev3dev2.motor.MoveJoystick`.
- Classes representing a variety of motor speed units are available and accepted by many of the motor interfaces: see :ref:`motor-unit-classes`.
- Friendlier interfaces for operating motors and sensors: check out :py:meth:`ev3dev2.motor.Motor.on_for_rotations` and the other ``on_for_*`` methods on motors.
- Easier interactivity via buttons: each button now has ``wait_for_pressed``, ``wait_for_released`` and ``wait_for_bump``
- Improved :py:class:`ev3dev2.sound.Sound` and :py:class:`ev3dev2.display.Display` interfaces
- New color conversion methods in :py:class:`ev3dev2.sensor.lego.ColorSensor`
```