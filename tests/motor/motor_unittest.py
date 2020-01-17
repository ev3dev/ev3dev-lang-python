#!/usr/bin/env python

# Based on the parameterized  test case technique described here:
#
# http://eli.thegreenplace.net/2011/08/02/python-unit-testing-parametrized-test-cases
import unittest
import time
import ev3dev.ev3 as ev3

import parameterizedtestcase as ptc
from motor_info import motor_info

class TestTachoMotorAddressValue(ptc.ParameterizedTestCase):

    def test_address_value(self):
        # Use the class variable
        self.assertEqual(self._param['motor'].address, self._param['port'])

    def test_address_value_is_read_only(self):
        # Use the class variable
        with self.assertRaises(AttributeError):
            self._param['motor'].address = "ThisShouldNotWork"

class TestTachoMotorCommandsValue(ptc.ParameterizedTestCase):

    def test_commands_value(self):
        self.assertTrue(self._param['motor'].commands == self._param['commands'])

    def test_commands_value_is_read_only(self):
        # Use the class variable
        with self.assertRaises(AttributeError):
            self._param['motor'].commands = "ThisShouldNotWork"

class TestTachoMotorCountPerRotValue(ptc.ParameterizedTestCase):

    def test_count_per_rot_value(self):
        # This is not available for linear motors - move to driver specific tests?
        self.assertEqual(self._param['motor'].count_per_rot, 360)

    def test_count_per_rot_value_is_read_only(self):
        # Use the class variable
        with self.assertRaises(AttributeError):
            self._param['motor'].count_per_rot = "ThisShouldNotWork"

class TestTachoMotorDriverNameValue(ptc.ParameterizedTestCase):

    def test_driver_name_value(self):
        # move to driver specific tests?
        self.assertEqual(self._param['motor'].driver_name, self._param['driver_name'])

    def test_driver_name_value_is_read_only(self):
        # Use the class variable
        with self.assertRaises(AttributeError):
            self._param['motor'].driver_name = "ThisShouldNotWork"

class TestTachoMotorDutyCycleValue(ptc.ParameterizedTestCase):

    def test_duty_cycle_value_is_read_only(self):
        # Use the class variable
        with self.assertRaises(AttributeError):
            self._param['motor'].duty_cycle = "ThisShouldNotWork"

    def test_duty_cycle_value_after_reset(self):
        self._param['motor'].command = 'reset'
        self.assertEqual(self._param['motor'].duty_cycle, 0)

class TestTachoMotorDutyCycleSpValue(ptc.ParameterizedTestCase):

    def test_duty_cycle_sp_large_negative(self):
        with self.assertRaises(IOError):
            self._param['motor'].duty_cycle_sp = -101

    def test_duty_cycle_sp_max_negative(self):
        self._param['motor'].duty_cycle_sp = -100
        self.assertEqual(self._param['motor'].duty_cycle_sp, -100)

    def test_duty_cycle_sp_min_negative(self):
        self._param['motor'].duty_cycle_sp = -1
        self.assertEqual(self._param['motor'].duty_cycle_sp, -1)

    def test_duty_cycle_sp_zero(self):
        self._param['motor'].duty_cycle_sp = 0
        self.assertEqual(self._param['motor'].duty_cycle_sp, 0)

    def test_duty_cycle_sp_min_positive(self):
        self._param['motor'].duty_cycle_sp = 1
        self.assertEqual(self._param['motor'].duty_cycle_sp, 1)

    def test_duty_cycle_sp_max_positive(self):
        self._param['motor'].duty_cycle_sp = 100
        self.assertEqual(self._param['motor'].duty_cycle_sp, 100)

    def test_duty_cycle_sp_large_positive(self):
        with self.assertRaises(IOError):
            self._param['motor'].duty_cycle_sp = 101

    def test_duty_cycle_sp_after_reset(self):
        self._param['motor'].duty_cycle_sp = 100
        self.assertEqual(self._param['motor'].duty_cycle_sp, 100)
        self._param['motor'].command = 'reset'
        self.assertEqual(self._param['motor'].duty_cycle_sp, 0)


