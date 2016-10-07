#!/usr/bin/env python3

import time
import threading
import ev3dev.ev3 as ev3

def tail_waggler():
    """
    This is the first thread of execution that will be responsible for waggling
    r3ptar's tail every couple of seconds.
    """
    m = ev3.MediumMotor(); assert m.connected

    while True:
        m.run_timed(speed_sp=90, time_sp=1000, stop_action='coast')
        time.sleep(1)
        ev3.Sound.play('rattle-snake.wav').wait()
        m.run_timed(speed_sp=-90, time_sp=1000, stop_action='coast')
        time.sleep(2)

def hand_biter():
    """
    This is the second thread of execution. It will constantly poll the
    infrared sensor for proximity info and bite anything that gets too close.
    """
    m = ev3.LargeMotor('outD'); assert m.connected
    s = ev3.InfraredSensor();   assert s.connected

    m.run_timed(speed_sp=-200, time_sp=1000, stop_action='brake')

    while True:
        # Wait until something (a hand?!) gets too close:
        while s.proximity() > 30: time.sleep(0.1)

        # Bite it! Also, don't forget to hiss:
        ev3.Sound.play('snake-hiss.wav')
        m.run_timed(speed_sp=600, time_sp=500, stop_action='brake')
        time.sleep(0.6)
        m.run_timed(speed_sp=-200, time_sp=500, stop_action='brake')
        time.sleep(1)


# Now that we have the worker functions defined, lets start them both in
# separate threads.
# Actually, we could run just one of those in a separate thread, and call the
# other from our own (master) thread, but this way seems to be more symmetric:
threading.Thread(target=tail_waggler).start()
threading.Thread(target=hand_biter).start()
