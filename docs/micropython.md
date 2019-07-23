# Using python-ev3dev with MicroPython

The core modules of this library are shipped as a module for [MicroPython](https://micropython.org/),
which is faster to load and run on the EV3. If your app only requires functionality supported on
MicroPython, we recommend you run your code with it for improved performance.

## Module support

```eval_rst
==============================  =================
Module                          Support status
==============================  =================
`ev3dev2.button`                ️️✔️
`ev3dev2.console`               ✔️️
`ev3dev2.control` [1]_          ⚠️
`ev3dev2.display` [2]_          ❌
`ev3dev2.fonts` [3]_            ⚠️
`ev3dev2.led`                   ✔️
`ev3dev2.motor`                 ✔️
`ev3dev2.port`                  ✔️
`ev3dev2.power`                 ✔️
`ev3dev2.sensor.*`              ✔️
`ev3dev2.sound`                 ✔️
`ev3dev2.unit`                  ✔️
`ev3dev2.wheel`                 ✔️
==============================  =================

.. [1] Untested/low-priority, but some of it might work.
.. [2] Display() isn't implemented. Use ``ev3dev2.console`` for text-only, using ANSI codes to the EV3 LCD console.
.. [3] It might work, but isn't useful without ``ev3dev2.display``.
```

## Differences from standard Python (CPython)

See [the MicroPython differences page](http://docs.micropython.org/en/latest/genrst/index.html) for language information.

### Shebang

You should modify the first line of your scripts to replace "python3" with "micropython":

```python
#!/usr/bin/env micropython
```

### Running from the command line

If you previously would have typed `python3 foo.py`, you should now type `micropython foo.py`.

If you are running programs via an SSH shell, use the following command line to inform Brickman that your
program needs control of the EV3:

```shell
brickrun -- ./program.py
```

### Displaying text on the EV3 LCD console

The EV3 LCD console supports ANSI codes to position the cursor, clear the screen, show text with different fonts,
and use reverse (white text on black background, versus the default black text on white background). See the file
`utils/console_fonts.py` to see the fonts supported with sample calls to the `ev3dev2.Console()` class.

### Building and installing the latest EV3DEV2 module on your EV3

In an SSH Terminal window with an EV3 with Internet access, run the following commands:
(recall that the `sudo` password is `maker`)

```shell
git clone https://github.com/ev3dev/ev3dev-lang-python.git
cd ev3dev-lang-python
sudo make micropython-install
```

To update the module, use the following commands:

```shell
cd ev3dev-lang-python
git pull
sudo make micropython-install
```
