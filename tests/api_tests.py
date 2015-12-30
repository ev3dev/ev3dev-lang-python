#!/usr/bin/env python
import unittest, sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import ev3dev.ev3 as ev3

ev3.Device.DEVICE_ROOT_PATH = os.path.join(os.path.dirname(__file__), 'fake-sys')

class TestAPI(unittest.TestCase):
    def test_device(self):
        d = ev3.Device('tacho-motor', 'motor*')
        self.assertTrue(d.connected)

        d = ev3.Device('tacho-motor', 'motor0')
        self.assertTrue(d.connected)

        d = ev3.Device('tacho-motor', 'motor*', driver_name='lego-ev3-m-motor')
        self.assertTrue(d.connected)

        d = ev3.Device('tacho-motor', 'motor*', address='outA')
        self.assertTrue(d.connected)

        d = ev3.Device('tacho-motor', 'motor*', address='outA', driver_name='not-valid')
        self.assertTrue(not d.connected)

        d = ev3.Device('lego-sensor', 'sensor*')
        self.assertTrue(d.connected)

    def test_medium_motor(self):
        def dummy(self):
            pass

        # Do not write motor.command on exit (so that fake tree stays intact)
        ev3.MediumMotor.__del__ = dummy

        m = ev3.MediumMotor()

        self.assertTrue(m.connected);

        self.assertEqual(m.device_index, 0)

        # Check that reading twice works:
        self.assertEqual(m.driver_name, 'lego-ev3-m-motor')
        self.assertEqual(m.driver_name, 'lego-ev3-m-motor')

        self.assertEqual(m.count_per_rot,            360)
        self.assertEqual(m.commands,                 ['run-forever', 'run-to-abs-pos', 'run-to-rel-pos', 'run-timed', 'run-direct', 'stop', 'reset'])
        self.assertEqual(m.duty_cycle,               0)
        self.assertEqual(m.duty_cycle_sp,            42)
        self.assertEqual(m.encoder_polarity,         'normal')
        self.assertEqual(m.polarity,                 'normal')
        self.assertEqual(m.address,                  'outA')
        self.assertEqual(m.position,                 42)
        self.assertEqual(m.position_sp,              42)
        self.assertEqual(m.ramp_down_sp,             0)
        self.assertEqual(m.ramp_up_sp,               0)
        self.assertEqual(m.speed,                    0)
        self.assertEqual(m.speed_regulation_enabled, 'off')
        self.assertEqual(m.speed_sp,                 0)
        self.assertEqual(m.state,                    ['running'])
        self.assertEqual(m.stop_command,             'coast')
        self.assertEqual(m.time_sp,                  1000)

        with self.assertRaises(Exception):
            c = m.command

    def test_infrared_sensor(self):
        s = ev3.InfraredSensor()

        self.assertTrue(s.connected)

        self.assertEqual(s.device_index,    0)
        self.assertEqual(s.bin_data_format, 's8')
        self.assertEqual(s.bin_data('<b'),  (16,))
        self.assertEqual(s.num_values,      1)
        self.assertEqual(s.address,         'in1')
        self.assertEqual(s.value(0),        16)

if __name__ == "__main__":
    unittest.main()
