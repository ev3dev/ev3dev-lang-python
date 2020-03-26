#!/bin/bash

exec &> >(tee benchmark.txt)

do_benchmark() {
    PYTHON=$1

    VERSION=$($PYTHON -c "import ev3dev2; print(ev3dev2.__version__)")
    MODULE_PATH=$($PYTHON -c "import ev3dev2; print(ev3dev2.__path__[0] if isinstance(ev3dev2.__path__, list) else ev3dev2.__path__)")

    echo "Using interpreter $PYTHON; found ev3dev2 version $VERSION from $MODULE_PATH"

    echo "Motor read address:"
    $PYTHON -m timeit -s "from ev3dev2.motor import Motor; m = Motor()" "m.address"
    
    echo "Motor read speed_sp:"
    $PYTHON -m timeit -s "from ev3dev2.motor import Motor; m = Motor()" "m.speed_sp"

    echo "Motor read count_per_rot (cached):"
    $PYTHON -m timeit -s "from ev3dev2.motor import Motor; m = Motor()" "m.count_per_rot"
    
    echo "Motor write speed_sp:"
    $PYTHON -m timeit -s "from ev3dev2.motor import Motor; m = Motor()" "m.speed_sp = 5"
}

do_benchmark python3
do_benchmark micropython
