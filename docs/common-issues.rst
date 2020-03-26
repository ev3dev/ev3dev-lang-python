Common Issues with ev3dev-lang-python
=====================================

``ImportError: No module named ev3dev2``
----------------------------------------

This likely means you are running the script on your computer rather than on the
EV3 (or other ev3dev platform). You can do so using our `Visual Studio Code extension`_
by connecting to a device in the 

``/usr/bin/env: 'python3\r': No such file or directory``
--------------------------------------------------------

This means your file includes Windows-style line endings
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
In Visual Studio Code, there is an option in the lower-right corner.
Most other editors have similar options; there may be an option for it in the
status bar at the bottom of the window or in the menu bar at the top.


``Exception: Unsupported platform 'None'``
------------------------------------------

You probably forgot to `update config.txt`_.

.. _update config.txt: https://www.ev3dev.org/docs/getting-started/#step-3a-raspberry-pi-only-update-options-in-configtxt
.. _Visual Studio Code extension: https://github.com/ev3dev/vscode-ev3dev-browser