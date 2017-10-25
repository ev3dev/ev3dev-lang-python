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
from collections import deque
from ev3dev.power import PowerSupply
from ev3dev.motor import LargeMotor, OUTPUT_A, OUTPUT_D
from ev3dev.sensor.lego import GyroSensor, InfraredSensor, TouchSensor

log = logging.getLogger(__name__)

########################################################################
# File I/O functions
########################################################################


def FastRead(infile):
    """Function for fast reading from sensor files."""
    infile.seek(0)
    return(int(infile.read().decode().strip()))


def FastWrite(outfile, value):
    """Function for fast writing to motor files."""
    outfile.truncate(0)
    outfile.write(str(int(value)))
    outfile.flush()


def SetDuty(motorDutyFileHandle, duty, frictionOffset, voltageCompensation):
    """Function to set the duty cycle of the motors."""
    # Compensate for nominal voltage and round the input
    dutyInt = int(round(duty*voltageCompensation))

    # Add or subtract offset and clamp the value between -100 and 100
    if dutyInt > 0:
        dutyInt = min(100, dutyInt + frictionOffset)
    elif dutyInt < 0:
        dutyInt = max(-100, dutyInt - frictionOffset)

    # Apply the signal to the motor
    FastWrite(motorDutyFileHandle, dutyInt)


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
                 power_friction_offset_nominal=3,
                 timing_loop_time_msec=30,
                 timing_motor_angle_history_length=5,
                 timing_gyro_drift_compensation_factor=0.05,
                 left_motor_port=OUTPUT_D,
                 right_motor_port=OUTPUT_A):
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
        self.power_friction_offset_nominal = power_friction_offset_nominal

        # Timing parameters
        self.timing_loop_time_msec = timing_loop_time_msec
        self.timing_motor_angle_history_length =\
            timing_motor_angle_history_length
        self.timing_gyro_drift_compensation_factor =\
            timing_gyro_drift_compensation_factor

        # EV3 Brick
        self.powerSupply = PowerSupply()
        # buttons = ev3.Button()

        # Gyro Sensor setup
        self.gyroSensor = GyroSensor()
        self.gyroSensor.mode = self.gyroSensor.MODE_GYRO_RATE
        self.gyroSensorValueRaw = open(self.gyroSensor._path + "/value0", "rb")

        # Touch Sensor setup
        self.touchSensor = TouchSensor()
        self.touchSensorValueRaw = open(self.touchSensor._path + "/value0",
                                        "rb")

        # IR Buttons setup
        self.irRemote = InfraredSensor()
        self.irRemote.mode = self.irRemote.MODE_IR_REMOTE
        self.irRemoteValueRaw = open(self.irRemote._path + "/value0", "rb")

        # Configure the motors
        self.motorLeft = LargeMotor(left_motor_port)
        self.motorRight = LargeMotor(right_motor_port)

    def main(self):
        """Make the robot go."""
        def shutdown():
            """Close all file handles and stop all motors."""
            self.touchSensorValueRaw.close()
            self.gyroSensorValueRaw.close()
            motorEncoderLeft.close()
            motorEncoderRight.close()
            motorDutyCycleLeft.close()
            motorDutyCycleRight.close()
            self.motorLeft.stop()
            self.motorRight.stop()

        try:
            while True:

                ###############################################################
                # Hardware (Re-)Config
                ###############################################################

                # Reset the motors
                self.motorLeft.reset()  # Reset the encoder
                self.motorRight.reset()
                self.motorLeft.run_direct()  # Set to run direct mode
                self.motorRight.run_direct()

                # Open sensor files for (fast) reading
                motorEncoderLeft = open(self.motorLeft._path + "/position",
                                        "rb")
                motorEncoderRight = open(self.motorRight._path + "/position",
                                         "rb")

                # Open motor files for (fast) writing
                motorDutyCycleLeft = open(self.motorLeft._path +
                                          "/duty_cycle_sp", "w")
                motorDutyCycleRight = open(self.motorRight._path +
                                           "/duty_cycle_sp", "w")

                ###############################################################
                # Definitions and Initialization variables
                ###############################################################

                # Math constants

                # The number of radians in a degree.
                radiansPerDegree = 3.14159/180

                # Platform specific constants and conversions

                # For the LEGO EV3 Gyro in Rate mode, 1 unit = 1 deg/s
                degPerSecondPerRawGyroUnit = 1

                # Express the above as the rate in rad/s per gyro unit
                radiansPerSecondPerRawGyroUnit = degPerSecondPerRawGyroUnit *\
                    radiansPerDegree

                # For the LEGO EV3 Large Motor 1 unit = 1 deg
                degPerRawMotorUnit = 1

                # Express the above as the angle in rad per motor unit
                radiansPerRawMotorUnit = degPerRawMotorUnit * radiansPerDegree

                # On the EV3, "1% speed" corresponds to 1.7 RPM (if speed
                # control were enabled).
                RPMperPerPercentSpeed = 1.7

                # Convert this number to the speed in deg/s per "percent speed"
                degPerSecPerPercentSpeed = RPMperPerPercentSpeed * 360 / 60

                # Convert this number to the speed in rad/s per "percent speed"
                radPerSecPerPercentSpeed = degPerSecPerPercentSpeed *\
                    radiansPerDegree

                # Variables representing physical signals
                # (more info on these in the docs)

                # The angle of "the motor", measured in raw units,
                # degrees for the EV3).
                # We will take the average of both motor positions as
                # "the motor" angle, which is essentially how far the middle
                # of the robot has traveled.
                motorAngleRaw = 0

                # The angle of the motor, converted to radians (2*pi radians
                # equals 360 degrees).
                motorAngle = 0

                # The reference angle of the motor. The robot will attempt to
                # drive forward or backward, such that its measured position
                motorAngleReference = 0
                # equals this reference (or close enough).

                # The error: the deviation of the measured motor angle from the
                # reference. The robot attempts to make this zero, by driving
                # toward the reference.
                motorAngleError = 0

                # We add up all of the motor angle error in time. If this value
                # gets out of hand, we can use it to drive the robot back to
                # the reference position a bit quicker.
                motorAngleErrorAccumulated = 0

                # The motor speed, estimated by how far the motor has turned in
                # a given amount of time.
                motorAngularSpeed = 0

                # The reference speed during manouvers: how fast we would like
                # to drive, measured in radians per second.
                motorAngularSpeedReference = 0

                # The error: the deviation of the motor speed from the
                # reference speed.
                motorAngularSpeedError = 0

                # The 'voltage' signal we send to the motor.
                # We calculate a new value each time, just right to keep the
                # robot upright.
                motorDutyCycle = 0

                # The raw value from the gyro sensor in rate mode.
                gyroRateRaw = 0

                # The angular rate of the robot (how fast it is falling forward
                # or backward), measured in radians per second.
                gyroRate = 0

                # The gyro doesn't measure the angle of the robot, but we can
                # estimate this angle by keeping track of the gyroRate value in
                # time.
                gyroEstimatedAngle = 0

                # Over time, the gyro rate value can drift. This causes the
                # sensor to think it is moving even when it is perfectly still.
                # We keep track of this offset.
                gyroOffset = 0

                log.info("Hold robot upright. Press Touch Sensor to start.")

                self.touchSensor.wait_for_bump()

                # Read battery voltage
                voltageIdle = self.powerSupply.measured_volts
                voltageCompensation = self.power_voltage_nominal/voltageIdle

                # Offset to limit friction deadlock
                frictionOffset = int(round(self.power_friction_offset_nominal *
                                     voltageCompensation))

                # Timing settings for the program
                # Time of each loop, measured in seconds.
                loopTimeSec = self.timing_loop_time_msec / 1000
                loopCount = 0  # Loop counter, starting at 0

                # A deque (a fifo array) which we'll use to keep track of
                # previous motor positions, which we can use to calculate the
                # rate of change (speed)
                motorAngleHistory =\
                    deque([0], self.timing_motor_angle_history_length)

                # The rate at which we'll update the gyro offset (precise
                # definition given in docs)
                gyroDriftCompensationRate =\
                    self.timing_gyro_drift_compensation_factor *\
                    loopTimeSec * radiansPerSecondPerRawGyroUnit

                ###############################################################
                # Calibrate Gyro
                ###############################################################

                log.info("-----------------------------------")
                log.info("Calibrating...")

                # As you hold the robot still, determine the average sensor
                # value of 100 samples
                gyroRateCalibrateCount = 100
                for i in range(gyroRateCalibrateCount):
                    gyroOffset = gyroOffset + FastRead(self.gyroSensorValueRaw)
                    time.sleep(0.01)
                gyroOffset = gyroOffset/gyroRateCalibrateCount

                # Print the result
                log.info("GyroOffset: " + str(gyroOffset))
                log.info("-----------------------------------")
                log.info("GO!")
                log.info("-----------------------------------")
                log.info("Press Touch Sensor to re-start.")
                log.info("-----------------------------------")

                ###############################################################
                # Balancing Loop
                ###############################################################

                # Remember start time
                tProgramStart = time.time()

                # Initial fast read touch sensor value
                touchSensorPressed = False

                # Keep looping until Touch Sensor is pressed again
                while not touchSensorPressed:

                    ###########################################################
                    #  Loop info
                    ###########################################################
                    loopCount = loopCount + 1
                    tLoopStart = time.time()

                    ###########################################################
                    #  Driving and Steering.
                    ###########################################################

                    # Just balance in place:
                    speed = 0
                    steering = 0

                    # Control speed and steering based on the IR Remote
                    buttonCode = FastRead(self.irRemoteValueRaw)

                    speed_max = 20
                    steer_max_right = 8

                    if(buttonCode == 5):
                        speed = speed_max
                        steering = 0
                    elif (buttonCode == 6):
                        speed = 0
                        steering = -steer_max_right
                    elif (buttonCode == 7):
                        speed = 0
                        steering = steer_max_right
                    elif (buttonCode == 8):
                        speed = -speed_max
                        steering = 0
                    else:
                        speed = 0
                        steering = 0

                    ###########################################################
                    #  Reading the Gyro.
                    ###########################################################
                    gyroRateRaw = FastRead(self.gyroSensorValueRaw)
                    gyroRate = (gyroRateRaw - gyroOffset) *\
                        radiansPerSecondPerRawGyroUnit

                    ###########################################################
                    #  Reading the Motor Position
                    ###########################################################

                    motorAngleRaw = (FastRead(motorEncoderLeft) +
                                     FastRead(motorEncoderRight)) / 2
                    motorAngle = motorAngleRaw*radiansPerRawMotorUnit

                    motorAngularSpeedReference = speed*radPerSecPerPercentSpeed
                    motorAngleReference = motorAngleReference +\
                        motorAngularSpeedReference * loopTimeSec

                    motorAngleError = motorAngle - motorAngleReference

                    ###########################################################
                    #  Computing Motor Speed
                    ###########################################################

                    motorAngularSpeed = (motorAngle - motorAngleHistory[0]) /\
                        (self.timing_motor_angle_history_length*loopTimeSec)
                    motorAngularSpeedError = motorAngularSpeed
                    motorAngleHistory.append(motorAngle)

                    ###########################################################
                    #  Computing the motor duty cycle value
                    ###########################################################

                    motorDutyCycle =\
                        (self.gain_gyro_angle * gyroEstimatedAngle +
                         self.gain_gyro_rate * gyroRate +
                         self.gain_motor_angle * motorAngleError +
                         self.gain_motor_angular_speed *
                         motorAngularSpeedError +
                         self.gain_motor_angle_error_accumulated *
                         motorAngleErrorAccumulated)

                    ###########################################################
                    #  Apply the signal to the motor, and add steering
                    ###########################################################

                    SetDuty(motorDutyCycleRight, motorDutyCycle +
                            steering, frictionOffset, voltageCompensation)
                    SetDuty(motorDutyCycleLeft, motorDutyCycle - steering,
                            frictionOffset, voltageCompensation)

                    ###########################################################
                    #  Update angle estimate and Gyro Offset Estimate
                    ###########################################################

                    gyroEstimatedAngle = gyroEstimatedAngle + gyroRate *\
                        loopTimeSec
                    gyroOffset = (1 - gyroDriftCompensationRate) *\
                        gyroOffset + gyroDriftCompensationRate * gyroRateRaw

                    ###########################################################
                    #  Update Accumulated Motor Error
                    ###########################################################

                    motorAngleErrorAccumulated = motorAngleErrorAccumulated +\
                        motorAngleError*loopTimeSec

                    ###########################################################
                    #  Read the touch sensor (the kill switch)
                    ###########################################################

                    touchSensorPressed = FastRead(self.touchSensorValueRaw)

                    ###########################################################
                    #  Busy wait for the loop to complete
                    ###########################################################

                    while(time.time() - tLoopStart < loopTimeSec):
                        time.sleep(0.0001)

                ###############################################################
                #
                # Closing down & Cleaning up
                #
                ###############################################################

                # Loop end time, for stats
                tProgramEnd = time.time()

                # Turn off the motors
                FastWrite(motorDutyCycleLeft, 0)
                FastWrite(motorDutyCycleRight, 0)

                # Wait for the Touch Sensor to be released
                while self.touchSensor.is_pressed:
                    time.sleep(0.01)

                # Calculate loop time
                tLoop = (tProgramEnd - tProgramStart)/loopCount
                log.info("Loop time:" + str(tLoop*1000) + "ms")

                # Print a stop message
                log.info("-----------------------------------")
                log.info("STOP")
                log.info("-----------------------------------")

        # Exit cleanly so that all motors are stopped
        except (KeyboardInterrupt, Exception) as e:
            log.exception(e)
            shutdown()
