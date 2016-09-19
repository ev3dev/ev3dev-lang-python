#!/usr/bin/env python3

import logging
from ev3dev.GyroBalancer import GyroBalancer


class BALANC3R(GyroBalancer):
    """
    Laurens Valk's BALANC3R
    http://robotsquare.com/2014/06/23/tutorial-building-balanc3r/
    """
    def __init__(self):
        GyroBalancer.__init__(self,
                              gainGyroAngle=1156,
                              gainGyroRate=146,
                              gainMotorAngle=7,
                              gainMotorAngularSpeed=9,
                              gainMotorAngleErrorAccumulated=3)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)5s: %(message)s')
    log = logging.getLogger(__name__)

    log.info("Starting BALANC3R")
    robot = BALANC3R()
    robot.main()
    log.info("Exiting BALANC3R")
