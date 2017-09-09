If you do not have the `fake-sys` directory it means you did not use the
`--recursive` option when you git cloned the ev3dev-lang-python repo.
Example:

```
$ git clone --recursive https://github.com/rhempel/ev3dev-lang-python.git
```

Commands used to copy the /sys/class node:

```
$ node=lego-sensor/sensor0
$ mkdir -p ./${node}
$ cp -P --copy-contents -r /sys/class/${node}/* ./${node}/
```

To run the tests do:
```
$ ./api_tests.py
```
