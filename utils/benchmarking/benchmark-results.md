# Historical I/O benchmark results

Procedure: Use an EV3. Disconnect all peripherals, including Wi-Fi. Connect one large EV3 motor. Cold-boot the EV3 and
leave it for around five minutes to make sure all services have loaded. Execute `io-benchmark.sh` from the Brickman
interface. Then grab the `benchmark.txt` file from the same directory.

TODO: instructions for installing from sources with Makefile?

## `2.1.0` release
System info:
```
Image file:         ev3dev-stretch-ev3-generic-2019-05-29
Kernel version:     4.14.117-ev3dev-2.3.4-ev3
Brickman:           0.10.1
BogoMIPS:           148.88
Bluetooth:          
Board:              board0
BOARD_INFO_HW_REV=7
BOARD_INFO_MODEL=LEGO MINDSTORMS EV3
BOARD_INFO_ROM_REV=6
BOARD_INFO_SERIAL_NUM=00165340720B
BOARD_INFO_TYPE=main
```

Benchmark results:
```
Using interpreter python3; found ev3dev2 version 2.1.0 from /usr/lib/python3/dist-packages/ev3dev2
Motor read address:
1000 loops, best of 3: 970 usec per loop
Motor read speed_sp:
1000 loops, best of 3: 1.1 msec per loop
Motor read count_per_rot (cached):
1000 loops, best of 3: 215 usec per loop
Motor write speed_sp:
1000 loops, best of 3: 1.12 msec per loop
Using interpreter micropython; found ev3dev2 version 2.1.0 from /usr/lib/micropython/ev3dev2
Motor read address:
1000 loops, best of 3: 1.21 msec per loop
Motor read speed_sp:
1000 loops, best of 3: 1.17 msec per loop
Motor read count_per_rot (cached):
10000 loops, best of 3: 144 usec per loop
Motor write speed_sp:
1000 loops, best of 3: 1.08 msec per loop
```