#!/usr/bin/env python

# Based on the parameterized  test case technique described here:
#
# http://eli.thegreenplace.net/2011/08/02/python-unit-testing-parametrized-test-cases

import unittest
import time
import sys
import ev3dev.ev3 as ev3

import parameterizedtestcase as ptc

from motor_info import motor_info

class TestTachoMotorAddressValue(ptc.ParameterizedTestCase):

    def test_address_value(self):
        self.assertEqual(self._param['motor'].address, self._param['port'])

    def test_address_value_is_read_only(self):
        with self.assertRaises(AttributeError):
            self._param['motor'].address = "ThisShouldNotWork"

class TestTachoMotorCommandsValue(ptc.ParameterizedTestCase):

    def test_commands_value(self):
        self.assertTrue(set(self._param['motor'].commands) == {'run-forever'
                                                              ,'run-to-abs-pos'
                                                              ,'run-to-rel-pos'
                                                              ,'run-timed'
                                                              ,'run-direct'
                                                              ,'stop'
                                                              ,'reset'})

    def test_commands_value_is_read_only(self):
        with self.assertRaises(AttributeError):
            self._param['motor'].commands = "ThisShouldNotWork"

class TestTachoMotorCountPerRotValue(ptc.ParameterizedTestCase):

    def test_count_per_rot_value(self):
        self.assertEqual(self._param['motor'].count_per_rot, motor_info[self._param['motor'].driver_name]['count_per_rot'])

    def test_count_per_rot_value_is_read_only(self):
        with self.assertRaises(AttributeError):
            self._param['motor'].count_per_rot = "ThisShouldNotWork"

class TestTachoMotorCountPerMValue(ptc.ParameterizedTestCase):

    def test_count_per_m_value(self):
        self.assertEqual(self._param['motor'].count_per_m, motor_info[self._param['motor'].driver_name]['count_per_m'])

    def test_count_per_m_value_is_read_only(self):
        with self.assertRaises(AttributeError):
            self._param['motor'].count_per_m = "ThisShouldNotWork"

class TestTachoMotorFullTravelCountValue(ptc.ParameterizedTestCase):

    def test_full_travel_count_value(self):
        self.assertEqual(self._param['motor'].full_travel_count, motor_info[self._param['motor'].driver_name]['full_travel_count'])

    def test_full_travel_count_value_is_read_only(self):
        with self.assertRaises(AttributeError):
            self._param['motor'].count_per_m = "ThisShouldNotWork"

class TestTachoMotorDriverNameValue(ptc.ParameterizedTestCase):

    def test_driver_name_value(self):
        self.assertEqual(self._param['motor'].driver_name, self._param['driver_name'])

    def test_driver_name_value_is_read_only(self):
        with self.assertRaises(AttributeError):
            self._param['motor'].driver_name = "ThisShouldNotWork"

class TestTachoMotorDutyCycleValue(ptc.ParameterizedTestCase):

    def test_duty_cycle_value_is_read_only(self):
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
        self.assertEqual(self._param['motor'].max_speed, motor_info[self._param['motor'].driver_name]['max_speed'])

    def test_max_speed_value_is_read_only(self):
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
        self.assertEqual(self._param['motor'].position_p, motor_info[self._param['motor'].driver_name]['position_p'])

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
        self.assertEqual(self._param['motor'].position_i, motor_info[self._param['motor'].driver_name]['position_i'])

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
        self.assertEqual(self._param['motor'].position_d, motor_info[self._param['motor'].driver_name]['position_d'])

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
        if ('normal' == motor_info[self._param['motor'].driver_name]['polarity']):
            self._param['motor'].polarity = 'inversed'
        else:
            self._param['motor'].polarity = 'normal'
        self._param['motor'].command = 'reset'
        if ('normal' == motor_info[self._param['motor'].driver_name]['polarity']):
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
        self._param['motor'].speed_sp = motor_info[self._param['motor'].driver_name]['max_speed']
        self.assertEqual(self._param['motor'].speed_sp, motor_info[self._param['motor'].driver_name]['max_speed'])

   def test_speed_sp_large_positive(self):
        with self.assertRaises(IOError):
            self._param['motor'].speed_sp = (motor_info[self._param['motor'].driver_name]['max_speed']+1)

   def test_speed_sp_after_reset(self):
        self._param['motor'].speed_sp = motor_info[self._param['motor'].driver_name]['max_speed']/2
        self.assertEqual(self._param['motor'].speed_sp, motor_info[self._param['motor'].driver_name]['max_speed']/2)
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
        self.assertEqual(self._param['motor'].speed_p, motor_info[self._param['motor'].driver_name]['speed_p'])

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
        self.assertEqual(self._param['motor'].speed_i, motor_info[self._param['motor'].driver_name]['speed_i'])

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
        self.assertEqual(self._param['motor'].speed_d, motor_info[self._param['motor'].driver_name]['speed_d'])

