# MINDCUB3R

### Installation
This can take several minutes on an EV3
```
sudo apt-get install build-essential python3-pip libffi-dev
sudo pip3 install git+https://github.com/dwalton76/kociemba.git
sudo pip3 install git+https://github.com/dwalton76/rubiks-color-resolver.git
kociemba DRLUUBFBRBLURRLRUBLRDDFDLFUFUFFDBRDUBRUFLLFDDBFLUBLRBD
```

### Running
./rubiks.py

### About kociemba
You may have noticed that the
`kociemba DRLUUBFBRBLURRLRUBLRDDFDLFUFUFFDBRDUBRUFLLFDDBFLUBLRBD`
step of the install looks a little odd. The "DRLUU..." string is a
representation of the colors of each of the 54 squares of a 3x3x3 cube. So
the D at the beginning means that square #1 is the same color as the middle
square of the Down side (the bottom), the R means that square #2 is the same
color as the middle square of the Right side, etc. The kociemba program takes
that color data and returns a sequence of moves that can be used to solve the
cube.

```
robot@beaglebone[lego-crane-cuber]# kociemba DRLUUBFBRBLURRLRUBLRDDFDLFUFUFFDBRDUBRUFLLFDDBFLUBLRBD
D2 R' D' F2 B D R2 D2 R' F2 D' F2 U' B2 L2 U2 D R2 U
robot@beaglebone[lego-crane-cuber]#
```

Running the kociemba program is part of the install process because the first
time you run it, it takes about 30 seconds to build a series of tables that
it caches to the filesystem.  After that first run it is nice and fast.
