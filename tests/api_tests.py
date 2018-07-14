#!/usr/bin/env python3
import unittest, sys, os

FAKE_SYS = os.path.join(os.path.dirname(__file__), 'fake-sys')

sys.path.append(FAKE_SYS)
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from populate_arena import populate_arena
from clean_arena    import clean_arena

import ev3dev2
from ev3dev2.sensor.lego import InfraredSensor
from ev3dev2.motor import Motor, MediumMotor, MoveTank, MoveSteering, MoveJoystick, SpeedPercent, SpeedDPM, SpeedDPS, SpeedRPM, SpeedRPS, SpeedNativeUnits, OUTPUT_A, OUTPUT_B

ev3dev2.Device.DEVICE_ROOT_PATH = os.path.join(FAKE_SYS, 'arena')

def dummy_wait(self, cond, timeout=None):
    pass

Motor.wait = dummy_wait

class TestAPI(unittest.TestCase):
    def test_device(self):
        clean_arena()
        populate_arena([('medium_motor', 0, 'outA'), ('infrared_sensor', 0, 'in1')])

        d = ev3dev2.Device('tacho-motor', 'motor*')

        d = ev3dev2.Device('tacho-motor', 'motor0')

        d = ev3dev2.Device('tacho-motor', 'motor*', driver_name='lego-ev3-m-motor')

        d = ev3dev2.Device('tacho-motor', 'motor*', address='outA')

        with self.assertRaises(ev3dev2.DeviceNotFound):
            d = ev3dev2.Device('tacho-motor', 'motor*', address='outA', driver_name='not-valid')

        d = ev3dev2.Device('lego-sensor', 'sensor*')

        with self.assertRaises(ev3dev2.DeviceNotFound):
            d = ev3dev2.Device('this-does-not-exist')

    def test_medium_motor(self):
        def dummy(self):
            pass

        clean_arena()
        populate_arena([('medium_motor', 0, 'outA')])

        # Do not write motor.command on exit (so that fake tree stays intact)
        MediumMotor.__del__ = dummy

        m = MediumMotor()

        self.assertEqual(m.device_index, 0)

        # Check that reading twice works:
        self.assertEqual(m.driver_name, 'lego-ev3-m-motor')
        self.assertEqual(m.driver_name, 'lego-ev3-m-motor')

        self.assertEqual(m.count_per_rot,            360)
        self.assertEqual(m.commands,                 ['run-forever', 'run-to-abs-pos', 'run-to-rel-pos', 'run-timed', 'run-direct', 'stop', 'reset'])
        self.assertEqual(m.duty_cycle,               0)
        self.assertEqual(m.duty_cycle_sp,            42)
        self.assertEqual(m.polarity,                 'normal')
        self.assertEqual(m.address,                  'outA')
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
        populate_arena([('infrared_sensor', 0, 'in1')])

        s = InfraredSensor()

        self.assertEqual(s.device_index,    0)
        self.assertEqual(s.bin_data_format, 's8')
        self.assertEqual(s.bin_data('<b'),  (16,))
        self.assertEqual(s.num_values,      1)
        self.assertEqual(s.address,         'in1')
        self.assertEqual(s.value(0),        16)

    def test_medium_motor_write(self):
        clean_arena()
        populate_arena([('medium_motor', 0, 'outA')])

        m = MediumMotor()

        self.assertEqual(m.speed_sp, 0)
        m.speed_sp = 500
        self.assertEqual(m.speed_sp, 500)

    def test_move_tank(self):
        clean_arena()
        populate_arena([('large_motor', 0, 'outA'), ('large_motor', 1, 'outB')])

        drive = MoveTank(OUTPUT_A, OUTPUT_B)
        drive.on_for_rotations(50, 25, 10)

        self.assertEqual(drive.left_motor.position, 0)
        self.assertEqual(drive.left_motor.position_sp, 10 * 360)
        self.assertEqual(drive.left_motor.speed_sp, 1050 / 2)

        self.assertEqual(drive.right_motor.position, 0)
        self.assertAlmostEqual(drive.right_motor.position_sp, 5 * 360, delta=5)
        self.assertAlmostEqual(drive.right_motor.speed_sp, 1050 / 4, delta=1)
    
    def test_tank_units(self):
        clean_arena()
        populate_arena([('large_motor', 0, 'outA'), ('large_motor', 1, 'outB')])

        drive = MoveTank(OUTPUT_A, OUTPUT_B)
        drive.on_for_rotations(SpeedDPS(400), SpeedDPM(10000), 10)

        self.assertEqual(drive.left_motor.position, 0)
        self.assertEqual(drive.left_motor.position_sp, 10 * 360)
        self.assertEqual(drive.left_motor.speed_sp, 400)

        self.assertEqual(drive.right_motor.position, 0)
        self.assertAlmostEqual(drive.right_motor.position_sp, 10 * 360 * ((10000 / 60) / 400), delta=7)
        self.assertAlmostEqual(drive.right_motor.speed_sp, 10000 / 60, delta=1)

    def test_steering_units(self):
        clean_arena()
        populate_arena([('large_motor', 0, 'outA'), ('large_motor', 1, 'outB')])

        drive = MoveSteering(OUTPUT_A, OUTPUT_B)
        drive.on_for_rotations(25, SpeedDPS(400), 10)

        self.assertEqual(drive.left_motor.position, 0)
        self.assertEqual(drive.left_motor.position_sp, 10 * 360)
        self.assertEqual(drive.left_motor.speed_sp, 400)

        self.assertEqual(drive.right_motor.position, 0)
        self.assertEqual(drive.right_motor.position_sp, 5 * 360)
        self.assertEqual(drive.right_motor.speed_sp, 200)

    def test_joystick_units(self):
        clean_arena()
        populate_arena([('large_motor', 0, 'outA'), ('large_motor', 1, 'outB')])

        drive = MoveJoystick(OUTPUT_A, OUTPUT_B)
        drive.on(100, 100, max_speed=SpeedPercent(50))

        self.assertEqual(drive.left_motor.speed_sp, 1050 / 2)
        self.assertAlmostEqual(drive.right_motor.speed_sp, 0)

    def test_units(self):
        clean_arena()
        populate_arena([('large_motor', 0, 'outA'), ('large_motor', 1, 'outB')])

        m = Motor()

        self.assertEqual(SpeedPercent(35).get_speed_pct(m), 35)
        self.assertEqual(SpeedDPS(300).get_speed_pct(m), 300 / 1050 * 100)
        self.assertEqual(SpeedNativeUnits(300).get_speed_pct(m), 300 / 1050 * 100)
        self.assertEqual(SpeedDPM(30000).get_speed_pct(m), (30000 / 60) / 1050 * 100)
        self.assertEqual(SpeedRPS(2).get_speed_pct(m), 360 * 2 / 1050 * 100)
        self.assertEqual(SpeedRPM(100).get_speed_pct(m), (360 * 100 / 60) / 1050 * 100)


if __name__ == "__main__":
    unittest.main()
