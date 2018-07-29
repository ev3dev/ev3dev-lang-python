Python language bindings for ev3dev
===================================

.. image:: https://travis-ci.org/ev3dev/ev3dev-lang-python.svg?branch=ev3dev-stretch
    :target: https://travis-ci.org/ev3dev/ev3dev-lang-python
.. image:: https://readthedocs.org/projects/python-ev3dev/badge/?version=ev3dev-stretch
    :target: http://python-ev3dev.readthedocs.org/en/ev3dev-stretch/?badge=ev3dev-stretch
    :alt: Documentation Status
.. image:: https://badges.gitter.im/ev3dev/chat.svg
    :target: https://gitter.im/ev3dev/chat
    :alt: Chat at https://gitter.im/ev3dev/chat

A Python3 library implementing an interface for ev3dev_ devices,
letting you control motors, sensors, hardware buttons, LCD
displays and more from Python code.

If you haven't written code in Python before, you'll need to learn the language
before you can use this library.

Getting Started
---------------

This library runs on ev3dev_. Before continuing, make sure that you have set up
your EV3 or other ev3dev device as explained in the `ev3dev Getting Started guide`_.
Make sure you have an ev3dev-stretch version greater than ``2.2.0``. You can check
the kernel version by selecting "About" in Brickman and scrolling down to the
"kernel version". If you don't have a compatible version, `upgrade the kernel before continuing`_.

Usage
-----

To start out, you'll need a way to work with Python. We recommend the
`ev3dev Visual Studio Code extension`_. If you're interested in using that,
check out our `Python + VSCode introduction tutorial`_ and then come back
once you have that set up.

Otherwise, you can can work with files `via an SSH connection`_ with an editor
such as `nano`_, use the Python interactive REPL (type ``python3``), or roll
your own solution. If you don't know how to do that, you are probably better off
choosing the recommended option above.

The template for a Python script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every Python program should have a few basic parts. Use this template
to get started:

.. code-block:: python

   #!/usr/bin/env python3
   from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_B, SpeedPercent, MoveTank
   from ev3dev2.sensor import INPUT_1
   from ev3dev2.sensor.lego import TouchSensor
   from ev3dev2.led import Leds

   # TODO: Add code here

The first line should be included in every Python program you write
for ev3dev. It allows you to run this program from Brickman, the graphical
menu that you see on the device screen. The other lines are import statements
which give you access to the library functionality. You will need to add
additional classes to the import list if you want to use other types of devices
or additional utilities.

You should use the ``.py`` extension for your file, e.g. ``my-file.py``.

If you encounter an error such as ``/usr/bin/env: 'python3\r': No such file or directory``,
you must switch your editor's "line endings" setting for the file from "CRLF" to just "LF".
This is usually in the status bar at the bottom. For help, see `our FAQ page`_.

