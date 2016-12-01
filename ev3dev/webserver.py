#!/usr/bin/env python3

import logging
import math
import os
import re
import sys
import time
import ev3dev.auto
from ev3dev.helper import Tank, list_motors
from http.server import BaseHTTPRequestHandler, HTTPServer
from time import sleep

log = logging.getLogger(__name__)


# ===============================================
# "Joystick" code for the web interface for tanks
# ===============================================
def angle_to_speed_percentage(angle):
    """
                            (1, 1)
                         . . . . . . .
                      .        |        .
                   .           |           .
          (0, 1) .             |             . (1, 0)
               .               |               .
              .                |                 .
             .                 |                  .
            .                  |                   .
           .                   |                   .
           .                   |     x-axis        .
   (-1, 1) .---------------------------------------. (1, -1)
           .                   |                   .
           .                   |                   .
            .                  |                  .
             .                 | y-axis          .
               .               |               .
         (0, -1) .             |             . (-1, 0)
                   .           |           .
                      .        |        .
                         . . . . . . .
                            (-1, -1)


    The joystick is a circle within a circle where the (x, y) coordinates
    of the joystick form an angle with the x-axis.  Our job is to translate
    this angle into the percentage of power that should be sent to each motor.
    For instance if the joystick is moved all the way to the top of the circle
    we want both motors to move forward with 100% power...that is represented
    above by (1, 1).  If the joystick is moved all the way to the right side of
    the circle we want to rotate clockwise so we move the left motor forward 100%
    and the right motor backwards 100%...so (1, -1).  If the joystick is at
    45 degrees then we move apply (1, 0) to move the left motor forward 100% and
    the right motor stays still.

    The 8 points shown above are pretty easy. For the points in between those 8
    we do some math to figure out what the percentages should be. Take 11.25 degrees
    for example. We look at how the motors transition from 0 degrees to 45 degrees:
    - the left motor is 1 so that is easy
    - the right motor moves from -1 to 0

    We determine how far we are between 0 and 45 degrees (11.25 is 25% of 45) so we
    know that the right motor should be 25% of the way from -1 to 0...so -0.75 is the
    percentage for the right motor at 11.25 degrees.
    """

    if angle >= 0 and angle <= 45:

        # left motor stays at 1
        left_speed_percentage = 1

        # right motor transitions from -1 to 0
        right_speed_percentage = -1 + (angle/45.0)

    elif angle > 45 and angle <= 90:

        # left motor stays at 1
        left_speed_percentage = 1

        # right motor transitions from 0 to 1
        percentage_from_45_to_90 = (angle - 45) / 45.0
        right_speed_percentage = percentage_from_45_to_90

    elif angle > 90 and angle <= 135:

        # left motor transitions from 1 to 0
        percentage_from_90_to_135 = (angle - 90) / 45.0
        left_speed_percentage = 1 - percentage_from_90_to_135

        # right motor stays at 1
        right_speed_percentage = 1

    elif angle > 135 and angle <= 180:

        # left motor transitions from 0 to -1
        percentage_from_135_to_180 = (angle - 135) / 45.0
        left_speed_percentage = -1 * percentage_from_135_to_180

        # right motor stays at 1
        right_speed_percentage = 1

    elif angle > 180 and angle <= 225:

        # left motor transitions from -1 to 0
        percentage_from_180_to_225 = (angle - 180) / 45.0
        left_speed_percentage = -1 + percentage_from_180_to_225

        # right motor transitions from 1 to -1
        # right motor transitions from 1 to 0 between 180 and 202.5
        if angle < 202.5:
            percentage_from_180_to_202 = (angle - 180) / 22.5
            right_speed_percentage = 1 - percentage_from_180_to_202

        # right motor is 0 at 202.5
        elif angle == 202.5:
            right_speed_percentage = 0

        # right motor transitions from 0 to -1 between 202.5 and 225
        else:
            percentage_from_202_to_225 = (angle - 202.5) / 22.5
            right_speed_percentage = -1 * percentage_from_202_to_225

    elif angle > 225 and angle <= 270:

        # left motor transitions from 0 to -1
        percentage_from_225_to_270 = (angle - 225) / 45.0
        left_speed_percentage = -1 * percentage_from_225_to_270

        # right motor stays at -1
        right_speed_percentage = -1

    elif angle > 270 and angle <= 315:

        # left motor stays at -1
        left_speed_percentage = -1

        # right motor transitions from -1 to 0
        percentage_from_270_to_315 = (angle - 270) / 45.0
        right_speed_percentage = -1 + percentage_from_270_to_315

    elif angle > 315 and angle <= 360:

        # left motor transitions from -1 to 1
        # left motor transitions from -1 to 0 between 315 and 337.5
        if angle < 337.5:
            percentage_from_315_to_337 = (angle - 315) / 22.5
            left_speed_percentage = (1 - percentage_from_315_to_337) * -1

        # left motor is 0 at 337.5
        elif angle == 337.5:
            left_speed_percentage = 0

        # left motor transitions from 0 to 1 between 337.5 and 360
        elif angle > 337.5:
            percentage_from_337_to_360 = (angle - 337.5) / 22.5
            left_speed_percentage = percentage_from_337_to_360

        # right motor transitions from 0 to -1
        percentage_from_315_to_360 = (angle - 315) / 45.0
        right_speed_percentage = -1 * percentage_from_315_to_360

    else:
        raise Exception('You created a circle with more than 360 degrees (%s)...that is quite the trick' % angle)

    return (left_speed_percentage, right_speed_percentage)


