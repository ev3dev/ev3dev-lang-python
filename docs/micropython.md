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
`ev3dev2.control` [1]_          ⚠️
`ev3dev2.display`               ❌
`ev3dev2.fonts` [2]_            ⚠️
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
.. [2] It might work, but isn't useful without ``ev3dev2.display``.
```

## Differences from standard Python (CPython)

See [the MicroPython differences page](http://docs.micropython.org/en/latest/genrst/index.html) for language information.

### Shebang

You should modify the first line of your scripts to replace "python3" with "micropython":

```
#!/usr/bin/env micropython
```

### Running from the command line

If you previously would have typed `python3 foo.py`, you should now type `micropython foo.py`.