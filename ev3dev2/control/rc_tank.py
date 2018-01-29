
import logging
from ev3dev2.motor import MoveTank
from ev3dev2.sensor.lego import InfraredSensor
from time import sleep

log = logging.getLogger(__name__)

# ============
# Tank classes
# ============
class RemoteControlledTank(MoveTank):

    def __init__(self, left_motor_port, right_motor_port, polarity='inversed', speed=400, channel=1):
        MoveTank.__init__(self, left_motor_port, right_motor_port)
        self.set_polarity(polarity)

        left_motor = self.motors[left_motor_port]
        right_motor = self.motors[right_motor_port]
        self.speed_sp = speed
        self.remote = InfraredSensor()
        self.remote.on_channel1_top_left = self.make_move(left_motor, self.speed_sp)
        self.remote.on_channel1_bottom_left = self.make_move(left_motor, self.speed_sp* -1)
        self.remote.on_channel1_top_right = self.make_move(right_motor, self.speed_sp)
        self.remote.on_channel1_bottom_right = self.make_move(right_motor, self.speed_sp * -1)
        self.channel = channel

    def make_move(self, motor, dc_sp):
        def move(state):
            if state:
                motor.run_forever(speed_sp=dc_sp)
            else:
                motor.stop()
        return move

    def main(self):

        try:
            while True:
                self.remote.process()
                sleep(0.01)

        # Exit cleanly so that all motors are stopped
        except (KeyboardInterrupt, Exception) as e:
            log.exception(e)
            self.stop()