def xy_to_speed(x, y, max_speed, radius=100.0):
    """
    Convert x,y joystick coordinates to left/right motor speed
    """

    vector_length = math.hypot(x, y)
    angle = math.degrees(math.atan2(y, x))

    if angle < 0:
        angle += 360

    # Should not happen but can happen (just by a hair) due to floating point math
    if vector_length > radius:
        vector_length = radius

    # print "radius        : %s" % radius
    # print "angle         : %s" % angle
    # print "vector length : %s" % vector_length

    (left_speed_percentage, right_speed_percentage) = angle_to_speed_percentage(angle)
    # print "init   left_speed_percentage: %s" % left_speed_percentage
    # print "init  right_speed_percentage: %s" % right_speed_percentage

    # scale the speed percentages based on vector_length vs. radius
    left_speed_percentage = (left_speed_percentage * vector_length) / radius
    right_speed_percentage = (right_speed_percentage * vector_length) / radius
    # print "final  left_speed_percentage: %s" % left_speed_percentage
    # print "final right_speed_percentage: %s" % right_speed_percentage

    # calculate the motor speeds based on speed percentages and max_speed of the motors
    left_speed = round(left_speed_percentage * max_speed)
    right_speed = round(right_speed_percentage * max_speed)

    # safety net
    if left_speed > max_speed:
        left_speed = max_speed

    if right_speed > max_speed:
        right_speed = max_speed

    return (left_speed, right_speed)


