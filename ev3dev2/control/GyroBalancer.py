"""Module for a robot that stands on two wheels and uses a gyro sensor.

The robot (eg. BALANC3R) will to keep its balance and move in response to
the remote control. This code was adapted from Laurens Valk's script at
https://github.com/laurensvalk/segway.

"""
# The MIT License (MIT)
#
# Copyright (c) 2016 Laurens Valk (laurensvalk@gmail.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
import time
import json
import queue
import threading
import math
import signal
from collections import deque
from ev3dev.power import PowerSupply
from ev3dev.motor import LargeMotor, OUTPUT_A, OUTPUT_D
from ev3dev.sensor.lego import GyroSensor, TouchSensor
from ev3dev.sound import Sound
from collections import OrderedDict

log = logging.getLogger(__name__)

# Constants
RAD_PER_DEG = math.pi / 180

# EV3 Platform specific constants

# For the LEGO EV3 Gyro in Rate mode, 1 unit = 1 deg/s
DEG_PER_SEC_PER_RAW_GYRO_UNIT = 1

# Express the above as the rate in rad/s per gyro unit
RAD_PER_SEC_PER_RAW_GYRO_UNIT = DEG_PER_SEC_PER_RAW_GYRO_UNIT * RAD_PER_DEG

# For the LEGO EV3 Large Motor 1 unit = 1 deg
DEG_PER_RAW_MOTOR_UNIT = 1

# Express the above as the angle in rad per motor unit
RAD_PER_RAW_MOTOR_UNIT = DEG_PER_RAW_MOTOR_UNIT * RAD_PER_DEG

# On the EV3, "1% speed" corresponds to 1.7 RPM (if speed
# control were enabled).
RPM_PER_PERCENT_SPEED = 1.7

# Convert this number to the speed in deg/s per "percent speed"
DEG_PER_SEC_PER_PERCENT_SPEED = RPM_PER_PERCENT_SPEED * 360 / 60

# Convert this number to the speed in rad/s per "percent speed"
RAD_PER_SEC_PER_PERCENT_SPEED = DEG_PER_SEC_PER_PERCENT_SPEED * RAD_PER_DEG

# Speed and steering limits
SPEED_MAX = 20
STEER_MAX = 8