Important: Make your script executable (non-Visual Studio Code only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To be able to run your Python file, **your program must be executable**. If
you are using the `ev3dev Visual Studio Code extension`_, you can skip this step,
as it will be automatically performed when you download your code to the brick.

**To mark a program as executable from the command line (often an SSH session),
run** ``chmod +x my-file.py``.

You can now run ``my-file.py`` via the Brickman File Browser or you can run it
from the command line by preceding the file name with ``./``: ``./my-file.py``

Controlling the LEDs with a touch sensor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This code will turn the LEDs red whenever the touch sensor is pressed, and
back to green when it's released. Plug a touch sensor into any sensor port before
trying this out.

.. code-block:: python

  ts = TouchSensor()
  leds = Leds()

  print("Press the touch sensor to change the LED color!")

  while True:
      if ts.is_pressed:
          leds.set_color("LEFT", "GREEN")
          leds.set_color("RIGHT", "GREEN")
      else:
          leds.set_color("LEFT", "RED")
          leds.set_color("RIGHT", "RED")

If you'd like to use a sensor on a specific port, specify the port like this:

.. code-block:: python

  ts = TouchSensor(INPUT_1)

Running a single motor
~~~~~~~~~~~~~~~~~~~~~~

This will run a LEGO Large Motor at 75% of maximum speed for 5 rotations.

.. code-block:: python

  m = LargeMotor(OUTPUT_A)
  m.on_for_rotations(SpeedPercent(75), 5)

You can also run a motor for a number of degrees, an amount of time, or simply
start it and let it run until you tell it to stop. Additionally, other units are
also available. See the following pages for more information:

- http://python-ev3dev.readthedocs.io/en/ev3dev-stretch/motors.html#ev3dev.motor.Motor.on_for_degrees
- http://python-ev3dev.readthedocs.io/en/ev3dev-stretch/motors.html#units

Driving with two motors
~~~~~~~~~~~~~~~~~~~~~~~

The simplest drive control style is with the `MoveTank` class:

.. code-block:: python

    tank_drive = MoveTank(OUTPUT_A, OUTPUT_B)

    # drive in a turn for 5 rotations of the outer motor
    # the first two parameters can be unit classes or percentages.
    tank_drive.on_for_rotations(SpeedPercent(50), SpeedPercent(75), 10)
    
    # drive in a different turn for 3 seconds
    tank_drive.on_for_seconds(SpeedPercent(60), SpeedPercent(30), 3)

There are also `MoveSteering` and `MoveJoystick` classes which provide different
styles of control. See the following pages for more information:

- http://python-ev3dev.readthedocs.io/en/ev3dev-stretch/motors.html#multiple-motor-groups
- http://python-ev3dev.readthedocs.io/en/ev3dev-stretch/motors.html#units

Using text-to-speech
~~~~~~~~~~~~~~~~~~~~

If you want to make your robot speak, you can use the ``Sound.speak`` method:

.. code-block:: python

  from ev3dev2.sound import Sound

  sound = Sound()
  sound.speak('Welcome to the E V 3 dev project!')

Make sure to check out the `User Resources`_ section for more detailed
information on these features and many others.

User Resources
--------------

Library Documentation
    **Class documentation for this library can be found on** `our Read the Docs page`_ **.**
    You can always go there to get information on how you can use this
    library's functionality.

Demo Code
    There are several demo programs that you can run to get acquainted with
    this language binding. The programs are available at
    https://github.com/ev3dev/ev3dev-lang-python-demo

ev3python.com
    One of our community members, @ndward, has put together a great website
    with detailed guides on using this library which are targeted at beginners.
    If you are just getting started with programming, we highly recommend
    that you check it out at `ev3python.com`_!

Frequently-Asked Questions
    Experiencing an odd error or unsure of how to do something that seems
    simple? Check our our `FAQ`_ to see if there's an existing answer.

ev3dev.org
    `ev3dev.org`_ is a great resource for finding guides and tutorials on
    using ev3dev, straight from the maintainers.

Support
    If you are having trouble using this library, please open an issue
    at `our Issues tracker`_ so that we can help you. When opening an
    issue, make sure to include as much information as possible about
    what you are trying to do and what you have tried. The issue template
    is in place to guide you through this process.

Upgrading this Library
----------------------

You can upgrade this library from the command line as follows. Make sure
to type the password (the default is ``maker``) when prompted.

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install --only-upgrade python3-ev3dev2


Developer Resources
-------------------

Python Package Index
    The Python language has a `package repository`_ where you can find
    libraries that others have written, including the `latest version of
    this package`_.

Python 2.x and Python 3.x Compatibility
---------------------------------------

Some versions of the ev3dev_ distribution come with both `Python 2.x`_ and `Python 3.x`_ installed
but this library is compatible only with Python 3.

.. _ev3dev: http://ev3dev.org
.. _ev3dev.org: ev3dev_
.. _Getting Started: ev3dev-getting-started_
.. _ev3dev Getting Started guide: ev3dev-getting-started_
.. _ev3dev-getting-started: http://www.ev3dev.org/docs/getting-started/
.. _upgrade the kernel before continuing: http://www.ev3dev.org/docs/tutorials/upgrading-ev3dev/
.. _detailed instructions for USB connections: ev3dev-usb-internet_
.. _via an SSH connection: http://www.ev3dev.org/docs/tutorials/connecting-to-ev3dev-with-ssh/
.. _ev3dev-usb-internet: http://www.ev3dev.org/docs/tutorials/connecting-to-the-internet-via-usb/
.. _our Read the Docs page: http://python-ev3dev.readthedocs.org/en/ev3dev-stretch/
.. _ev3python.com: http://ev3python.com/
.. _FAQ: http://python-ev3dev.readthedocs.io/en/ev3dev-stretch/faq.html
.. _our FAQ page: FAQ_
.. _ev3dev-lang-python: https://github.com/rhempel/ev3dev-lang-python
.. _our Issues tracker: https://github.com/rhempel/ev3dev-lang-python/issues
.. _EXPLOR3R: demo-robot_
.. _demo-robot: http://robotsquare.com/2015/10/06/explor3r-building-instructions/
.. _demo programs: demo-code_
.. _demo-code: https://github.com/rhempel/ev3dev-lang-python/tree/master/demo
.. _robot-square: http://robotsquare.com/
.. _Python 2.x: python2_
.. _python2: https://docs.python.org/2/
.. _Python 3.x: python3_
.. _python3: https://docs.python.org/3/
.. _package repository: pypi_
.. _pypi: https://pypi.python.org/pypi
.. _latest version of this package: pypi-python-ev3dev_
.. _pypi-python-ev3dev: https://pypi.python.org/pypi/python-ev3dev2
.. _ev3dev Visual Studio Code extension: https://github.com/ev3dev/vscode-ev3dev-browser
.. _Python + VSCode introduction tutorial: https://github.com/ev3dev/vscode-hello-python
.. _nano: http://www.ev3dev.org/docs/tutorials/nano-cheat-sheet/
