Frequently-Asked Questions
==========================

Q: Why does my Python program exit quickly or immediately throw an error?
    A: This may occur if your file includes Windows-style line endings
    (CRLF--carriage-return line-feed), which are often inserted by editors on
    Windows. To resolve this issue, open an SSH session and run the following
    command, replacing ``<file>`` with the name of the Python file you're
    using:

    .. code:: shell

        sed -i 's/\r//g' <file>

    This will fix it for the copy of the file on the brick, but if you plan to edit
    it again from Windows, you should configure your editor to use Unix-style
    line endings (LF--line-feed). For PyCharm, you can find a guide on doing this
    `here <https://www.jetbrains.com/help/pycharm/2016.2/configuring-line-separators.html>`_.
    Most other editors have similar options; there may be an option for it in the
    status bar at the bottom of the window or in the menu bar at the top.

Q: Where can I learn more about the ev3dev operating system?
    A: `ev3dev.org`_ is a great resource for finding guides and tutorials on
    using ev3dev, straight from the maintainers.

Q: How can I request support on the ev3dev2 Python library?
    A: If you are having trouble using this library, please open an issue
    at `our Issues tracker`_ so that we can help you. When opening an
    issue, make sure to include as much information as possible about
    what you are trying to do and what you have tried. The issue template
    is in place to guide you through this process.

Q: How can I upgrade the library on my EV3?
    A: You can upgrade this library from an Internet-connected EV3 with an
    SSH shell as follows. Make sure to type the password
    (the default is ``maker``) when prompted.

    .. code-block:: bash

        sudo apt-get update
        sudo apt-get install --only-upgrade python3-ev3dev2 micropython-ev3dev2

Q: Are there other useful Python modules to use on the EV3?
    A: The Python language has a `package repository`_ where you can find
    libraries that others have written, including the `latest version of
    this package`_.

Q: What compatibility issues are there with the different versions of Python?
    A: Some versions of the ev3dev_ distribution come with
    `Python 2.x`_, `Python 3.x`_, and `micropython`_ installed,
    but this library is compatible only with Python 3 and micropython.

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
.. _our Issues tracker: https://github.com/ev3dev/ev3dev-lang-python/issues
.. _EXPLOR3R: demo-robot_
.. _demo-robot: http://robotsquare.com/2015/10/06/explor3r-building-instructions/
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
.. _Micropython: http://python-ev3dev.readthedocs.io/en/ev3dev-stretch/micropython.html
