#!/usr/bin/env python3

import time
import threading
import signal
import ev3dev.ev3 as ev3

def tail_waggler(done):
    """
    This is the first thread of execution that will be responsible for waggling
    r3ptar's tail every couple of seconds.
    """
    m = ev3.MediumMotor(); assert m.connected

    while not done.is_set():
        m.run_timed(speed_sp=90, time_sp=1000, stop_action='coast')
        time.sleep(1)
        ev3.Sound.play('rattle-snake.wav').wait()
        m.run_timed(speed_sp=-90, time_sp=1000, stop_action='coast')
        time.sleep(2)

def hand_biter(done):
    """
    This is the second thread of execution. It will constantly poll the
    infrared sensor for proximity info and bite anything that gets too close.
    """
    m = ev3.LargeMotor('outD'); assert m.connected
    s = ev3.InfraredSensor();   assert s.connected

    m.run_timed(speed_sp=-200, time_sp=1000, stop_action='brake')

    while not done.is_set():
        # Wait until something (a hand?!) gets too close:
        while s.proximity > 30:
            if done.is_set(): return
            time.sleep(0.1)

        # Bite it! Also, don't forget to hiss:
        ev3.Sound.play('snake-hiss.wav')
        m.run_timed(speed_sp=600, time_sp=500, stop_action='brake')
        time.sleep(0.6)
        m.run_timed(speed_sp=-200, time_sp=500, stop_action='brake')
        time.sleep(1)

# The 'done' event will be used to signal the threads to stop:
done = threading.Event()

# We also need to catch SIGINT (keyboard interrup) and SIGTERM (termination
# signal from brickman) and exit gracefully:
def signal_handler(signal, frame):
    done.set()

signal.signal(signal.SIGINT,  signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Now that we have the worker functions defined, lets run those in separate
# threads.
tail = threading.Thread(target=tail_waggler, args=(done,))
head = threading.Thread(target=hand_biter,   args=(done,))

tail.start()
head.start()

# The main thread will wait for the 'back' button to be pressed.  When that
# happens, it will signal the worker threads to stop and wait for their
# completion.
btn = ev3.Button()
while not btn.backspace and not done.is_set():
    time.sleep(0.1)

done.set()
tail.join()
head.join()
