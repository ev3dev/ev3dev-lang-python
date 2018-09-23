#!/usr/bin/env python3
import unittest, sys, os.path

FAKE_SYS = os.path.join(os.path.dirname(__file__), 'fake-sys')

sys.path.append(FAKE_SYS)
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from populate_arena import populate_arena
from clean_arena    import clean_arena

import ev3dev2
from ev3dev2.sensor.lego import InfraredSensor
from ev3dev2.motor import \
    Motor, MediumMotor, LargeMotor, \
    MoveTank, MoveSteering, MoveJoystick, \
    SpeedPercent, SpeedDPM, SpeedDPS, SpeedRPM, SpeedRPS, SpeedNativeUnits, \
    OUTPUT_A, OUTPUT_B

ev3dev2.Device.DEVICE_ROOT_PATH = os.path.join(FAKE_SYS, 'arena')

_internal_set_attribute = ev3dev2.Device._set_attribute
def _set_attribute(self, attribute, name, value):
    # Follow the text with a newline to separate new content from stuff that
    # already existed in the buffer. On the real device we're writing to sysfs
    # attributes where there isn't any persistent buffer, but in the test
    # environment they're normal files on disk which retain previous data.
    attribute = _internal_set_attribute(self, attribute, name, value)
    attribute.write(b'\n')
    return attribute
ev3dev2.Device._set_attribute = _set_attribute

_internal_get_attribute = ev3dev2.Device._get_attribute
def _get_attribute(self, attribute, name):
    # Split on newline delimiter; see _set_attribute above
    attribute, value = _internal_get_attribute(self, attribute, name)
    return attribute, value.split('\n', 1)[0]
