#!/usr/bin/env python3

import logging
import os
import re
from ev3dev2.motor import MoveJoystick, list_motors, LargeMotor
from http.server import BaseHTTPRequestHandler, HTTPServer

log = logging.getLogger(__name__)


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
joystick_engaged = False

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
                    self.robot.on(x, y, motor_max_speed)
                    max_move_xy_seq = seq
                    log.debug("seq %d: (x, y) (%4d, %4d)" % (seq, x, y))
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


class WebControlledTank(MoveJoystick):
    """
    A tank that is controlled via a web browser
    """

    def __init__(self, left_motor, right_motor, port_number=8000, desc=None, motor_class=LargeMotor):
        MoveJoystick.__init__(self, left_motor, right_motor, desc, motor_class)
        self.www = RobotWebServer(self, TankWebHandler, port_number)

    def main(self):
        # start the web server
        self.www.run()
