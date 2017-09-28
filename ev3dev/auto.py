
import os


def get_current_platform():
    """
    Look in /sys/class/board-info/ to determine the platform type
    """
    board_info_dir = '/sys/class/board-info/'

    for board in os.listdir(board_info_dir):
        uevent_filename = os.path.join(board_info_dir, board, 'uevent')

        if os.path.exists(uevent_filename):
            with open(uevent_filename, 'r') as fh:
                for line in fh.readlines():
                    (key, value) = line.strip().split('=')

                    if key == 'BOARD_INFO_MODEL':
                        if value == 'FatcatLab EVB':
                            return 'evb'
                        elif value == 'LEGO MINDSTORMS EV3':
                            return 'ev3'
                        elif value == 'TBD':
                            return 'brickpi'
    return None


current_platform = get_current_platform()

if current_platform == 'brickpi':
    from .brickpi import *
elif current_platform == 'evb':
    from .evb import *
else:
    # Import ev3 by default, so that it is covered by documentation.
    from .ev3 import *