class TestTachoMotorMaxSpeedValue(ptc.ParameterizedTestCase):

    def test_max_speed_value(self):
        # This is not available for linear motors - move to driver specific tests?
        self.assertEqual(self._param['motor'].max_speed, motor_info[self._param['motor'].driver_name]['max_speed'])

    def test_max_speed_value_is_read_only(self):
        # Use the class variable
        with self.assertRaises(AttributeError):
            self._param['motor'].max_speed = "ThisShouldNotWork"

class TestTachoMotorPositionPValue(ptc.ParameterizedTestCase):

    def test_position_p_negative(self):
        with self.assertRaises(IOError):
            self._param['motor'].position_p = -1

    def test_position_p_zero(self):
        self._param['motor'].position_p = 0
        self.assertEqual(self._param['motor'].position_p, 0)

    def test_position_p_positive(self):
        self._param['motor'].position_p = 1
        self.assertEqual(self._param['motor'].position_p, 1)

    def test_position_p_after_reset(self):
        self._param['motor'].position_p = 1

        self._param['motor'].command = 'reset'

        if 'hold_pid' in self._param:
            expected = self._param['hold_pid']['kP']
        else:
             expected = motor_info[self._param['motor'].driver_name]['position_p']
        self.assertEqual(self._param['motor'].position_p, expected)

class TestTachoMotorPositionIValue(ptc.ParameterizedTestCase):

    def test_position_i_negative(self):
        with self.assertRaises(IOError):
            self._param['motor'].position_i = -1

    def test_position_i_zero(self):
        self._param['motor'].position_i = 0
        self.assertEqual(self._param['motor'].position_i, 0)

    def test_position_i_positive(self):
        self._param['motor'].position_i = 1
        self.assertEqual(self._param['motor'].position_i, 1)

    def test_position_i_after_reset(self):
        self._param['motor'].position_i = 1

        self._param['motor'].command = 'reset'

        if 'hold_pid' in self._param:
            expected = self._param['hold_pid']['kI']
        else:
             expected = motor_info[self._param['motor'].driver_name]['position_i']
        self.assertEqual(self._param['motor'].position_i, expected)

class TestTachoMotorPositionDValue(ptc.ParameterizedTestCase):

    def test_position_d_negative(self):
        with self.assertRaises(IOError):
            self._param['motor'].position_d = -1

    def test_position_d_zero(self):
        self._param['motor'].position_d = 0
        self.assertEqual(self._param['motor'].position_d, 0)

    def test_position_d_positive(self):
        self._param['motor'].position_d = 1
        self.assertEqual(self._param['motor'].position_d, 1)

    def test_position_d_after_reset(self):
        self._param['motor'].position_d = 1

        self._param['motor'].command = 'reset'

        if 'hold_pid' in self._param:
            expected = self._param['hold_pid']['kD']
        else:
             expected = motor_info[self._param['motor'].driver_name]['position_d']
        self.assertEqual(self._param['motor'].position_d, expected)

class TestTachoMotorPolarityValue(ptc.ParameterizedTestCase):

    def test_polarity_normal_value(self):
        self._param['motor'].polarity = 'normal'
        self.assertEqual(self._param['motor'].polarity, 'normal')

    def test_polarity_inversed_value(self):
        self._param['motor'].polarity = 'inversed'
        self.assertEqual(self._param['motor'].polarity, 'inversed')

    def test_polarity_illegal_value(self):
        with self.assertRaises(IOError):
            self._param['motor'].polarity = "ThisShouldNotWork"

    def test_polarity_after_reset(self):
        if 'normal' == motor_info[self._param['motor'].driver_name]['polarity']:
            self._param['motor'].polarity = 'inversed'
        else:
            self._param['motor'].polarity = 'normal'

        self._param['motor'].command = 'reset'

        if 'normal' == motor_info[self._param['motor'].driver_name]['polarity']:
            self.assertEqual(self._param['motor'].polarity, 'normal')
        else:
            self.assertEqual(self._param['motor'].polarity, 'inversed')

