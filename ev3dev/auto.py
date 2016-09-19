
"""
Use platform.machine() to determine the platform type, cache the
results in /tmp/current_platform so that we do not have to import
platform and run platform.machine() each time someone imports ev3dev.auto
"""
import os

filename = '/tmp/current_platform'
current_platform = None

if os.path.exists(filename):
    with open(filename, 'r') as fh:
        current_platform = fh.read().strip()

if not current_platform:
    import platform

    def get_current_platform():
        """
        Guess platform we are running on
        """
        machine = platform.machine()

        if machine == 'armv5tejl':
            return 'ev3'
        elif machine == 'armv6l':
            return 'brickpi'
        else:
            return 'unsupported'

    current_platform = get_current_platform()

    with open(filename, 'w') as fh:
        fh.write(current_platform + '\n')

if current_platform == 'brickpi':
    from .brickpi import *
else:
    # Import ev3 by default, so that it is covered by documentation.
    from .ev3 import *
