Python language bindings for ev3dev
===================================

.. image:: https://travis-ci.org/rhempel/ev3dev-lang-python.svg?branch=master
    :target: https://travis-ci.org/rhempel/ev3dev-lang-python
.. image:: https://readthedocs.org/projects/python-ev3dev/badge/?version=latest
    :target: http://python-ev3dev.readthedocs.org/en/latest/?badge=latest
    :alt: Documentation Status

A Python3 library implementing unified interface for ev3dev_ devices.

Example Code
------------

To run these minimal examples, run the Python3 interpreter from
the terminal like this: 

.. code-block:: bash

  robot@ev3dev:~/ev3dev-lang-python$ python3
  Python 3.4.2 (default, Oct  8 2014, 14:47:30) 
  [GCC 4.9.1] on linux
  Type "help", "copyright", "credits" or "license" for more information.
  >>>

The ``>>>`` characters are the default prompt for Python. In the examples
below, we have removed these characters so it's easier to cut and 
paste the code into your session.

Load the ev3dev-lang_ bindings:

.. code-block:: python

  import ev3dev.ev3 as ev3

Now let's try our first program. This code will turn the left LED red
whenever the touch sensor is pressed, and back to green when it's
released. Plug a touch sensor into any sensor port and then paste in this
code - you'll need to hit ``Enter`` after pasting to complete the
loop and start the program.  Hit ``Ctrl-C`` to exit the loop.

.. code-block:: python

  ts = ev3.TouchSensor()
  while True:
      ev3.Leds.set_color(ev3.Leds.LEFT, (ev3.Leds.GREEN, ev3.Leds.RED)[ts.value()])
  
Now plug a motor into the ``A`` port and paste this code into the terminal. This
little program will run the motor at 500 RPM for 3 seconds.

.. code-block:: python

  m = ev3.LargeMotor('outA')
  m.run_timed(time_sp=3000, speed_sp=500)

If you want to make your robot speak, then paste this code into the terminal:

.. code-block:: python

  ev3.Sound.speak('Welcome to the E V 3 dev project!').wait()

To quit Python, just type ``exit()`` or ``Ctrl-D``.

User Resources
--------------

Getting Started with ev3dev
    If you got here as the result of looking for "how to program
    LEGO MINDSTORMS EV3 using Python" then you might not be aware that
    this is part of a much larger project called ev3dev_. Make sure
    you read the `Getting Started`_ page
    to become familiar with ev3dev_ first!

Connecting the EV3 to the Internet
    You can connect to an EV3 running ev3dev_ using USB, Wifi or
    Bluetooth. The USB connection is a good starting point, and
    the ev3dev_ site has `detailed instructions for USB connections`_
    for Linux, Windows, and Mac computers.

Demo Robot
    Laurens Valk of robot-square_ has been kind enough to allow us to
    reference his excellent `EXPLOR3R`_ robot. Consider building the
    `EXPLOR3R`_ and running the demo programs referenced below to get
    familiar with what Python programs using this binding look like.

Demo Code
    There are `demo programs`_ that you can run to get acquainted with
    this language binding. The programs are designed to work with the
    `EXPLOR3R`_ robot.

Developer Resources
-------------------

Python Package Index
    The Python language has a `package repository`_ where you can find
    libraries that others have written, including the `latest version of
    this package`_.

The ev3dev Binding Specification
    Like all of the language bindings for ev3dev_ supported hardware, the
    Python binding follows the minimal API that must be provided per
    `this document`_.

The ev3dev-lang Project on GitHub
    The `source repository for the generic API`_ and the scripts to automatically
    generate the binding. Only developers of the ev3dev-lang-python_ binding 
    would normally need to access this information.

Python2.x and Python3.x Compatibility
-------------------------------------

The ev3dev_ distribution comes with both python2_ and python3_ installed
but this library is compatible only with Python3.

Note that currently, the Python3 binding for ev3dev_ is not installed
by default - this will be addressed in the next package we
release.

The easiest way to work around the problem is
to get your EV3 connected to the Internet and then:

#. Update the package lists
#. Install the ``python3-pil`` package
#. Use ``easy-install`` install ``python-ev3dev``

.. code-block:: bash

  sudo apt-get update
  sudo apt-get install python3-pil
  sudo python3 -m easy_install python-ev3dev

You will be asked for the ``robot`` user's password to get ``sudo`` access
to the system - the default password is ``maker``.

Please be patient - a typical ``apt-get update`` will take about
10 minutes - there's a LOT going on under the hood to sort out
package dependencies.

And now you can use ev3dev-lang-python_ under `Python 3.x`_.

.. code-block:: python

  from ev3dev.auto import *

----

.. _ev3dev: http://ev3dev.org
.. _Getting Started: ev3dev-getting-started_
.. _ev3dev-getting-started: http://www.ev3dev.org/docs/getting-started/
.. _detailed instructions for USB connections: ev3dev-usb-internet_ 
.. _ev3dev-usb-internet: http://www.ev3dev.org/docs/tutorials/connecting-to-the-internet-via-usb/
.. _source repository for the generic API: ev3dev-lang_
.. _ev3dev-lang: https://github.com/ev3dev/ev3dev-lang
.. _ev3dev-lang-python: https://github.com/rhempel/ev3dev-lang-python
.. _this document: wrapper-specification_
.. _wrapper-specification: https://github.com/ev3dev/ev3dev-lang/blob/develop/wrapper-specification.md
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
.. _pypi-python-ev3dev: https://pypi.python.org/pypi/python-ev3dev
