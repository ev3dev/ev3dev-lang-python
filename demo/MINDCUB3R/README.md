# MINDCUB3R

## Installation
### Installing kociemba
The kociemba program produces a sequence of moves used to solve
a 3x3x3 rubiks cube.
```
$ sudo apt-get install build-essential libffi-dev
$ cd ~/
$ git clone https://github.com/dwalton76/kociemba.git
$ cd ~/kociemba/kociemba/ckociemba/
$ make
$ sudo make install
```

### Installing rubiks-color-resolver
When the cube is scanned we get the RGB (red, green, blue) value for
all 54 squares of a 3x3x3 cube.  rubiks-color-resolver analyzes those RGB
values to determine which of the six possible cube colors is the color for
each square.
```
$ sudo apt-get install python3-pip
$ sudo pip3 install git+https://github.com/dwalton76/rubiks-color-resolver.git
```

### Installing the MINDCUB3R demo
We must git clone the ev3dev-lang-python repository.  MINDCUB3R is included
in the demo directory.
```
$ cd ~/
$ git clone https://github.com/rhempel/ev3dev-lang-python.git
$ cd ~/ev3dev-lang-python/demo/MINDCUB3R/
$ kociemba DRLUUBFBRBLURRLRUBLRDDFDLFUFUFFDBRDUBRUFLLFDDBFLUBLRBD
```

## Running MINDCUB3R
```
$ cd ~/ev3dev-lang-python/demo/MINDCUB3R/
$ ./rubiks.py
```

## About kociemba
You may have noticed that the
`kociemba DRLUUBFBRBLURRLRUBLRDDFDLFUFUFFDBRDUBRUFLLFDDBFLUBLRBD`
step of the install looks a little odd. The "DRLUU..." string is a
representation of the colors of each of the 54 squares of a 3x3x3 cube. So
the D at the beginning means that square `#1` is the same color as the middle
square of the Down side (the bottom), the R means that square `#2` is the same
color as the middle square of the Right side, etc. The kociemba program takes
that color data and returns a sequence of moves that can be used to solve the
cube.

```
$ kociemba DRLUUBFBRBLURRLRUBLRDDFDLFUFUFFDBRDUBRUFLLFDDBFLUBLRBD
D2 R' D' F2 B D R2 D2 R' F2 D' F2 U' B2 L2 U2 D R2 U
$
```

Running the kociemba program is part of the install process because the first
time you run it, it takes about 30 seconds to build a series of tables that
it caches to the filesystem.  After that first run it is nice and fast.