class TestTachoMotorPositionValue(ptc.ParameterizedTestCase):

    def test_position_large_negative(self):
        self._param['motor'].position = -1000000
        self.assertEqual(self._param['motor'].position, -1000000)

    def test_position_min_negative(self):
        self._param['motor'].position = -1
        self.assertEqual(self._param['motor'].position, -1)

    def test_position_zero(self):
        self._param['motor'].position = 0
        self.assertEqual(self._param['motor'].position, 0)

    def test_position_min_positive(self):
        self._param['motor'].position = 1
        self.assertEqual(self._param['motor'].position, 1)

    def test_position_large_positive(self):
        self._param['motor'].position = 1000000
        self.assertEqual(self._param['motor'].position, 1000000)

    def test_position_after_reset(self):
        self._param['motor'].position = 100
        self.assertEqual(self._param['motor'].position, 100)
        self._param['motor'].command = 'reset'
        self.assertEqual(self._param['motor'].position, 0)


class TestTachoMotorPositionSpValue(ptc.ParameterizedTestCase):

    def test_position_sp_large_negative(self):
        self._param['motor'].position_sp = -1000000
        self.assertEqual(self._param['motor'].position_sp, -1000000)

    def test_position_sp_min_negative(self):
        self._param['motor'].position_sp = -1
        self.assertEqual(self._param['motor'].position_sp, -1)

    def test_position_sp_zero(self):
        self._param['motor'].position_sp = 0
        self.assertEqual(self._param['motor'].position_sp, 0)

    def test_position_sp_min_positive(self):
        self._param['motor'].position_sp = 1
        self.assertEqual(self._param['motor'].position_sp, 1)

    def test_position_sp_large_positive(self):
        self._param['motor'].position_sp = 1000000
        self.assertEqual(self._param['motor'].position_sp, 1000000)

    def test_position_sp_after_reset(self):
        self._param['motor'].position_sp = 100
        self.assertEqual(self._param['motor'].position_sp, 100)
        self._param['motor'].command = 'reset'
        self.assertEqual(self._param['motor'].position_sp, 0)

class TestTachoMotorRampDownSpValue(ptc.ParameterizedTestCase):

    def test_ramp_down_sp_negative_value(self):
        with self.assertRaises(IOError):
            self._param['motor'].ramp_down_sp = -1

    def test_ramp_down_sp_zero(self):
        self._param['motor'].ramp_down_sp = 0
        self.assertEqual(self._param['motor'].ramp_down_sp, 0)

    def test_ramp_down_sp_min_positive(self):
        self._param['motor'].ramp_down_sp = 1
        self.assertEqual(self._param['motor'].ramp_down_sp, 1)

    def test_ramp_down_sp_max_positive(self):
        self._param['motor'].ramp_down_sp = 60000
        self.assertEqual(self._param['motor'].ramp_down_sp, 60000)

    def test_ramp_down_sp_large_positive(self):
        with self.assertRaises(IOError):
            self._param['motor'].ramp_down_sp = 60001

    def test_ramp_down_sp_after_reset(self):
        self._param['motor'].ramp_down_sp = 100
        self.assertEqual(self._param['motor'].ramp_down_sp, 100)
        self._param['motor'].command = 'reset'
        self.assertEqual(self._param['motor'].ramp_down_sp, 0)
        
class TestTachoMotorRampUpSpValue(ptc.ParameterizedTestCase):

    def test_ramp_up_negative_value(self):
        with self.assertRaises(IOError):
            self._param['motor'].ramp_up_sp = -1

    def test_ramp_up_sp_zero(self):
        self._param['motor'].ramp_up_sp = 0
        self.assertEqual(self._param['motor'].ramp_up_sp, 0)

    def test_ramp_up_sp_min_positive(self):
        self._param['motor'].ramp_up_sp = 1
        self.assertEqual(self._param['motor'].ramp_up_sp, 1)

    def test_ramp_up_sp_max_positive(self):
        self._param['motor'].ramp_up_sp = 60000
        self.assertEqual(self._param['motor'].ramp_up_sp, 60000)

    def test_ramp_up_sp_large_positive(self):
        with self.assertRaises(IOError):
            self._param['motor'].ramp_up_sp = 60001

    def test_ramp_up_sp_after_reset(self):
        self._param['motor'].ramp_up_sp = 100
        self.assertEqual(self._param['motor'].ramp_up_sp, 100)
        self._param['motor'].command = 'reset'
        self.assertEqual(self._param['motor'].ramp_up_sp, 0)
        