class TestTachoMotorStateValue(ptc.ParameterizedTestCase):

    def test_state_value_is_read_only(self):
        with self.assertRaises(AttributeError):
            self._param['motor'].state = 'ThisShouldNotWork'

    def test_state_value_after_reset(self):
        self._param['motor'].command = 'reset'
        self.assertEqual(self._param['motor'].state, [])

class TestTachoMotorStopActionValue(ptc.ParameterizedTestCase):

    def test_stop_action_illegal(self):
        with self.assertRaises(IOError):
            self._param['motor'].stop_action = 'ThisShouldNotWork'

    def test_stop_action_coast(self):
        self._param['motor'].stop_action = 'coast'
        self.assertEqual(self._param['motor'].stop_action, 'coast')

    def test_stop_action_brake(self):
        self._param['motor'].stop_action = 'brake'
        self.assertEqual(self._param['motor'].stop_action, 'brake')

    def test_stop_action_hold(self):
        self._param['motor'].stop_action = 'hold'
        self.assertEqual(self._param['motor'].stop_action, 'hold')

    def test_stop_action_after_reset(self):
        self._param['motor'].stop_action = 'hold'
        self._param['motor'].command = 'reset'
        self.assertEqual(self._param['motor'].stop_action, 'coast')

class TestTachoMotorStopActionsValue(ptc.ParameterizedTestCase):

    def test_stop_actions_value(self):
        self.assertTrue(set(self._param['motor'].stop_actions) == {'coast'
                                                                  ,'brake'
                                                                  ,'hold'})

    def test_stop_actions_value_is_read_only(self):
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
        self.assertEqual(self._param['motor'].speed_d, 0)

class TestTachoMotorDummy(ptc.ParameterizedTestCase):

    def test_dummy_no_message(self):
        try:
            self.assertEqual(self._param['motor'].speed_d, 100, "Some clever error message {0}".format(self._param['motor'].speed_d))
        except:
           # Remove traceback info as we don't need it
           unittest_exception = sys.exc_info()
           raise unittest_exception[0], unittest_exception[1], unittest_exception[2].tb_next

# Add all the tests to the suite - some tests apply only to certain drivers!

def AddTachoMotorParameterTestsToSuite( suite, driver_name, params ):
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorAddressValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorCommandsValue, param=params))
    if( motor_info[driver_name]['motion_type'] == 'rotation' ):
        suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorCountPerRotValue, param=params))
    if( motor_info[driver_name]['motion_type'] == 'linear' ):
        suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorCountPerMValue, param=params))
        suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorFullTravelCountValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorDriverNameValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorDutyCycleSpValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorMaxSpeedValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorPositionPValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorPositionIValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorPositionDValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorPolarityValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorPositionValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorPositionSpValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorRampDownSpValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorRampUpSpValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorSpeedValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorSpeedSpValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorSpeedPValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorSpeedIValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorSpeedDValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorStateValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorStopActionValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorStopActionsValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorTimeSpValue, param=params))
    suite.addTest(ptc.ParameterizedTestCase.parameterize(TestTachoMotorDummy, param=params))

if __name__ == '__main__':
     for k in motor_info:
        file = open('/sys/class/lego-port/port4/set_device', 'w')
        file.write('{0}\n'.format(k))
        file.close()
        time.sleep(0.5)

        params = { 'motor': ev3.Motor('outA'), 'port': 'outA', 'driver_name': k }

        suite = unittest.TestSuite()

        AddTachoMotorParameterTestsToSuite( suite, k, params )
        print( '-------------------- TESTING {0} --------------'.format(k))
        unittest.TextTestRunner(verbosity=1,buffer=True ).run(suite)

