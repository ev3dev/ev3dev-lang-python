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

# Running Tests
To run the tests do:
```
$ cd ev3dev-lang-python/
$ chmod -R g+rw ./tests/fake-sys/devices/**/*
$ python3 -W ignore ./tests/api_tests.py
```