class TestTachoMotorSpeedValue(ptc.ParameterizedTestCase):

    def test_speed_value_is_read_only(self):
        # Use the class variable
        with self.assertRaises(AttributeError):
            self._param['motor'].speed = 1

    def test_speed_value_after_reset(self):
        self._param['motor'].command = 'reset'
        self.assertEqual(self._param['motor'].speed, 0)
        
class TestTachoMotorSpeedSpValue(ptc.ParameterizedTestCase):

   def test_speed_sp_large_negative(self):
        with self.assertRaises(IOError):
            self._param['motor'].speed_sp = -(motor_info[self._param['motor'].driver_name]['max_speed']+1)

   def test_speed_sp_max_negative(self):
        self._param['motor'].speed_sp = -motor_info[self._param['motor'].driver_name]['max_speed']
        self.assertEqual(self._param['motor'].speed_sp, -motor_info[self._param['motor'].driver_name]['max_speed'])

   def test_speed_sp_min_negative(self):
        self._param['motor'].speed_sp = -1
        self.assertEqual(self._param['motor'].speed_sp, -1)

   def test_speed_sp_zero(self):
        self._param['motor'].speed_sp = 0
        self.assertEqual(self._param['motor'].speed_sp, 0)

   def test_speed_sp_min_positive(self):
        self._param['motor'].speed_sp = 1
        self.assertEqual(self._param['motor'].speed_sp, 1)

   def test_speed_sp_max_positive(self):
        self._param['motor'].speed_sp = (motor_info[self._param['motor'].driver_name]['max_speed'])
        self.assertEqual(self._param['motor'].speed_sp, motor_info[self._param['motor'].driver_name]['max_speed'])

   def test_speed_sp_large_positive(self):
        with self.assertRaises(IOError):
            self._param['motor'].speed_sp = motor_info[self._param['motor'].driver_name]['max_speed'] + 1

   def test_speed_sp_after_reset(self):
        self._param['motor'].speed_sp = 100
        self.assertEqual(self._param['motor'].speed_sp, 100)
        self._param['motor'].command = 'reset'
        self.assertEqual(self._param['motor'].speed_sp, 0)
        
class TestTachoMotorSpeedPValue(ptc.ParameterizedTestCase):

    def test_speed_i_negative(self):
        with self.assertRaises(IOError):
            self._param['motor'].speed_p = -1

    def test_speed_p_zero(self):
        self._param['motor'].speed_p = 0
        self.assertEqual(self._param['motor'].speed_p, 0)

    def test_speed_p_positive(self):
        self._param['motor'].speed_p = 1
        self.assertEqual(self._param['motor'].speed_p, 1)

    def test_speed_p_after_reset(self):
        self._param['motor'].speed_p = 1

        self._param['motor'].command = 'reset'

        if 'speed_pid' in self._param:
            expected = self._param['speed_pid']['kP']
        else:
             expected = motor_info[self._param['motor'].driver_name]['speed_p']
        self.assertEqual(self._param['motor'].speed_p, expected)

class TestTachoMotorSpeedIValue(ptc.ParameterizedTestCase):

    def test_speed_i_negative(self):
        with self.assertRaises(IOError):
            self._param['motor'].speed_i = -1

    def test_speed_i_zero(self):
        self._param['motor'].speed_i = 0
        self.assertEqual(self._param['motor'].speed_i, 0)

    def test_speed_i_positive(self):
        self._param['motor'].speed_i = 1
        self.assertEqual(self._param['motor'].speed_i, 1)

    def test_speed_i_after_reset(self):
        self._param['motor'].speed_i = 1

        self._param['motor'].command = 'reset'

        if 'speed_pid' in self._param:
            expected = self._param['speed_pid']['kI']
        else:
             expected = motor_info[self._param['motor'].driver_name]['speed_i']
        self.assertEqual(self._param['motor'].speed_i, expected)