def test_xy_to_speed():
    """
    Used to test changes to xy_to_speed() and angle_to_speed_percentage()
    """

    # Move straight forward
    assert xy_to_speed(0, 100, 400) == (400, 400), "FAILED"

    # Spin clockwise
    assert xy_to_speed(100, 0, 400) == (400, -400), "FAILED"

    # Spin counter clockwise
    assert xy_to_speed(-100, 0, 400) == (-400, 400), "FAILED"

    # Move straight back
    assert xy_to_speed(0, -100, 400) == (-400, -400), "FAILED"

    # Test vector length to power percentages
    # Move straight forward, 1/2 power
    assert xy_to_speed(0, 50, 400) == (200, 200), "FAILED"

    # Test motor max_speed
    # Move straight forward, 1/2 power with lower max_speed
    assert xy_to_speed(0, 50, 200) == (100, 100), "FAILED"

    # http://www.pagetutor.com/trigcalc/trig.html

    # top right quadrant
    # ==================
    # 0 -> 45 degrees
    assert xy_to_speed(98.07852804032305, 19.509032201612825, 400) == (400, -300), "FAILED" # 11.25 degrees
    assert xy_to_speed(92.38795325112868, 38.26834323650898, 400) == (400, -200), "FAILED" # 22.5 degrees
    assert xy_to_speed(83.14696123025452, 55.557023301960214, 400) == (400, -100), "FAILED" # 33.75 degrees

    # 45 degrees, only left motor should turn
    assert xy_to_speed(70.71068, 70.71068, 400) == (400, 0), "FAILED"

    # 45 -> 90 degrees
    assert xy_to_speed(55.55702330196023, 83.14696123025452, 400) == (400, 100), "FAILED" # 56.25 degrees
    assert xy_to_speed(38.26834323650898, 92.38795325112868, 400) == (400, 200), "FAILED" # 67.5 degrees
    assert xy_to_speed(19.509032201612833, 98.07852804032305, 400) == (400, 300), "FAILED" # 78.75 degrees


    # top left quadrant
    # =================
    # 90 -> 135 degrees
    assert xy_to_speed(-19.509032201612833, 98.07852804032305, 400) == (300, 400), "FAILED"
    assert xy_to_speed(-38.26834323650898, 92.38795325112868, 400) == (200, 400), "FAILED"
    assert xy_to_speed(-55.55702330196023, 83.14696123025452, 400) == (100, 400), "FAILED"

    # 135 degrees, only right motor should turn
    assert xy_to_speed(-70.71068, 70.71068, 400) == (0, 400), "FAILED"

    # 135 -> 180 degrees
    assert xy_to_speed(-83.14696123025452, 55.55702330196023, 400) == (-100, 400), "FAILED"
    assert xy_to_speed(-92.38795325112868, 38.26834323650898, 400) == (-200, 400), "FAILED"
    assert xy_to_speed(-98.07852804032305, 19.509032201612833, 400) == (-300, 400), "FAILED"


    # bottom left quadrant
    # ====================
    # 180 -> 225 degrees
    assert xy_to_speed(-98.07852804032305, -19.509032201612833, 400) == (-300, 200), "FAILED"
    assert xy_to_speed(-92.38795325112868, -38.26834323650898, 400) == (-200, 0), "FAILED"
    assert xy_to_speed(-83.14696123025452, -55.55702330196023, 400) == (-100, -200), "FAILED"

    # 225 degrees, only right motor should turn (backwards)
    assert xy_to_speed(-70.71068, -70.71068, 400) == (0, -400), "FAILED"

    # 225 -> 270 degrees
    assert xy_to_speed(-55.55702330196023, -83.14696123025452, 400) == (-100, -400), "FAILED"
    assert xy_to_speed(-38.26834323650898, -92.38795325112868, 400) == (-200, -400), "FAILED"
    assert xy_to_speed(-19.509032201612833, -98.07852804032305, 400) == (-300, -400), "FAILED"


    # bottom right quadrant
    # =====================
    # 270 -> 315 degrees
    assert xy_to_speed(19.509032201612833, -98.07852804032305, 400) == (-400, -300), "FAILED"
    assert xy_to_speed(38.26834323650898, -92.38795325112868, 400) == (-400, -200), "FAILED"
    assert xy_to_speed(55.55702330196023, -83.14696123025452, 400) == (-400, -100), "FAILED"

    # 315 degrees, only left motor should turn (backwards)
    assert xy_to_speed(70.71068, -70.71068, 400) == (-400, 0), "FAILED"

    # 315 -> 360 degrees
    assert xy_to_speed(83.14696123025452, -55.557023301960214, 400) == (-200, -100), "FAILED"
    assert xy_to_speed(92.38795325112868, -38.26834323650898, 400) == (0, -200), "FAILED"
    assert xy_to_speed(98.07852804032305, -19.509032201612825, 400) == (200, -300), "FAILED"


# ==================
# Web Server classes
# ==================
class RobotWebHandler(BaseHTTPRequestHandler):
    """
    Base WebHandler class for various types of robots.

    RobotWebHandler's do_GET() will serve files, it is up to the child
    class to handle REST APIish GETs via their do_GET()

    self.robot is populated in RobotWebServer.__init__()
    """

    # File extension to mimetype
    mimetype = {
        'css'  : 'text/css',
        'gif'  : 'image/gif',
        'html' : 'text/html',
        'ico'  : 'image/x-icon',
        'jpg'  : 'image/jpg',
        'js'   : 'application/javascript',
        'png'  : 'image/png'
    }

    def do_GET(self):
        """
        If the request is for a known file type serve the file (or send a 404) and return True
        """

        if self.path == "/":
            self.path = "/index.html"

        # Serve a file (image, css, html, etc)
        if '.' in self.path:
            extension = self.path.split('.')[-1]
            mt = self.mimetype.get(extension)

            if mt:
                filename = os.curdir + os.sep + self.path

                # Open the static file requested and send it
                if os.path.exists(filename):
                    self.send_response(200)
                    self.send_header('Content-type', mt)
                    self.end_headers()

                    if extension in ('gif', 'ico', 'jpg', 'png'):
                        # Open in binary mode, do not encode
                        with open(filename, mode='rb') as fh:
                            self.wfile.write(fh.read())
                    else:
                        # Open as plain text and encode
                        with open(filename, mode='r') as fh:
                            self.wfile.write(fh.read().encode())
                else:
                    log.error("404: %s not found" % self.path)
                    self.send_error(404, 'File Not Found: %s' % self.path)
                return True

        return False

    def log_message(self, format, *args):
        """
        log using our own handler instead of BaseHTTPServer's
        """
        # log.debug(format % args)
        pass


