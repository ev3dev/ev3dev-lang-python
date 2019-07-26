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
`ev3dev2.fonts` [3]_            ❌
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
.. [2] ``ev3dev2.display`` isn't implemented. Use ``ev3dev2.console`` for text-only, using ANSI codes to the EV3 LCD console.
.. [3] ``ev3dev2.console`` supports the system fonts, but the fonts for ``ev3dev2.display`` do not work.
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

If you are running programs via an SSH shell to your EV3, use the following command line to
prevent Brickman from interfering:

```shell
brickrun -- ./program.py
```
