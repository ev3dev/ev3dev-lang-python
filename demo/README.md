# ev3dev demo programs

This folder contains several demo programs that you can use to help you in
developing your own code. Brief descriptions of each demo are provided below;
you can access the full source code and some more detailed information on each
by opening the respective folders above.

To install these on your EV3, use git to clone the ev3dev-lang-python repository
from github. Your EV3 will need Internet connectivty in order to clone the
repository from github.
```
$ sudo apt-get install git
$ git clone https://github.com/rhempel/ev3dev-lang-python.git
```

## Running A Program
There are two ways to run a program. You can run a program from the command line
or from the brickman interface.

Note that for both running from the command line and running from Brickman the
program **must be marked as an executable** and the **first line of the program
must be** `#!/usr/bin/env python3`. To mark a program as executable run
`chmod +x PROGRAM_NAME.py`. All of the demo programs are already marked as
executable and already have `#!/usr/bin/env python3` so you should be fine, we
only mention it so you know to do these things when writing your own programs.

## Command Line
To run one of the demo programs from the command line, cd to the directory and
run the program via `./PROGRAM_NAME.py`. Example:
```
$ cd ev3dev-lang-python/demo/R3PTAR/
$ ./r3ptar.py
```
## Brickman
To run one of the demo programs from Brickman, select the program in the
File Browser.

## Demo Programs
### BALANC3R

Laurens Valk's BALANC3R - This robot uses the gyro sensor to balance on two
wheels. Use the IR remote to control BALANC3R

* http://robotsquare.com/2014/07/01/tutorial-ev3-self-balancing-robot/

### EV3D4

* http://www.lego.com/en-us/mindstorms/build-a-robot/ev3d4
* EV3D4RemoteControl - Use the IR remote to control EV3D4
* EV3D4WebControl - Use a web interface to control EV3D4. There is a desktop version and a mobile version, both support touchscreen so you can drive via your smartphone. The web server will listen on port 8000 so go to http://x.x.x.x:8000/

### EXPLOR3R

Lauren Valk's EXPLOR3R

* http://robotsquare.com/2015/10/06/explor3r-building-instructions/

### MINDCUB3R

David Gilday's MINDCUB3R

* http://mindcuber.com/

### TRACK3R

A basic example of Object Oriented programming where there is a base TRACK3R
class with child classes for the various permutations of TRACK3R

* http://www.lego.com/en-us/mindstorms/build-a-robot/track3r
* TRACK3R.py
* TRACK3RWithBallShooter
* TRACK3RWithClaw
* TRACK3RWithSpinner