class GyroBalancer(object):
    """
    Base class for a robot that stands on two wheels and uses a gyro sensor.

    Robot will keep its balance.
    """

    def __init__(self,
                 gain_gyro_angle=1700,
                 gain_gyro_rate=120,
                 gain_motor_angle=7,
                 gain_motor_angular_speed=9,
                 gain_motor_angle_error_accumulated=3,
                 power_voltage_nominal=8.0,
                 pwr_friction_offset_nom=3,
                 timing_loop_msec=30,
                 motor_angle_history_length=5,
                 gyro_drift_compensation_factor=0.05,
                 left_motor_port=OUTPUT_D,
                 right_motor_port=OUTPUT_A,
                 debug=False):
        """Create GyroBalancer."""
        # Gain parameters
        self.gain_gyro_angle = gain_gyro_angle
        self.gain_gyro_rate = gain_gyro_rate
        self.gain_motor_angle = gain_motor_angle
        self.gain_motor_angular_speed = gain_motor_angular_speed
        self.gain_motor_angle_error_accumulated =\
            gain_motor_angle_error_accumulated

        # Power parameters
        self.power_voltage_nominal = power_voltage_nominal
        self.pwr_friction_offset_nom = pwr_friction_offset_nom

        # Timing parameters
        self.timing_loop_msec = timing_loop_msec
        self.motor_angle_history_length = motor_angle_history_length
        self.gyro_drift_compensation_factor = gyro_drift_compensation_factor

        # Power supply setup
        self.power_supply = PowerSupply()

        # Gyro Sensor setup
        self.gyro = GyroSensor()
        self.gyro.mode = self.gyro.MODE_GYRO_RATE

        # Touch Sensor setup
        self.touch = TouchSensor()

        # IR Buttons setup
        # self.remote = InfraredSensor()
        # self.remote.mode = self.remote.MODE_IR_REMOTE

        # Configure the motors
        self.motor_left = LargeMotor(left_motor_port)
        self.motor_right = LargeMotor(right_motor_port)

        # Sound setup
        self.sound = Sound()

        # Open sensor and motor files
        self.gyro_file = open(self.gyro._path + "/value0", "rb")
        self.touch_file = open(self.touch._path + "/value0", "rb")
        self.encoder_left_file = open(self.motor_left._path + "/position",
                                      "rb")
        self.encoder_right_file = open(self.motor_right._path + "/position",
                                       "rb")
        self.dc_left_file = open(self.motor_left._path + "/duty_cycle_sp", "w")
        self.dc_right_file = open(self.motor_right._path + "/duty_cycle_sp",
                                  "w")

        # Drive queue
        self.drive_queue = queue.Queue()

        # Stop event for balance thread
        self.stop_balance = threading.Event()

        # Debugging
        self.debug = debug

        # Handlers for SIGINT and SIGTERM
        signal.signal(signal.SIGINT, self.signal_int_handler)
        signal.signal(signal.SIGTERM, self.signal_term_handler)

    def shutdown(self):
        """Close all file handles and stop all motors."""
        self.stop_balance.set()  # Stop balance thread
        self.motor_left.stop()
        self.motor_right.stop()
        self.gyro_file.close()
        self.touch_file.close()
        self.encoder_left_file.close()
        self.encoder_right_file.close()
        self.dc_left_file.close()
        self.dc_right_file.close()

    def _fast_read(self, infile):
        """Function for fast reading from sensor files."""
        infile.seek(0)
        return(int(infile.read().decode().strip()))

    def _fast_write(self, outfile, value):
        """Function for fast writing to motor files."""
        outfile.truncate(0)
        outfile.write(str(int(value)))
        outfile.flush()

    def _set_duty(self, motor_duty_file, duty, friction_offset,
                  voltage_comp):
        """Function to set the duty cycle of the motors."""
        # Compensate for nominal voltage and round the input
        duty_int = int(round(duty*voltage_comp))

        # Add or subtract offset and clamp the value between -100 and 100
        if duty_int > 0:
            duty_int = min(100, duty_int + friction_offset)
        elif duty_int < 0:
            duty_int = max(-100, duty_int - friction_offset)

        # Apply the signal to the motor
        self._fast_write(motor_duty_file, duty_int)

    def signal_int_handler(self, signum, frame):
        """Signal handler for SIGINT."""
        log.info('"Caught SIGINT')
        self.shutdown()
        raise GracefulShutdown()

    def signal_term_handler(self, signum, frame):
        """Signal handler for SIGTERM."""
        log.info('"Caught SIGTERM')
        self.shutdown()
        raise GracefulShutdown()

    def balance(self):
        """Run the _balance method as a thread."""
        balance_thread = threading.Thread(target=self._balance)
        balance_thread.start()

    def _balance(self):
        """Make the robot balance."""
        while True and not self.stop_balance.is_set():

            # Reset the motors
            self.motor_left.reset()  # Reset the encoder
            self.motor_right.reset()
            self.motor_left.run_direct()  # Set to run direct mode
            self.motor_right.run_direct()

            # Initialize variables representing physical signals
            # (more info on these in the docs)

            # The angle of "the motor", measured in raw units,
            # degrees for the EV3).
            # We will take the average of both motor positions as
            # "the motor" angle, which is essentially how far the middle
            # of the robot has travelled.
            motor_angle_raw = 0

            # The angle of the motor, converted to RAD (2*pi RAD
            # equals 360 degrees).
            motor_angle = 0

            # The reference angle of the motor. The robot will attempt to
            # drive forward or backward, such that its measured position
            motor_angle_ref = 0
            # equals this reference (or close enough).

            # The error: the deviation of the measured motor angle from the
            # reference. The robot attempts to make this zero, by driving
            # toward the reference.
            motor_angle_error = 0

            # We add up all of the motor angle error in time. If this value
            # gets out of hand, we can use it to drive the robot back to
            # the reference position a bit quicker.
            motor_angle_error_acc = 0

            # The motor speed, estimated by how far the motor has turned in
            # a given amount of time.
            motor_angular_speed = 0

            # The reference speed during manouvers: how fast we would like
            # to drive, measured in RAD per second.
            motor_angular_speed_ref = 0

            # The error: the deviation of the motor speed from the
            # reference speed.
            motor_angular_speed_error = 0

            # The 'voltage' signal we send to the motor.
            # We calculate a new value each time, just right to keep the
            # robot upright.
            motor_duty_cycle = 0

            # The raw value from the gyro sensor in rate mode.
            gyro_rate_raw = 0

            # The angular rate of the robot (how fast it is falling forward
            # or backward), measured in RAD per second.
            gyro_rate = 0

            # The gyro doesn't measure the angle of the robot, but we can
            # estimate this angle by keeping track of the gyro_rate value
            # in time.
            gyro_est_angle = 0

            # Over time, the gyro rate value can drift. This causes the
            # sensor to think it is moving even when it is perfectly still.
            # We keep track of this offset.
            gyro_offset = 0

            # Start
            log.info("Hold robot upright. Press touch sensor to start.")
            self.sound.speak("Press touch sensor to start.")

            self.touch.wait_for_bump()

            # Read battery voltage
            voltage_idle = self.power_supply.measured_volts
            voltage_comp = self.power_voltage_nominal / voltage_idle

            # Offset to limit friction deadlock
            friction_offset = int(round(self.pwr_friction_offset_nom *
                                        voltage_comp))

            # Timing settings for the program
            # Time of each loop, measured in seconds.
            loop_time_target = self.timing_loop_msec / 1000
            loop_count = 0  # Loop counter, starting at 0

            # A deque (a fifo array) which we'll use to keep track of
            # previous motor positions, which we can use to calculate the
            # rate of change (speed)
            motor_angle_hist =\
                deque([0], self.motor_angle_history_length)

            # The rate at which we'll update the gyro offset (precise
            # definition given in docs)
            gyro_drift_comp_rate =\
                self.gyro_drift_compensation_factor *\
                loop_time_target * RAD_PER_SEC_PER_RAW_GYRO_UNIT

            # Calibrate Gyro
            log.info("-----------------------------------")
            log.info("Calibrating...")

            # As you hold the robot still, determine the average sensor
            # value of 100 samples
            gyro_calibrate_count = 100
            for i in range(gyro_calibrate_count):
                gyro_offset = gyro_offset + self._fast_read(self.gyro_file)
                time.sleep(0.01)
            gyro_offset = gyro_offset / gyro_calibrate_count

            # Print the result
            log.info("gyro_offset: " + str(gyro_offset))
            log.info("-----------------------------------")
            log.info("GO!")
            log.info("-----------------------------------")
            log.info("Press Touch Sensor to re-start.")
            log.info("-----------------------------------")
            self.sound.beep()

            # Remember start time
            prog_start_time = time.time()

            if self.debug:
                # Data logging
                data = OrderedDict()
                loop_times = OrderedDict()
                data['loop_times'] = loop_times
                gyro_readings = OrderedDict()
                data['gyro_readings'] = gyro_readings

            # Initial fast read touch sensor value
            touch_pressed = False

            # Driving and Steering
            speed, steering = (0, 0)

            # Record start time of loop
            loop_start_time = time.time()

            # Balancing Loop
            while not touch_pressed and not self.stop_balance.is_set():

                loop_count += 1

                # Check for drive instructions and set speed / steering
                try:
                    speed, steering = self.drive_queue.get_nowait()
                    self.drive_queue.task_done()
                except queue.Empty:
                    pass

                # Read the touch sensor (the kill switch)
                touch_pressed = self._fast_read(self.touch_file)

                # Read the Motor Position
                motor_angle_raw = ((self._fast_read(self.encoder_left_file) +
                                   self._fast_read(self.encoder_right_file)) /
                                   2.0)
                motor_angle = motor_angle_raw * RAD_PER_RAW_MOTOR_UNIT

                # Read the Gyro
                gyro_rate_raw = self._fast_read(self.gyro_file)

                # Busy wait for the loop to reach target time length
                loop_time = 0
                while(loop_time < loop_time_target):
                    loop_time = time.time() - loop_start_time
                    time.sleep(0.001)

                # Calculate most recent loop time
                loop_time = time.time() - loop_start_time

                # Set start time of next loop
                loop_start_time = time.time()

                if self.debug:
                    # Log gyro data and loop time
                    time_of_sample = time.time() - prog_start_time
                    gyro_readings[time_of_sample] = gyro_rate_raw
                    loop_times[time_of_sample] = loop_time * 1000.0

                # Calculate gyro rate
                gyro_rate = (gyro_rate_raw - gyro_offset) *\
                    RAD_PER_SEC_PER_RAW_GYRO_UNIT

                # Calculate Motor Parameters
                motor_angular_speed_ref =\
                    speed * RAD_PER_SEC_PER_PERCENT_SPEED
                motor_angle_ref = motor_angle_ref +\
                    motor_angular_speed_ref * loop_time_target
                motor_angle_error = motor_angle - motor_angle_ref

                # Compute Motor Speed
                motor_angular_speed =\
                    ((motor_angle - motor_angle_hist[0]) /
                     (self.motor_angle_history_length * loop_time_target))
                motor_angular_speed_error = motor_angular_speed
                motor_angle_hist.append(motor_angle)

                # Compute the motor duty cycle value
                motor_duty_cycle =\
                    (self.gain_gyro_angle * gyro_est_angle +
                     self.gain_gyro_rate * gyro_rate +
                     self.gain_motor_angle * motor_angle_error +
                     self.gain_motor_angular_speed *
                     motor_angular_speed_error +
                     self.gain_motor_angle_error_accumulated *
                     motor_angle_error_acc)

                # Apply the signal to the motor, and add steering
                self._set_duty(self.dc_right_file, motor_duty_cycle + steering,
                               friction_offset, voltage_comp)
                self._set_duty(self.dc_left_file, motor_duty_cycle - steering,
                               friction_offset, voltage_comp)

                # Update angle estimate and gyro offset estimate
                gyro_est_angle = gyro_est_angle + gyro_rate *\
                    loop_time_target
                gyro_offset = (1 - gyro_drift_comp_rate) *\
                    gyro_offset + gyro_drift_comp_rate * gyro_rate_raw

                # Update Accumulated Motor Error
                motor_angle_error_acc = motor_angle_error_acc +\
                    motor_angle_error * loop_time_target

            # Closing down & Cleaning up

            # Loop end time, for stats
            prog_end_time = time.time()

            # Turn off the motors
            self._fast_write(self.dc_left_file, 0)
            self._fast_write(self.dc_right_file, 0)

            # Wait for the Touch Sensor to be released
            while self.touch.is_pressed:
                time.sleep(0.01)

            # Calculate loop time
            avg_loop_time = (prog_end_time - prog_start_time) / loop_count
            log.info("Loop time:" + str(avg_loop_time * 1000) + "ms")

            # Print a stop message
            log.info("-----------------------------------")
            log.info("STOP")
            log.info("-----------------------------------")

            if self.debug:
                # Dump logged data to file
                with open("data.txt", 'w') as data_file:
                    json.dump(data, data_file)

    def _move(self, speed=0, steering=0, seconds=None):
        """Move robot."""
        self.drive_queue.put((speed, steering))
        if seconds is not None:
            time.sleep(seconds)
            self.drive_queue.put((0, 0))
        self.drive_queue.join()

    def move_forward(self, seconds=None):
        """Move robot forward."""
        self._move(speed=SPEED_MAX, steering=0, seconds=seconds)

    def move_backward(self, seconds=None):
        """Move robot backward."""
        self._move(speed=-SPEED_MAX, steering=0, seconds=seconds)

    def rotate_left(self, seconds=None):
        """Rotate robot left."""
        self._move(speed=0, steering=STEER_MAX, seconds=seconds)

    def rotate_right(self, seconds=None):
        """Rotate robot right."""
        self._move(speed=0, steering=-STEER_MAX, seconds=seconds)

    def stop(self):
        """Stop robot (balancing will continue)."""
        self._move(speed=0, steering=0)


class GracefulShutdown(Exception):
    """Custom exception for SIGINT and SIGTERM."""

    pass
