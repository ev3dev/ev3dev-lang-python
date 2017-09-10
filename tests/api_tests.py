#!/usr/bin/env python3
import unittest, sys, os

FAKE_SYS = os.path.join(os.path.dirname(__file__), 'fake-sys')

sys.path.append(FAKE_SYS)
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from populate_arena import populate_arena
from clean_arena    import clean_arena

import ev3dev.core as ev3
import argparse

ev3.Device.DEVICE_ROOT_PATH = os.path.join(FAKE_SYS, 'arena')
medium_motor_port = 'outA'
medium_motor_driver = 'lego-ev3-m-motor'

class TestAPI(unittest.TestCase):
    def test_device(self):
        clean_arena()
        populate_arena({'medium_motor' : [0, medium_motor_port], 'infrared_sensor' : [0, 'in1']})

        d = ev3.Device('tacho-motor', 'motor*')
        self.assertTrue(d.connected)

        d = ev3.Device('tacho-motor', 'motor0')
        self.assertTrue(d.connected)

        d = ev3.Device('tacho-motor', 'motor*', driver_name=medium_motor_driver)
        self.assertTrue(d.connected)

        d = ev3.Device('tacho-motor', 'motor*', address=medium_motor_port)
        self.assertTrue(d.connected)

        d = ev3.Device('tacho-motor', 'motor*', address=medium_motor_port, driver_name='not-valid')
        self.assertTrue(not d.connected)

        d = ev3.Device('lego-sensor', 'sensor*')
        self.assertTrue(d.connected)

        d = ev3.Device('this-does-not-exist')
        self.assertFalse(d.connected)

    def test_medium_motor(self):
        def dummy(self):
            pass

        clean_arena()
        populate_arena({'medium_motor' : [0, medium_motor_port]})

        # Do not write motor.command on exit (so that fake tree stays intact)
        ev3.MediumMotor.__del__ = dummy

        m = ev3.MediumMotor()

        self.assertTrue(m.connected);

        self.assertEqual(m.device_index, 0)

        # Check that reading twice works:
        self.assertEqual(m.driver_name, medium_motor_driver)
        self.assertEqual(m.driver_name, medium_motor_driver)

        self.assertEqual(m.count_per_rot,            360)
        self.assertEqual(m.commands,                 ['run-forever', 'run-to-abs-pos', 'run-to-rel-pos', 'run-timed', 'run-direct', 'stop', 'reset'])
        self.assertEqual(m.duty_cycle,               0)
        self.assertEqual(m.duty_cycle_sp,            42)
        self.assertEqual(m.polarity,                 'normal')
        self.assertEqual(m.address,                  medium_motor_port)
        self.assertEqual(m.position,                 42)
        self.assertEqual(m.position_sp,              42)
        self.assertEqual(m.ramp_down_sp,             0)
        self.assertEqual(m.ramp_up_sp,               0)
        self.assertEqual(m.speed,                    0)
        self.assertEqual(m.speed_sp,                 0)
        self.assertEqual(m.state,                    ['running'])
        self.assertEqual(m.stop_action,              'coast')
        self.assertEqual(m.time_sp,                  1000)

        with self.assertRaises(Exception):
            c = m.command

    def test_infrared_sensor(self):
        clean_arena()
        populate_arena({'infrared_sensor' : [0, 'in1']})

        s = ev3.InfraredSensor()

        self.assertTrue(s.connected)

        self.assertEqual(s.device_index,    0)
        self.assertEqual(s.bin_data_format, 's8')
        self.assertEqual(s.bin_data('<b'),  (16,))
        self.assertEqual(s.num_values,      1)
        self.assertEqual(s.address,         'in1')
        self.assertEqual(s.value(0),        16)

if __name__ == "__main__":

    # command line args
    parser = argparse.ArgumentParser(description="Used to test ev3dev-lang-python basic functionality")
    parser.add_argument("--medium-motor-port", type=str, default='outA')
    parser.add_argument("--medium-motor-driver", type=str, default='lego-ev3-m-motor')
    parser.add_argument('unittest_args', nargs='*')
    args = parser.parse_args()

    medium_motor_port = args.medium_motor_port
    medium_motor_driver = args.medium_motor_driver

    # Now set the sys.argv to the unittest_args (leaving sys.argv[0] alone)
    sys.argv[1:] = args.unittest_args

    unittest.main()
