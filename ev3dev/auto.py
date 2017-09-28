
from ev3dev.core import get_current_platform

current_platform = get_current_platform()

if current_platform == 'brickpi':
    from .brickpi import *

elif current_platform == 'evb':
    from .evb import *

elif current_platform == 'pistorms':
    from .pistorms import *

else:
    # Import ev3 by default, so that it is covered by documentation.
    from .ev3 import *