ev3dev2.Device._get_attribute = _get_attribute

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

        with self.assertRaises(ev3dev2.DeviceNotFound):
            d = ev3dev2.Device('tacho-motor', 'motor*', address='this-does-not-exist')

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
        self.assertEqual(s.mode,            "IR-PROX")

        s.mode = "IR-REMOTE"
        self.assertEqual(s.mode,            "IR-REMOTE")

        val = s.proximity
        self.assertEqual(s.mode, "IR-PROX")
        self.assertEqual(val,               16)

        val = s.buttons_pressed()
        self.assertEqual(s.mode, "IR-REMOTE")
        self.assertEqual(val,               [])

    def test_medium_motor_write(self):
        clean_arena()
        populate_arena([('medium_motor', 0, 'outA')])

        m = MediumMotor()

        self.assertEqual(m.speed_sp, 0)
        m.speed_sp = 500
        self.assertEqual(m.speed_sp, 500)

    def test_motor_on_for_degrees(self):
        clean_arena()
        populate_arena([('large_motor', 0, 'outA')])

        m = LargeMotor()

        # simple case
        m.on_for_degrees(75, 100)
        self.assertEqual(m.speed_sp, int(round(0.75 * 1050)))
        self.assertEqual(m.position_sp, 100)
    
        # various negative cases; values act like multiplication
        m.on_for_degrees(-75, 100)
        self.assertEqual(m.speed_sp, int(round(0.75 * 1050)))
        self.assertEqual(m.position_sp, -100)
        
        m.on_for_degrees(75, -100)
        self.assertEqual(m.speed_sp, int(round(0.75 * 1050)))
        self.assertEqual(m.position_sp, -100)
        
        m.on_for_degrees(-75, -100)
        self.assertEqual(m.speed_sp, int(round(0.75 * 1050)))
        self.assertEqual(m.position_sp, 100)

        # zero speed (on-device, this will return immediately due to reported stall)
        m.on_for_degrees(0, 100)
        self.assertEqual(m.speed_sp, 0)
        self.assertEqual(m.position_sp, 100)
        
        # zero distance
        m.on_for_degrees(75, 0)
        self.assertEqual(m.speed_sp, int(round(0.75 * 1050)))
        self.assertEqual(m.position_sp, 0)

        # zero speed and distance
        m.on_for_degrees(0, 0)
        self.assertEqual(m.speed_sp, 0)
        self.assertEqual(m.position_sp, 0)

        # None speed
        with self.assertRaises(ValueError):
            m.on_for_degrees(None, 100)
        
        # None distance
        with self.assertRaises(ValueError):
            m.on_for_degrees(75, None)
    
    def test_motor_on_for_rotations(self):
        clean_arena()
        populate_arena([('large_motor', 0, 'outA')])

        m = LargeMotor()

        # simple case
        m.on_for_rotations(75, 5)
        self.assertEqual(m.speed_sp, int(round(0.75 * 1050)))
        self.assertEqual(m.position_sp, 5 * 360)

        # None speed
        with self.assertRaises(ValueError):
            m.on_for_rotations(None, 5)
        
        # None distance
        with self.assertRaises(ValueError):
            m.on_for_rotations(75, None)

    def test_move_tank_relative_distance(self):
        clean_arena()
        populate_arena([('large_motor', 0, 'outA'), ('large_motor', 1, 'outB')])

        drive = MoveTank(OUTPUT_A, OUTPUT_B)

        # simple case (degrees)
        drive.on_for_degrees(50, 25, 100)
        self.assertEqual(drive.left_motor.position_sp, 100)
        self.assertEqual(drive.left_motor.speed_sp, 0.50 * 1050)
        self.assertEqual(drive.right_motor.position_sp, 50)
        self.assertAlmostEqual(drive.right_motor.speed_sp, 0.25 * 1050, delta=0.5)
        
        # simple case (rotations, based on degrees)
        drive.on_for_rotations(50, 25, 10)
        self.assertEqual(drive.left_motor.position_sp, 10 * 360)
        self.assertEqual(drive.left_motor.speed_sp, 0.50 * 1050)
        self.assertEqual(drive.right_motor.position_sp, 5 * 360)
        self.assertAlmostEqual(drive.right_motor.speed_sp, 0.25 * 1050, delta=0.5)

        # negative distance
        drive.on_for_rotations(50, 25, -10)
        self.assertEqual(drive.left_motor.position_sp, -10 * 360)
        self.assertEqual(drive.left_motor.speed_sp, 0.50 * 1050)
        self.assertEqual(drive.right_motor.position_sp, -5 * 360)
        self.assertAlmostEqual(drive.right_motor.speed_sp, 0.25 * 1050, delta=0.5)

        # negative speed
        drive.on_for_rotations(-50, 25, 10)
        self.assertEqual(drive.left_motor.position_sp, -10 * 360)
        self.assertEqual(drive.left_motor.speed_sp, 0.50 * 1050)
        self.assertEqual(drive.right_motor.position_sp, 5 * 360)
        self.assertAlmostEqual(drive.right_motor.speed_sp, 0.25 * 1050, delta=0.5)

        # negative distance and speed
        drive.on_for_rotations(-50, 25, -10)
        self.assertEqual(drive.left_motor.position_sp, 10 * 360)
        self.assertEqual(drive.left_motor.speed_sp, 0.50 * 1050)
        self.assertEqual(drive.right_motor.position_sp, -5 * 360)
        self.assertAlmostEqual(drive.right_motor.speed_sp, 0.25 * 1050, delta=0.5)

        # both speeds zero but nonzero distance
        drive.on_for_rotations(0, 0, 10)
        self.assertEqual(drive.left_motor.position_sp, 10 * 360)
        self.assertAlmostEqual(drive.left_motor.speed_sp, 0)
        self.assertEqual(drive.right_motor.position_sp, 10 * 360)
        self.assertAlmostEqual(drive.right_motor.speed_sp, 0)
        
        # zero distance
        drive.on_for_rotations(25, 50, 0)
        self.assertEqual(drive.left_motor.position_sp, 0)
        self.assertAlmostEqual(drive.left_motor.speed_sp, 0.25 * 1050, delta=0.5)
        self.assertEqual(drive.right_motor.position_sp, 0)
        self.assertAlmostEqual(drive.right_motor.speed_sp, 0.50 * 1050)

        # zero distance and zero speed
        drive.on_for_rotations(0, 0, 0)
        self.assertEqual(drive.left_motor.position_sp, 0)
        self.assertAlmostEqual(drive.left_motor.speed_sp, 0)
        self.assertEqual(drive.right_motor.position_sp, 0)
        self.assertAlmostEqual(drive.right_motor.speed_sp, 0)
    
    def test_tank_units(self):
        clean_arena()
        populate_arena([('large_motor', 0, 'outA'), ('large_motor', 1, 'outB')])

        drive = MoveTank(OUTPUT_A, OUTPUT_B)
        drive.on_for_rotations(SpeedDPS(400), SpeedDPM(10000), 10)

        self.assertEqual(drive.left_motor.position, 0)
        self.assertEqual(drive.left_motor.position_sp, 10 * 360)
        self.assertEqual(drive.left_motor.speed_sp, 400)

        self.assertEqual(drive.right_motor.position, 0)
        self.assertAlmostEqual(drive.right_motor.position_sp, 10 * 360 * ((10000 / 60) / 400))
        self.assertAlmostEqual(drive.right_motor.speed_sp, 10000 / 60, delta=0.5)

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
    
    def test_steering_large_value(self):
        clean_arena()
        populate_arena([('large_motor', 0, 'outA'), ('large_motor', 1, 'outB')])

        drive = MoveSteering(OUTPUT_A, OUTPUT_B)
        drive.on_for_rotations(-100, SpeedDPS(400), 10)

        self.assertEqual(drive.left_motor.position, 0)
        self.assertEqual(drive.left_motor.position_sp, -10 * 360)
        self.assertEqual(drive.left_motor.speed_sp, 400)

        self.assertEqual(drive.right_motor.position, 0)
        self.assertEqual(drive.right_motor.position_sp, 10 * 360)
        self.assertEqual(drive.right_motor.speed_sp, 400)

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

        self.assertEqual(SpeedPercent(35).to_native_units(m), 35 / 100 * m.max_speed)
        self.assertEqual(SpeedDPS(300).to_native_units(m), 300)
        self.assertEqual(SpeedNativeUnits(300).to_native_units(m), 300)
        self.assertEqual(SpeedDPM(30000).to_native_units(m), (30000 / 60))
        self.assertEqual(SpeedRPS(2).to_native_units(m), 360 * 2)
        self.assertEqual(SpeedRPM(100).to_native_units(m), (360 * 100 / 60))

if __name__ == "__main__":
    unittest.main()