max_move_xy_seq = 0
motor_max_speed = None
medium_motor_max_speed = None
joystick_enaged = False

class TankWebHandler(RobotWebHandler):

    def __str__(self):
        return "%s-TankWebHandler" % self.robot

    def do_GET(self):
        """
        Returns True if the requested URL is supported
        """

        if RobotWebHandler.do_GET(self):
            return True

        global motor_max_speed
        global medium_motor_max_speed
        global max_move_xy_seq
        global joystick_engaged

        if medium_motor_max_speed is None:
            motor_max_speed = self.robot.left_motor.max_speed

            if hasattr(self.robot, 'medium_motor'):
                medium_motor_max_speed = self.robot.medium_motor.max_speed
            else:
                medium_motor_max_speed = 0

        '''
        Sometimes we get AJAX requests out of order like this:
        2016-09-06 02:29:35,846 DEBUG: seq 65: (x, y): 0, 44 -> speed 462 462
        2016-09-06 02:29:35,910 DEBUG: seq 66: (x, y): 0, 45 -> speed 473 473
        2016-09-06 02:29:35,979 DEBUG: seq 67: (x, y): 0, 46 -> speed 483 483
        2016-09-06 02:29:36,033 DEBUG: seq 69: (x, y): -1, 48 -> speed 491 504
        2016-09-06 02:29:36,086 DEBUG: seq 68: (x, y): -1, 47 -> speed 480 494
        2016-09-06 02:29:36,137 DEBUG: seq 70: (x, y): -1, 49 -> speed 501 515
        2016-09-06 02:29:36,192 DEBUG: seq 73: (x, y): -2, 51 -> speed 509 536
        2016-09-06 02:29:36,564 DEBUG: seq 74: (x, y): -3, 51 -> speed 496 536
        2016-09-06 02:29:36,649  INFO: seq 75: CLIENT LOG: touchend
        2016-09-06 02:29:36,701 DEBUG: seq 71: (x, y): -1, 50 -> speed 512 525
        2016-09-06 02:29:36,760 DEBUG: seq 76: move stop
        2016-09-06 02:29:36,814 DEBUG: seq 72: (x, y): -1, 51 -> speed 522 536

        This can be bad because the last command sequentially was #76 which was "move stop"
        but we RXed seq #72 after that so we started moving again and never stopped

        A quick fix is to have the client send us an AJAX request to let us know
        when the joystick has been engaged so that we can ignore any move-xy events
        that we get out of order and show up after "move stop" but before the
        next "joystick-engaged"

        We can also ignore any move-xy requests that show up late by tracking the
        max seq for any move-xy we service.
        '''
        # dwalton - fix this

        path = self.path.split('/')
        seq = int(path[1])
        action = path[2]

        # desktop interface
        if action == 'move-start':
            direction = path[3]
            speed_percentage = path[4]
            log.debug("seq %d: move %s" % (seq, direction))

            left_speed = int(int(speed_percentage) * motor_max_speed)/100.0
            right_speed = int(int(speed_percentage) * motor_max_speed)/100.0

            if direction == 'forward':
                self.robot.left_motor.run_forever(speed_sp=left_speed)
                self.robot.right_motor.run_forever(speed_sp=right_speed)

            elif direction == 'backward':
                self.robot.left_motor.run_forever(speed_sp=left_speed * -1)
                self.robot.right_motor.run_forever(speed_sp=right_speed * -1)

            elif direction == 'left':
                self.robot.left_motor.run_forever(speed_sp=left_speed * -1)
                self.robot.right_motor.run_forever(speed_sp=right_speed)

            elif direction == 'right':
                self.robot.left_motor.run_forever(speed_sp=left_speed)
                self.robot.right_motor.run_forever(speed_sp=right_speed * -1)

        # desktop & mobile interface
        elif action == 'move-stop':
            log.debug("seq %d: move stop" % seq)
            self.robot.left_motor.stop()
            self.robot.right_motor.stop()
            joystick_engaged = False

        # medium motor
        elif action == 'motor-stop':
            motor = path[3]
            log.debug("seq %d: motor-stop %s" % (seq, motor))

            if motor == 'medium':
                if hasattr(self.robot, 'medium_motor'):
                    self.robot.medium_motor.stop()
            else:
                raise Exception("motor %s not supported yet" % motor)

        elif action == 'motor-start':
            motor = path[3]
            direction = path[4]
            speed_percentage = path[5]
            log.debug("seq %d: start motor %s, direction %s, speed_percentage %s" % (seq, motor, direction, speed_percentage))

            if motor == 'medium':
                if hasattr(self.robot, 'medium_motor'):
                    if direction == 'clockwise':
                        medium_speed = int(int(speed_percentage) * medium_motor_max_speed)/100.0
                        self.robot.medium_motor.run_forever(speed_sp=medium_speed)

                    elif direction == 'counter-clockwise':
                        medium_speed = int(int(speed_percentage) * medium_motor_max_speed)/100.0
                        self.robot.medium_motor.run_forever(speed_sp=medium_speed * -1)
                else:
                    log.info("we do not have a medium_motor")
            else:
                raise Exception("motor %s not supported yet" % motor)

        # mobile interface
        elif action == 'move-xy':
            x = int(path[3])
            y = int(path[4])

            if joystick_engaged:
                if seq > max_move_xy_seq:
                    (left_speed, right_speed) = xy_to_speed(x, y, motor_max_speed)
                    log.debug("seq %d: (x, y) %4d, %4d -> speed %d %d" % (seq, x, y, left_speed, right_speed))
                    max_move_xy_seq = seq

                    if left_speed == 0:
                        self.robot.left_motor.stop()
                    else:
                        self.robot.left_motor.run_forever(speed_sp=left_speed)

                    if right_speed == 0:
                        self.robot.right_motor.stop()
                    else:
                        self.robot.right_motor.run_forever(speed_sp=right_speed)
                else:
                    log.debug("seq %d: (x, y) %4d, %4d (ignore, max seq %d)" %
                              (seq, x, y, max_move_xy_seq))
            else:
                log.debug("seq %d: (x, y) %4d, %4d (ignore, joystick idle)" %
                          (seq, x, y))

        elif action == 'joystick-engaged':
            joystick_engaged = True

        elif action == 'log':
            msg = ''.join(path[3:])
            re_msg = re.search('^(.*)\?', msg)

            if re_msg:
                msg = re_msg.group(1)

            log.debug("seq %d: CLIENT LOG: %s" % (seq, msg))

        else:
            log.warning("Unsupported URL %s" % self.path)

        # It is good practice to send this but if we are getting move-xy we
        # tend to get a lot of them and we need to be as fast as possible so
        # be bad and don't send a reply. This takes ~20ms.
        if action != 'move-xy':
            self.send_response(204)

        return True


class RobotWebServer(object):
    """
    A Web server so that 'robot' can be controlled via 'handler_class'
    """

    def __init__(self, robot, handler_class, port_number=8000):
        self.content_server = None
        self.handler_class = handler_class
        self.handler_class.robot = robot
        self.port_number = port_number

    def run(self):

        try:
            log.info("Started HTTP server (content) on port %d" % self.port_number)
            self.content_server = HTTPServer(('', self.port_number), self.handler_class)
            self.content_server.serve_forever()

        # Exit cleanly, stop both web servers and all motors
        except (KeyboardInterrupt, Exception) as e:
            log.exception(e)

            if self.content_server:
                self.content_server.socket.close()
                self.content_server = None

            for motor in list_motors():
                motor.stop()


class WebControlledTank(Tank):
    """
    A tank that is controlled via a web browser
    """

    def __init__(self, left_motor, right_motor, polarity='normal', port_number=8000):
        Tank.__init__(self, left_motor, right_motor, polarity)
        self.www = RobotWebServer(self, TankWebHandler, port_number)

    def main(self):
        # start the web server
        self.www.run()
