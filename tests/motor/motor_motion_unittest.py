#!/usr/bin/env python

# Based on the parameterized  test case technique described here:
#
# http://eli.thegreenplace.net/2011/08/02/python-unit-testing-parametrized-test-cases

import unittest
import time
import ev3dev.ev3 as ev3

import parameterizedtestcase as ptc

from motor_info import motor_info

class TestMotorMotion(ptc.ParameterizedTestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def initialize_motor(self):
        self._param['motor'].command = 'reset'

    def run_to_positions(self,stop_action,command,speed_sp,positions,tolerance):
        self._param['motor'].stop_action = stop_action
        self._param['motor'].speed_sp = speed_sp

        target = self._param['motor'].position

        for i in positions:
            self._param['motor'].position_sp = i
            if 'run-to-rel-pos' == command:
                target += i
            else:
                target = i
            print( "PRE position = {0} i = {1} target = {2}".format(self._param['motor'].position, i, target))
            self._param['motor'].command = command
            while 'running' in self._param['motor'].state:
                pass
            print( "POS position = {0} i = {1} target = {2}".format(self._param['motor'].position, i, target))
            self.assertGreaterEqual(tolerance, abs(self._param['motor'].position - target))
            time.sleep(0.2)

        self._param['motor'].command = 'stop'

    def test_stop_brake_no_ramp_med_speed_relative(self):
        self.initialize_motor()
        self.run_to_positions('brake','run-to-rel-pos',400,[0,90,180,360,720,-720,-360,-180,-90,0],20)

    def test_stop_hold_no_ramp_med_speed_relative(self):
        self.initialize_motor()
        self.run_to_positions('hold','run-to-rel-pos',400,[0,90,180,360,720,-720,-360,-180,-90,0],5)

    def test_stop_brake_no_ramp_low_speed_relative(self):
        self.initialize_motor()
        self.run_to_positions('brake','run-to-rel-pos',100,[0,90,180,360,720,-720,-360,-180,-90,0],20)

    def test_stop_hold_no_ramp_low_speed_relative(self):
        self.initialize_motor()
        self.run_to_positions('hold','run-to-rel-pos',100,[0,90,180,360,720,-720,-360,-180,-90,0],5)

    def test_stop_brake_no_ramp_high_speed_relative(self):
        self.initialize_motor()
        self.run_to_positions('brake','run-to-rel-pos',900,[0,90,180,360,720,-720,-360,-180,-90,0],50)

    def test_stop_hold_no_ramp_high_speed_relative(self):
        self.initialize_motor()
        self.run_to_positions('hold','run-to-rel-pos',100,[0,90,180,360,720,-720,-360,-180,-90,0],5)

    def test_stop_brake_no_ramp_med_speed_absolute(self):
        self.initialize_motor()
        self.run_to_positions('brake','run-to-abs-pos',400,[0,90,180,360,180,90,0,-90,-180,-360,-180,-90,0],20)

    def test_stop_hold_no_ramp_med_speed_absolute(self):
        self.initialize_motor()
        self.run_to_positions('hold','run-to-abs-pos',400,[0,90,180,360,180,90,0,-90,-180,-360,-180,-90,0],5)

    def test_stop_brake_no_ramp_low_speed_absolute(self):
        self.initialize_motor()
        self.run_to_positions('brake','run-to-abs-pos',100,[0,90,180,360,180,90,0,-90,-180,-360,-180,-90,0],20)

    def test_stop_hold_no_ramp_low_speed_absolute(self):
        self.initialize_motor()
        self.run_to_positions('hold','run-to-abs-pos',100,[0,90,180,360,180,90,0,-90,-180,-360,-180,-90,0],5)

    def test_stop_brake_no_ramp_high_speed_absolute(self):
        self.initialize_motor()
        self.run_to_positions('brake','run-to-abs-pos',900,[0,90,180,360,180,90,0,-90,-180,-360,-180,-90,0],50)

    def test_stop_hold_no_ramp_high_speed_absolute(self):
        self.initialize_motor()
        self.run_to_positions('hold','run-to-abs-pos',100,[0,90,180,360,180,90,0,-90,-180,-360,-180,-90,0],5)

# Add all the tests to the suite - some tests apply only to certain drivers!

def AddTachoMotorMotionTestsToSuite( suite, driver_name, params ):
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestMotorMotion, param=params))

if __name__ == '__main__':
    params = { 'motor': ev3.Motor('outA'), 'port': 'outA', 'driver_name': 'lego-ev3-l-motor' }

    suite = unittest.TestSuite()

    AddTachoMotorMotionTestsToSuite( suite, 'lego-ev3-l-motor', params )

    unittest.TextTestRunner(verbosity=1,buffer=True ).run(suite)
