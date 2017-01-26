#!/usr/bin/env python3

from ev3dev.auto import OUTPUT_A, OUTPUT_B, OUTPUT_C, InfraredSensor
from ev3dev.helper import LargeMotor, MediumMotor, ColorSensor, MotorStall
from pprint import pformat
from rubikscolorresolver import RubiksColorSolverGeneric
from subprocess import check_output
from time import sleep
import json
import logging
import os
import signal
import sys
import time

log = logging.getLogger(__name__)


class ScanError(Exception):
    pass


class Rubiks(object):
    scan_order = [
        5, 9, 6, 3, 2, 1, 4, 7, 8,
        23, 27, 24, 21, 20, 19, 22, 25, 26,
        50, 54, 51, 48, 47, 46, 49, 52, 53,
        14, 10, 13, 16, 17, 18, 15, 12, 11,
        41, 43, 44, 45, 42, 39, 38, 37, 40,
        32, 34, 35, 36, 33, 30, 29, 28, 31]

    hold_cube_pos = 85
    rotate_speed = 400
    flip_speed = 300
    flip_speed_push = 400
    corner_to_edge_diff = 60

    def __init__(self):
        self.shutdown = False
        self.flipper = LargeMotor(OUTPUT_A)
        self.turntable = LargeMotor(OUTPUT_B)
        self.colorarm = MediumMotor(OUTPUT_C)
        self.color_sensor = ColorSensor()
        self.color_sensor.mode = self.color_sensor.MODE_RGB_RAW
        self.infrared_sensor = InfraredSensor()
        self.cube = {}
        self.init_motors()
        self.state = ['U', 'D', 'F', 'L', 'B', 'R']
        self.rgb_solver = None
        signal.signal(signal.SIGTERM, self.signal_term_handler)
        signal.signal(signal.SIGINT, self.signal_int_handler)

    def init_motors(self):

        for x in (self.flipper, self.turntable, self.colorarm):
            if not x.connected:
                log.error("%s is not connected" % x)
                sys.exit(1)
            x.reset()

        log.info("Initialize flipper %s" % self.flipper)
        self.flipper.run_forever(speed_sp=-50, stop_action='hold')
        self.flipper.wait_for_stop()
        self.flipper.stop()
        self.flipper.reset()
        self.flipper.stop(stop_action='hold')

        log.info("Initialize colorarm %s" % self.colorarm)
        self.colorarm.run_forever(speed_sp=500, stop_action='hold')
        self.colorarm.wait_for_stop()
        self.colorarm.stop()
        self.colorarm.reset()
        self.colorarm.stop(stop_action='hold')

        log.info("Initialize turntable %s" % self.turntable)
        self.turntable.reset()
        self.turntable.stop(stop_action='hold')

    def shutdown_robot(self):
        log.info('Shutting down')
        self.shutdown = True

        if self.rgb_solver:
            self.rgb_solver.shutdown = True

        for x in (self.flipper, self.turntable, self.colorarm):
            x.shutdown = True

        for x in (self.flipper, self.turntable, self.colorarm):
            x.stop(stop_action='brake')

    def signal_term_handler(self, signal, frame):
        log.error('Caught SIGTERM')
        self.shutdown_robot()

    def signal_int_handler(self, signal, frame):
        log.error('Caught SIGINT')
        self.shutdown_robot()

    def apply_transformation(self, transformation):
        self.state = [self.state[t] for t in transformation]

    def rotate_cube(self, direction, nb):
        current_pos = self.turntable.position
        final_pos = 135 * round((self.turntable.position + (270 * direction * nb)) / 135.0)
        log.info("rotate_cube() direction %s, nb %s, current_pos %d, final_pos %d" % (direction, nb, current_pos, final_pos))

        if self.flipper.position > 35:
            self.flipper_away()

        self.turntable.run_to_abs_pos(position_sp=final_pos,
                                      speed_sp=Rubiks.rotate_speed,
                                      stop_action='hold',
                                      ramp_up_sp=0)
        self.turntable.wait_for_running()
        self.turntable.wait_for_position(final_pos)
        self.turntable.wait_for_stop()

        if nb >= 1:
            for i in range(nb):
                if direction > 0:
                    transformation = [0, 1, 5, 2, 3, 4]
                else:
                    transformation = [0, 1, 3, 4, 5, 2]
                self.apply_transformation(transformation)

    def rotate_cube_1(self):
        self.rotate_cube(1, 1)

    def rotate_cube_2(self):
        self.rotate_cube(1, 2)

    def rotate_cube_3(self):
        self.rotate_cube(-1, 1)

    def rotate_cube_blocked(self, direction, nb):

        # Move the arm down to hold the cube in place
        self.flipper_hold_cube()

        # OVERROTATE depends on lot on Rubiks.rotate_speed
        current_pos = self.turntable.position
        OVERROTATE = 18
        final_pos = int(135 * round((current_pos + (270 * direction * nb)) / 135.0))
        temp_pos = int(final_pos + (OVERROTATE * direction))

        log.info("rotate_cube_blocked() direction %s nb %s, current pos %s, temp pos %s, final pos %s" %
                 (direction, nb, current_pos, temp_pos, final_pos))

        self.turntable.run_to_abs_pos(position_sp=temp_pos,
                                      speed_sp=Rubiks.rotate_speed,
                                      stop_action='hold',
                                      ramp_up_sp=0)
        self.turntable.wait_for_running()
        self.turntable.wait_for_position(temp_pos)
        self.turntable.wait_for_stop()

        self.turntable.run_to_abs_pos(position_sp=final_pos,
                                      speed_sp=int(Rubiks.rotate_speed/4),
                                      stop_action='hold',
                                      ramp_up_sp=0)
        self.turntable.wait_for_running()
        self.turntable.wait_for_position(final_pos, stall_ok=True)
        self.turntable.wait_for_stop()

    def rotate_cube_blocked_1(self):
        self.rotate_cube_blocked(1, 1)

    def rotate_cube_blocked_2(self):
        self.rotate_cube_blocked(1, 2)

    def rotate_cube_blocked_3(self):
        self.rotate_cube_blocked(-1, 1)

    def flipper_hold_cube(self, speed=300):
        current_position = self.flipper.position

        # Push it forward so the cube is always in the same position
        # when we start the flip
        if (current_position <= Rubiks.hold_cube_pos - 10 or
            current_position >= Rubiks.hold_cube_pos + 10):
            self.flipper.run_to_abs_pos(position_sp=Rubiks.hold_cube_pos,
                                        ramp_down_sp=400,
                                        speed_sp=speed)
            self.flipper.wait_for_running()
            self.flipper.wait_for_position(Rubiks.hold_cube_pos)
            self.flipper.wait_for_stop()
            sleep(0.05)

    def flipper_away(self, speed=300):
        """
        Move the flipper arm out of the way
        """
        log.info("flipper_away()")
        self.flipper.run_to_abs_pos(position_sp=0,
                                    ramp_down_sp=400,
                                    speed_sp=speed)
        self.flipper.wait_for_running()

        try:
            self.flipper.wait_for_position(0)
            self.flipper.wait_for_stop()
        except MotorStall:
            self.flipper.stop()

    def flip(self):
        """
        Motors will sometimes stall if you call run_to_abs_pos() multiple
        times back to back on the same motor. To avoid this we call a 50ms
        sleep in flipper_hold_cube() and after each run_to_abs_pos() below.

        We have to sleep after the 2nd run_to_abs_pos() because sometimes
        flip() is called back to back.
        """
        log.info("flip()")

        if self.shutdown:
            return

        # Move the arm down to hold the cube in place
        self.flipper_hold_cube()

        # Grab the cube and pull back
        self.flipper.run_to_abs_pos(position_sp=190,
                                    ramp_up_sp=200,
                                    ramp_down_sp=0,
                                    speed_sp=self.flip_speed)
        self.flipper.wait_for_running()
        self.flipper.wait_for_position(190)
        self.flipper.wait_for_stop()
        sleep(0.05)

        # At this point the cube is at an angle, push it forward to
        # drop it back down in the turntable
        self.flipper.run_to_abs_pos(position_sp=Rubiks.hold_cube_pos,
                                    ramp_up_sp=200,
                                    ramp_down_sp=400,
                                    speed_sp=self.flip_speed_push)
        self.flipper.wait_for_running()
        self.flipper.wait_for_position(Rubiks.hold_cube_pos)
        self.flipper.wait_for_stop()
        sleep(0.05)

        transformation = [2, 4, 1, 3, 0, 5]
        self.apply_transformation(transformation)

    def colorarm_middle(self):
        log.info("colorarm_middle()")
        self.colorarm.run_to_abs_pos(position_sp=-750,
                                     speed_sp=600,
                                     stop_action='hold')
        self.colorarm.wait_for_running()
        self.colorarm.wait_for_position(-750)
        self.colorarm.wait_for_stop()

    def colorarm_corner(self, square_index):
        log.info("colorarm_corner(%d)" % square_index)
        position_target = -580

        if square_index == 1:
            position_target += 20
        elif square_index == 3:
            pass
        elif square_index == 5:
            position_target -= 20
        elif square_index == 7:
            pass
        else:
            raise ScanError("colorarm_corner was given unsupported square_index %d" % square_index)

        self.colorarm.run_to_abs_pos(position_sp=position_target,
                                     speed_sp=600,
                                     stop_action='hold')

    def colorarm_edge(self, square_index):
        log.info("colorarm_edge(%d)" % square_index)
        position_target = -640

        if square_index == 2:
            pass
        elif square_index == 4:
            position_target -= 20
        elif square_index == 6:
            position_target -= 20
        elif square_index == 8:
            pass
        else:
            raise ScanError("colorarm_edge was given unsupported square_index %d" % square_index)

        self.colorarm.run_to_abs_pos(position_sp=position_target,
                                     speed_sp=600,
                                     stop_action='hold')

    def colorarm_remove(self):
        log.info("colorarm_remove()")
        self.colorarm.run_to_abs_pos(position_sp=0,
                                     speed_sp=600)
        self.colorarm.wait_for_running()
        try:
            self.colorarm.wait_for_position(0)
            self.colorarm.wait_for_stop()
        except MotorStall:
            self.colorarm.stop()

    def colorarm_remove_halfway(self):
        log.info("colorarm_remove_halfway()")
        self.colorarm.run_to_abs_pos(position_sp=-400,
                                     speed_sp=600)
        self.colorarm.wait_for_running()
        self.colorarm.wait_for_position(-400)
        self.colorarm.wait_for_stop()

    def scan_middle(self, face_number):
        log.info("scan_middle() %d/6" % face_number)

        if self.flipper.position > 35:
            self.flipper_away()

        self.colorarm_middle()
        log.info(self.color_sensor.rgb())
        self.colorarm_remove_halfway()

    def scan_middles(self):
        """
        Used once to get the RGB values of the middle squares to
        populate the crayola_colors in rubiks_rgb_solver.py
        """
        log.info("scan_middle()")
        self.colors = {}
        self.k = 0
        self.scan_middle(1)
        raw_input('Paused')

        self.flip()
        self.scan_middle(2)
        raw_input('Paused')

        self.flip()
        self.scan_middle(3)
        raw_input('Paused')

        self.rotate_cube(-1, 1)
        self.flip()
        self.scan_middle(4)
        raw_input('Paused')

        self.rotate_cube(1, 1)
        self.flip()
        self.scan_middle(5)
        raw_input('Paused')

        self.flip()
        self.scan_middle(6)
        raw_input('Paused')

    def scan_face(self, face_number):
        log.info("scan_face() %d/6" % face_number)

        if self.shutdown:
            return

        if self.flipper.position > 35:
            self.flipper_away()

        self.colorarm_middle()
        self.colors[int(Rubiks.scan_order[self.k])] = tuple(self.color_sensor.rgb())

        self.k += 1
        i = 1
        self.colorarm_corner(i)

        # The gear ratio is 3:1 so 1080 is one full rotation
        self.turntable.reset()
        self.turntable.run_to_abs_pos(position_sp=1080,
                                      speed_sp=Rubiks.rotate_speed,
                                      stop_action='hold')

        while True:
            current_position = self.turntable.position

            # 135 is 1/8 of full rotation
            if current_position >= (i * 135):
                current_color = tuple(self.color_sensor.rgb())
                self.colors[int(Rubiks.scan_order[self.k])] = current_color
                # log.info("%s: i %d, current_position %d, current_color %s" %
                #          (self.turntable, i, current_position, current_color))

                i += 1
                self.k += 1

                if i == 9:
                    # Last face, move the color arm all the way out of the way
                    if face_number == 6:
                        self.colorarm_remove()

                    # Move the color arm far enough away so that the flipper
                    # arm doesn't hit it
                    else:
                        self.colorarm_remove_halfway()

                    break

                elif i % 2:
                    self.colorarm_corner(i)
                else:
                    self.colorarm_edge(i)

            if self.shutdown:
                return

        if i < 9:
            raise ScanError('i is %d..should be 9' % i)

        self.turntable.wait_for_position(1080)
        self.turntable.stop()
        self.turntable.reset()
        log.info("\n")

    def scan(self):
        log.info("scan()")
        self.colors = {}
        self.k = 0
        self.scan_face(1)

        self.flip()
        self.scan_face(2)

        self.flip()
        self.scan_face(3)

        self.rotate_cube(-1, 1)
        self.flip()
        self.scan_face(4)

        self.rotate_cube(1, 1)
        self.flip()
        self.scan_face(5)

        self.flip()
        self.scan_face(6)

        if self.shutdown:
            return

        log.info("RGB json:\n%s\n" % json.dumps(self.colors))
        self.rgb_solver = RubiksColorSolverGeneric(3)
        self.rgb_solver.enter_scan_data(self.colors)
        self.rgb_solver.crunch_colors()
        self.cube_kociemba = self.rgb_solver.cube_for_kociemba_strict()
        log.info("Final Colors (kociemba): %s" % ''.join(self.cube_kociemba))

        # This is only used if you want to rotate the cube so U is on top, F is
        # in the front, etc. You would do this if you were troubleshooting color
        # detection and you want to pause to compare the color pattern on the
        # cube vs. what we think the color pattern is.
        '''
        log.info("Position the cube so that U is on top, F is in the front, etc...to make debugging easier")
        self.rotate_cube(-1, 1)
        self.flip()
        self.flipper_away()
        self.rotate_cube(1, 1)
        raw_input('Paused')
        '''

    def move(self, face_down):
        log.info("move() face_down %s" % face_down)

        position = self.state.index(face_down)
        actions = {
            0: ["flip", "flip"],
            1: [],
            2: ["rotate_cube_2", "flip"],
            3: ["rotate_cube_1", "flip"],
            4: ["flip"],
            5: ["rotate_cube_3", "flip"]
        }.get(position, None)

        for a in actions:

            if self.shutdown:
                break

            getattr(self, a)()

    def run_kociemba_actions(self, actions):
        log.info('Action (kociemba): %s' % ' '.join(actions))
        total_actions = len(actions)

        for (i, a) in enumerate(actions):

            if self.shutdown:
                break

            if a.endswith("'"):
                face_down = list(a)[0]
                rotation_dir = 1
            elif a.endswith("2"):
                face_down = list(a)[0]
                rotation_dir = 2
            else:
                face_down = a
                rotation_dir = 3

            log.info("Move %d/%d: %s%s (a %s)" % (i, total_actions, face_down, rotation_dir, pformat(a)))
            self.move(face_down)

            if rotation_dir == 1:
                self.rotate_cube_blocked_1()
            elif rotation_dir == 2:
                self.rotate_cube_blocked_2()
            elif rotation_dir == 3:
                self.rotate_cube_blocked_3()
            log.info("\n")

    def resolve(self):

        if rub.shutdown:
            return

        output = check_output(['kociemba', ''.join(map(str, self.cube_kociemba))]).decode('ascii')
        actions = output.strip().split()
        self.run_kociemba_actions(actions)
        self.cube_done()

    def cube_done(self):
        self.flipper_away()

    def wait_for_cube_insert(self):
        rubiks_present = 0
        rubiks_present_target = 10
        log.info('wait for cube...to be inserted')

        while True:

            if self.shutdown:
                break

            dist = self.infrared_sensor.proximity

            # It is odd but sometimes when the cube is inserted
            # the IR sensor returns a value of 100...most of the
            # time it is just a value less than 50
            if dist < 50 or dist == 100:
                rubiks_present += 1
                log.info("wait for cube...distance %d, present for %d/%d" %
                         (dist, rubiks_present, rubiks_present_target))
            else:
                if rubiks_present:
                    log.info('wait for cube...cube removed (%d)' % dist)
                rubiks_present = 0

            if rubiks_present >= rubiks_present_target:
                log.info('wait for cube...cube found and stable')
                break

            time.sleep(0.1)


if __name__ == '__main__':

    # logging.basicConfig(filename='rubiks.log',
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(filename)12s %(levelname)8s: %(message)s')
    log = logging.getLogger(__name__)

    # Color the errors and warnings in red
    logging.addLevelName(logging.ERROR, "\033[91m   %s\033[0m" % logging.getLevelName(logging.ERROR))
    logging.addLevelName(logging.WARNING, "\033[91m %s\033[0m" % logging.getLevelName(logging.WARNING))

    rub = Rubiks()

    try:
        rub.wait_for_cube_insert()

        # Push the cube to the right so that it is in the expected
        # position when we begin scanning
        rub.flipper_hold_cube(100)
        rub.flipper_away(100)

        rub.scan()
        rub.resolve()
        rub.shutdown_robot()

    except Exception as e:
        log.exception(e)
        rub.shutdown_robot()
        sys.exit(1)