class TestTachoMotorSpeedDValue(ptc.ParameterizedTestCase):

    def test_speed_d_negative(self):
        with self.assertRaises(IOError):
            self._param['motor'].speed_d = -1

    def test_speed_d_zero(self):
        self._param['motor'].speed_d = 0
        self.assertEqual(self._param['motor'].speed_d, 0)

    def test_speed_d_positive(self):
        self._param['motor'].speed_d = 1
        self.assertEqual(self._param['motor'].speed_d, 1)

    def test_speed_d_after_reset(self):
        self._param['motor'].speed_d = 1

        self._param['motor'].command = 'reset'

        if 'speed_pid' in self._param:
            expected = self._param['speed_pid']['kD']
        else:
             expected = motor_info[self._param['motor'].driver_name]['speed_d']
        self.assertEqual(self._param['motor'].speed_d, expected)

class TestTachoMotorStateValue(ptc.ParameterizedTestCase):

    def test_state_value_is_read_only(self):
        # Use the class variable
        with self.assertRaises(AttributeError):
            self._param['motor'].state = 'ThisShouldNotWork'

    def test_state_value_after_reset(self):
        self._param['motor'].command = 'reset'
        self.assertEqual(self._param['motor'].state, [])

#    def test_stop_action_value(self):
#        self.assertEqual(self._param['motor'].stop_action, 'coast')
class TestTachoMotorStopCommandValue(ptc.ParameterizedTestCase):

    def test_stop_action_illegal(self):
        with self.assertRaises(IOError):
            self._param['motor'].stop_action = 'ThisShouldNotWork'

    def test_stop_action_coast(self):
        if 'coast' in self._param['stop_actions']:
            self._param['motor'].stop_action = 'coast'
            self.assertEqual(self._param['motor'].stop_action, 'coast')
        else:
            with self.assertRaises(IOError):
                self._param['motor'].stop_action = 'coast'

    def test_stop_action_brake(self):
        if 'brake' in self._param['stop_actions']:
            self._param['motor'].stop_action = 'brake'
            self.assertEqual(self._param['motor'].stop_action, 'brake')
        else:
            with self.assertRaises(IOError):
                self._param['motor'].stop_action = 'brake'

    def test_stop_action_hold(self):
        if 'hold' in self._param['stop_actions']:
            self._param['motor'].stop_action = 'hold'
            self.assertEqual(self._param['motor'].stop_action, 'hold')
        else:
            with self.assertRaises(IOError):
                self._param['motor'].stop_action = 'hold'

    def test_stop_action_after_reset(self):
        action = 1
        # controller may only support one stop action
        if len(self._param['stop_actions']) < 2:
            action = 0
        self._param['motor'].stop_action = self._param['stop_actions'][action]
        self._param['motor'].command = 'reset'
        self.assertEqual(self._param['motor'].stop_action, self._param['stop_actions'][0])

class TestTachoMotorStopCommandsValue(ptc.ParameterizedTestCase):

    def test_stop_actions_value(self):
        self.assertTrue(self._param['motor'].stop_actions == self._param['stop_actions'])

    def test_stop_actions_value_is_read_only(self):
        # Use the class variable
        with self.assertRaises(AttributeError):
            self._param['motor'].stop_actions = "ThisShouldNotWork"

class TestTachoMotorTimeSpValue(ptc.ParameterizedTestCase):

    def test_time_sp_negative(self):
        with self.assertRaises(IOError):
            self._param['motor'].time_sp = -1

    def test_time_sp_zero(self):
        self._param['motor'].time_sp = 0
        self.assertEqual(self._param['motor'].time_sp, 0)

    def test_time_sp_min_positive(self):
        self._param['motor'].time_sp = 1
        self.assertEqual(self._param['motor'].time_sp, 1)

    def test_time_sp_large_positive(self):
        self._param['motor'].time_sp = 1000000
        self.assertEqual(self._param['motor'].time_sp, 1000000)

    def test_time_sp_after_reset(self):
        self._param['motor'].time_sp = 1
        self._param['motor'].command = 'reset'
        self.assertEqual(self._param['motor'].time_sp, 0)

