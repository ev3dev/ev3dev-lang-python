Frequently-Asked Questions
==========================

My script works when launched as ``python3 script.py`` but exits immediately or throws an error when launched from Brickman or as ``./script.py``
-------------------------------------------------------------------------------------------------------------------------------------------------

This may occur if your file includes Windows-style line endings, which are often
inserted by editors on Windows. To resolve this issue, open an SSH session and
run the following command, replacing ``<file>`` with the name of the Python file
you're using:

.. code:: shell

    sed -i 's/\r//g' <file>

This will fix it for the copy of the file on the brick, but if you plan to edit
it again from Windows you should configure your editor to use Unix-style endings.
For PyCharm, you can find a guide on doing this `here <https://www.jetbrains.com/help/pycharm/2016.2/configuring-line-separators.html>`_.
Most other editors have similar options; there may be an option for it in the
status bar at the bottom of the window or in the menu bar at the top.
