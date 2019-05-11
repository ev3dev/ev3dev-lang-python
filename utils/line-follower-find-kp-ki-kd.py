
"""
This program is used to find the kp, ki, kd PID values for
`MoveTank.follow_line()`. These values vary from robot to robot, the best way
to find them for your robot is to have it follow a line, tweak the values a
little, repeat.

The default speed for this program is SpeedPercent(30).  You can use whatever
speed you want, just search for "speed = SpeedPercent(30)" in this file and
modigy that line.

You can use the pdf from this site to print a line that makes an oval, just
have your robot follow that oval when running this program.
http://robotsquare.com/2012/11/28/line-following/
"""

from ev3dev2.motor import OUTPUT_A, OUTPUT_B, MoveTank, SpeedPercent, LineFollowFailed
from ev3dev2.sensor.lego import ColorSensor
from time import sleep
import datetime as dt
import logging
import sys


start_time = None


def follow_for_10s(_tank):
    """
    Return True if we have been following the line for less than 10s.
    Return False if we have been following the line for 10s or more.
    """
    global start_time

    if start_time is None:
        start_time = dt.datetime.now()

    delta = dt.datetime.now() - start_time
    delta_ms = delta.total_seconds() * 1000

    if delta_ms >= 10000:
        return False
    else:
        return True


def frange(start, end, increment):
    """
    range() does not support floats, this frange() does
    """
    result = []
    x = start

    while x < end:
        result.append(x)
        x += increment

    return result


def find_kp_ki_kd(start, end, increment, speed, kx_to_tweak, kp, ki, kd):
    """
    Return the optimal `kx_to_tweak` value where `kx_to_tweak` must be "kp", "ki" or "kd"
    This will test values from `start` to `end` in steps of `increment`. The value
    that results in the robot moving the least total distance is the optimal value
    that is returned by this function.
    """
    global start_time
    min_delta = None
    min_delta_kx = None

    for kx in frange(start, end, increment):
        log.info("%s %s: place robot on line, then press <ENTER>" % (kx_to_tweak, kx))
        input("")
        init_left_motor_pos = tank.left_motor.position
        start_time = None

        try:
            if kx_to_tweak == "kp":
                tank.follow_line(
                    kp=kx, ki=ki, kd=kd,
                    speed=speed,
                    keep_following_function=follow_for_10s
                )

            elif kx_to_tweak == "ki":
                tank.follow_line(
                    kp=kp, ki=kx, kd=kd,
                    speed=speed,
                    keep_following_function=follow_for_10s
                )

            elif kx_to_tweak == "kd":
                tank.follow_line(
                    kp=kp, ki=ki, kd=kx,
                    speed=speed,
                    keep_following_function=follow_for_10s
                )

            else:
                raise Exception("Invalid kx_to_tweak %s" % kx_to_tweak)

        except LineFollowFailed:
            continue

        except:
            tank.stop()
            raise

        final_left_motor_pos = tank.left_motor.position
        delta_left_motor_pos = abs(final_left_motor_pos - init_left_motor_pos)

        if min_delta is None or delta_left_motor_pos < min_delta:
            min_delta = delta_left_motor_pos
            min_delta_kx = kx
            log.info("%s: %s %s, left motor moved %s (NEW MIN)" % (tank, kx_to_tweak, kx, delta_left_motor_pos))
        else:
            log.info("%s: %s %s, left motor moved %s" % (tank, kx_to_tweak, kx, delta_left_motor_pos))

    tank.stop()
    return min_delta_kx


if __name__ == "__main__":

    # logging
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(levelname)5s: %(message)s")
    log = logging.getLogger(__name__)

    tank = MoveTank(OUTPUT_A, OUTPUT_B)
    tank.cs = ColorSensor()

    speed = SpeedPercent(30)

    # Find the best integer for kp (in increments of 1) then fine tune by
    # finding the best float (in increments of 0.1)
    kp = find_kp_ki_kd(1, 20, 1, speed, 'kp', 0, 0, 0)
    kp = find_kp_ki_kd(kp - 1, kp + 1, 0.1, 'kp', kp, 0, 0)
    print("\n\n\n%s\nkp %s\n%s\n\n\n" % ("" * 10, kp, "*" * 10))

    # Find the best float ki (in increments of 0.1)
    ki = find_kp_ki_kd(0, 1, 0.1, speed, 'ki', kp, 0, 0)
    print("\n\n\n%s\nki %s\n%s\n\n\n" % ("" * 10, ki, "*" * 10))

    # Find the best integer for kd (in increments of 1) then fine tune by
    # finding the best float (in increments of 0.1)
    kd = find_kp_ki_kd(0, 10, 1, speed, 'kd', kp, ki, 0)
    kd = find_kp_ki_kd(kd - 1, kd + 1, 0.1, speed, 'kd', kp, ki, 0)
    print("\n\n\n%s\nkd %s\n%s\n\n\n" % ("" * 10, kd, "*" * 10))

    print("Final results: kp %s, ki %s, kd %s" % (kp, ki, kd))