ev3_params = {
    'motor': ev3.Motor('outA'),
    'port': 'outA',
    'driver_name': 'lego-ev3-l-motor',
    'commands': ['run-forever', 'run-to-abs-pos', 'run-to-rel-pos', 'run-timed', 'run-direct', 'stop', 'reset'],
    'stop_actions': ['coast', 'brake', 'hold'],
}
evb_params = {
    'motor': ev3.Motor('evb-ports:outA'),
    'port': 'evb-ports:outA',
    'driver_name': 'lego-ev3-l-motor',
    'commands': ['run-forever', 'run-to-abs-pos', 'run-to-rel-pos', 'run-timed', 'run-direct', 'stop', 'reset'],
    'stop_actions': ['coast', 'brake', 'hold'],
}
brickpi_params = {
    'motor': ev3.Motor('ttyAMA0:MA'),
    'port': 'ttyAMA0:MA',
    'driver_name': 'lego-nxt-motor',
    'commands': ['run-forever', 'run-to-abs-pos', 'run-to-rel-pos', 'run-timed', 'run-direct', 'stop', 'reset'],
    'stop_actions': ['coast', 'hold'],
    'speed_pid': { 'kP': 1000, 'kI': 60, 'kD': 0 },
    'hold_pid': { 'kP': 20000, 'kI': 0, 'kD': 0 },
}
pistorms_params = {
    'motor': ev3.Motor('pistorms:BAM1'),
    'port': 'pistorms:BAM1',
    'driver_name': 'lego-nxt-motor',
    'commands': ['run-forever', 'run-to-abs-pos', 'run-to-rel-pos', 'run-timed', 'stop', 'reset'],
    'stop_actions': ['coast', 'brake', 'hold'],
    'speed_pid': { 'kP': 1000, 'kI': 60, 'kD': 0 },
    'hold_pid': { 'kP': 20000, 'kI': 0, 'kD': 0 },
}
paramsA = ev3_params
paramsA['motor'].command = 'reset'

suite = unittest.TestSuite()

suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorAddressValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorCommandsValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorCountPerRotValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorDriverNameValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorDutyCycleSpValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorMaxSpeedValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorPositionPValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorPositionIValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorPositionDValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorPolarityValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorPositionValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorPositionSpValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorRampDownSpValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorRampUpSpValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorSpeedValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorSpeedSpValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorSpeedPValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorSpeedIValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorSpeedDValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorStateValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorStopCommandValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorStopCommandsValue, param=paramsA))
suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorTimeSpValue, param=paramsA))


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=1,buffer=True ).run(suite)

exit()

# Move these up later

class TestMotorRelativePosition(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._motor = ev3.Motor('outA')
        cls._motor.speed_sp = 400
        cls._motor.ramp_up_sp = 300
        cls._motor.ramp_down_sp = 300
        cls._motor.position = 0
        cls._motor.position_sp = 180
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    @unittest.skip("Skipping coast mode - always fails")
    def test_stop_coast(self):
        self._motor.stop_action = 'coast'
        self._motor.command = 'run-to-rel-pos'
        time.sleep(1)
        self.assertGreaterEqual(1, abs(self._motor.position - self._motor.position_sp))

    def test_stop_brake(self):
        self._motor.stop_action = 'brake'
        self._motor.position = 0

        for i in range(1,5):
            self._motor.command = 'run-to-rel-pos'
            time.sleep(1)
            print(self._motor.position)
            self.assertGreaterEqual(8, abs(self._motor.position - (i * self._motor.position_sp)))

    def test_stop_hold(self):
        self._motor.stop_action = 'hold'
        self._motor.position = 0

        for i in range(1,5):
            self._motor.command = 'run-to-rel-pos'
            time.sleep(1)
            print(self._motor.position)
            self.assertGreaterEqual(1, abs(self._motor.position - (i * self._motor.position_sp)))


if __name__ == '__main__':
    unittest.main(verbosity=2,buffer=True ).run(suite)
