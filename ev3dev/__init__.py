import platform

# -----------------------------------------------------------------------------
# Guess platform we are running on
def current_platform():
    machine = platform.machine()
    if machine == 'armv5tejl':
        return 'ev3'
    elif machine == 'armv6l':
        return 'brickpi'
    else:
        return 'unsupported'

if current_platform() == 'brickpi':
    from .brickpi import *
else:
    # Import ev3 by default, so that it is covered by documentation.
    from .ev3 import *
