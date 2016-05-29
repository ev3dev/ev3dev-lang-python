import platform

# -----------------------------------------------------------------------------
# Guess platform we are running on
def current_platform():
    machine = platform.machine()
    if machine == 'armv5tejl':
        return 'ev3'
    elif machine == 'armv6l':
        return 'brickpi'
    elif machine == 'armv7l':
        return 'pistorms'
    else:
        return 'unsupported'

platform = current_platform()

if platform == 'brickpi':
    from .brickpi import *
elif platform == 'pistorms':
    from .pistorms import *
else:
    # Import ev3 by default, so that it is covered by documentation.
    from .ev3 import *
