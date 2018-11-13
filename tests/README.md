# fake-sys directory
The tests require the fake-sys directory which comes from
https://github.com/ddemidov/ev3dev-lang-fake-sys

If you have already cloned the ev3dev-lang-python repo but do not have the
`fake-sys` directory use `git submodule init` to get it.  If you have not
already cloned the ev3dev-lang-python repo you can use the `--recursive` option
when you git clone.  Example:

```
$ git clone --recursive https://github.com/ev3dev/ev3dev-lang-python.git
```

# Running Tests with CPython (default)
To run the tests:
```
$ cd ev3dev-lang-python/
$ chmod -R g+rw ./tests/fake-sys/devices/**/*
$ python3 -W ignore::ResourceWarning tests/api_tests.py
```

If on Windows, the `chmod` command can be ignored.

# Running Tests with Micropython

This library also supports a subset of functionality on [Micropython](http://micropython.org/).

You can follow the instructions on [the Micropython wiki](https://github.com/micropython/micropython/wiki/Getting-Started)
or check out our [installation script for Travis CI workers](https://github.com/ev3dev/ev3dev-lang-python/blob/ev3dev-stretch/.travis/install-micropython.sh)
to get Micropython installed. If following the official instructions,
make sure you install the relevant micropython-lib modules listed in the linked script as well.

Once Micropython is installed, you can run the tests with:

```
$ cd ev3dev-lang-python/
$ micropython tests/api_tests.py
```
