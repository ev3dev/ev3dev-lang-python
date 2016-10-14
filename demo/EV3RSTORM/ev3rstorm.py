#!/usr/bin/env python3

import time, random
import ev3dev.ev3 as ev3

random.seed( time.time() )

def quote(topic):
    """
    Recite a random Marvin the Paranoid Android quote on the specified topic.
    See https://en.wikipedia.org/wiki/Marvin_(character)
    """

    marvin_quotes = {
            'initiating' : (
                "Life? Don't talk to me about life!",
                "Now I've got a headache.",
                "This will all end in tears.",
                ),
            'depressed' : (
                "I think you ought to know I'm feeling very depressed.",
                "Incredible... it's even worse than I thought it would be.",
                "I'd make a suggestion, but you wouldn't listen.",
                ),
            }

    ev3.Sound.speak(random.choice(marvin_quotes[topic])).wait()

def check(condition, message):
    """
    Check that condition is true,
    loudly complain and throw an exception otherwise.
    """
    if not condition:
        ev3.Sound.speak(message).wait()
        quote('depressed')
        raise Exception(message)

class ev3rstorm:
    def __init__(self):
        # Connect the required equipement
        self.lm = ev3.LargeMotor('outB')
        self.rm = ev3.LargeMotor('outC')
        self.mm = ev3.MediumMotor()

        self.ir = ev3.InfraredSensor()
        self.ts = ev3.TouchSensor()
        self.cs = ev3.ColorSensor()

        self.screen = ev3.Screen()

        # Check if everything is attached
        check(self.lm.connected, 'My left leg is missing!')
        check(self.rm.connected, 'Right leg is not found!')
        check(self.mm.connected, 'My left arm is not connected!')

        check(self.ir.connected, 'My eyes, I can not see!')
        check(self.ts.connected, 'Touch sensor is not attached!')
        check(self.cs.connected, 'Color sensor is not responding!')

        # Reset the motors
        for m in (self.lm, self.rm, self.mm):
            m.reset()
            m.position = 0
            m.stop_action = 'brake'

        self.draw_face()

        quote('initiating')

    def draw_face(self):
        w,h = self.screen.shape
        y = h // 2

        eye_xrad = 20
        eye_yrad = 30

        pup_xrad = 10
        pup_yrad = 10

        def draw_eye(x):
            self.screen.draw.ellipse((x-eye_xrad, y-eye_yrad, x+eye_xrad, y+eye_yrad))
            self.screen.draw.ellipse((x-pup_xrad, y-pup_yrad, x+pup_xrad, y+pup_yrad), fill='black')

        draw_eye(w//3)
        draw_eye(2*w//3)

        self.screen.update()

    def shoot(self, direction='up'):
        """
        Shot a ball in the specified direction (valid choices are 'up' and 'down')
        """
        self.mm.run_to_rel_pos(speed_sp=900, position_sp=(-1080 if direction == 'up' else 1080))
        while 'running' in self.mm.state:
            time.sleep(0.1)

    def rc_loop(self):
        """
        Enter the remote control loop. RC buttons on channel 1 control the
        robot movement, channel 2 is for shooting things.
        The loop ends when the touch sensor is pressed.
        """

        def roll(motor, led_group, speed):
            """
            Generate remote control event handler. It rolls given motor into
            given direction (1 for forward, -1 for backward). When motor rolls
            forward, the given led group flashes green, when backward -- red.
            When motor stops, the leds are turned off.

            The on_press function has signature required by RemoteControl
            class.  It takes boolean state parameter; True when button is
            pressed, False otherwise.
            """
            def on_press(state):
                if state:
                    # Roll when button is pressed
                    motor.run_forever(speed_sp=speed)
                    ev3.Leds.set_color(led_group,
                            ev3.Leds.GREEN if speed > 0 else ev3.Leds.RED)
                else:
                    # Stop otherwise
                    motor.stop()
                    ev3.Leds.set_color(led_group, ev3.Leds.BLACK)

            return on_press

        rc1 = ev3.RemoteControl(self.ir, 1)
        rc1.on_red_up    = roll(self.lm, ev3.Leds.LEFT,   900)
        rc1.on_red_down  = roll(self.lm, ev3.Leds.LEFT,  -900)
        rc1.on_blue_up   = roll(self.rm, ev3.Leds.RIGHT,  900)
        rc1.on_blue_down = roll(self.rm, ev3.Leds.RIGHT, -900)


        def shoot(direction):
            def on_press(state):
                if state: self.shoot(direction)
            return on_press

        rc2 = ev3.RemoteControl(self.ir, 2)
        rc2.on_red_up    = shoot('up')
        rc2.on_blue_up   = shoot('up')
        rc2.on_red_down  = shoot('down')
        rc2.on_blue_down = shoot('down')

        # Now that the event handlers are assigned,
        # lets enter the processing loop:
        while not self.ts.is_pressed:
            rc1.process()
            rc2.process()
            time.sleep(0.1)


if __name__ == '__main__':
    Marvin = ev3rstorm()
    Marvin.rc_loop()
