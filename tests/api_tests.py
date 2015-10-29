#!/usr/bin/env python
import unittest, sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import ev3dev

ev3dev.Device.DEVICE_ROOT_PATH = os.path.join(os.path.dirname(__file__), 'fake_sys_class')

class TestAPI(unittest.TestCase):
    def test_medium_motor(self):
        m = ev3dev.MediumMotor()

        self.assertTrue(m.connected);
        self.assertEqual(m.count_per_rot,            360)
        self.assertEqual(m.driver_name,              'lego-ev3-m-motor')
        self.assertEqual(m.duty_cycle,               0)
        self.assertEqual(m.duty_cycle_sp,            42)
        self.assertEqual(m.encoder_polarity,         'normal')
        self.assertEqual(m.polarity,                 'normal')
        self.assertEqual(m.port_name,                'outA')
        self.assertEqual(m.position,                 42)
        self.assertEqual(m.position_sp,              42)
        self.assertEqual(m.ramp_down_sp,             0)
        self.assertEqual(m.ramp_up_sp,               0)
        self.assertEqual(m.speed,                    0)
        self.assertEqual(m.speed_regulation_enabled, 'off')
        self.assertEqual(m.speed_sp,                 0)
        self.assertEqual(m.state,                    [])
        self.assertEqual(m.stop_command,             'coast')
        self.assertEqual(m.time_sp,                  1000)


if __name__ == "__main__":
    unittest.main()
