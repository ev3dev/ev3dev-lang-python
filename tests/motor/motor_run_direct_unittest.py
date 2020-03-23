#!/usr/bin/env python

# Based on the parameterized  test case technique described here:
#
# http://eli.thegreenplace.net/2011/08/02/python-unit-testing-parametrized-test-cases

import unittest
import time
import ev3dev.ev3 as ev3
import parameterizedtestcase as ptc


class TestMotorRunDirect(ptc.ParameterizedTestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def initialize_motor(self):
        self._param['motor'].command = 'reset'

    def run_direct_duty_cycles(self, stop_action, duty_cycles):
        self._param['motor'].stop_action = stop_action
        self._param['motor'].command = 'run-direct'

        for i in duty_cycles:
            self._param['motor'].duty_cycle_sp = i
            time.sleep(0.5)

        self._param['motor'].command = 'stop'

    def test_stop_coast_duty_cycles(self):
        self.initialize_motor()
        self.run_direct_duty_cycles('coast', [0, 20, 40, 60, 80, 100, 66, 33, 0, -20, -40, -60, -80, -100, -66, -33, 0])


# Add all the tests to the suite - some tests apply only to certain drivers!


def AddTachoMotorRunDirectTestsToSuite(suite, driver_name, params):
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestMotorRunDirect, param=params))


if __name__ == '__main__':
    params = {'motor': ev3.Motor('outA'), 'port': 'outA', 'driver_name': 'lego-ev3-l-motor'}

    suite = unittest.TestSuite()

    AddTachoMotorRunDirectTestsToSuite(suite, 'lego-ev3-l-motor', params)

    unittest.TextTestRunner(verbosity=1, buffer=True).run(suite)
