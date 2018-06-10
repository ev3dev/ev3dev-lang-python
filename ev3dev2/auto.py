from ev3dev2 import *

platform = get_current_platform()

if platform == 'ev3':
    from ev3dev2._platform.ev3 import INPUT_1, INPUT_2, INPUT_3, INPUT_4
    from ev3dev2._platform.ev3 import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
    from ev3dev2._platform.ev3 import LEDS, LED_GROUPS, LED_COLORS

elif platform == 'evb':
    from ev3dev2._platform.evb import INPUT_1, INPUT_2, INPUT_3, INPUT_4
    from ev3dev2._platform.evb import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
    from ev3dev2._platform.evb import LEDS, LED_GROUPS, LED_COLORS

elif platform == 'pistorms':
    from ev3dev2._platform.pistorms import INPUT_1, INPUT_2, INPUT_3, INPUT_4
    from ev3dev2._platform.pistorms import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
    from ev3dev2._platform.pistorms import LEDS, LED_GROUPS, LED_COLORS

elif platform == 'brickpi':
    from ev3dev2._platform.brickpi import INPUT_1, INPUT_2, INPUT_3, INPUT_4
    from ev3dev2._platform.brickpi import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
    from ev3dev2._platform.brickpi import LEDS, LED_GROUPS, LED_COLORS

elif platform == 'brickpi3':
    from ev3dev2._platform.brickpi3 import INPUT_1, INPUT_2, INPUT_3, INPUT_4
    from ev3dev2._platform.brickpi3 import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
    from ev3dev2._platform.brickpi3 import LEDS, LED_GROUPS, LED_COLORS

elif platform == 'fake':
    from ev3dev2._platform.fake import INPUT_1, INPUT_2, INPUT_3, INPUT_4
    from ev3dev2._platform.fake import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
    from ev3dev2._platform.fake import LEDS, LED_GROUPS, LED_COLORS

else:
    raise Exception("Unsupported platform '%s'" % platform)

from ev3dev2.button import *
from ev3dev2.display import *
from ev3dev2.fonts import *
from ev3dev2.led import *
from ev3dev2.motor import *
from ev3dev2.port import *
from ev3dev2.power import *
from ev3dev2.sensor import *
from ev3dev2.sensor.lego import *
from ev3dev2.sound import *
