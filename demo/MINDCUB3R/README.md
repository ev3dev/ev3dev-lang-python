Installation
===============
cd ~/ev3dev-lang-python/demo/MINDCUB3R/kociemba/ckociemba/

# This can take a minute on an EV3
sudo apt-get update
sudo apt-get install build-essential
make
sudo make install

# The first time you run this it has to create a cache
# directory, this takes about 30s on an EV3

cd ~/ev3dev-lang-python/demo/MINDCUB3R/
kociemba DRLUUBFBRBLURRLRUBLRDDFDLFUFUFFDBRDUBRUFLLFDDBFLUBLRBD


Running
=======
./rubiks.py


Credit
======
Much of rubiks.py and rubiks_rgb_solver.py were ported from
https://github.com/cavenel/ev3dev_examples

The kociemba code is from
https://github.com/muodov/kociemba
