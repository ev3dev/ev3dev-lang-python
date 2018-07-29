
"""
An assortment of classes modeling specific features of the PiStorms.
"""
from collections import OrderedDict

OUTPUT_A = 'pistorms:BAM1'
OUTPUT_B = 'pistorms:BAM2'
OUTPUT_C = 'pistorms:BBM1'
OUTPUT_D = 'pistorms:BBM2'

INPUT_1 = 'pistorms:BAS1'
INPUT_2 = 'pistorms:BAS2'
INPUT_3 = 'pistorms:BBS1'
INPUT_4 = 'pistorms:BBS2'


BUTTONS_FILENAME = '/dev/input/by-path/platform-3f804000.i2c-event'
EVDEV_DEVICE_NAME = 'PiStorms'


LEDS = OrderedDict()
LEDS['red_left'] = 'pistorms:BB:red:brick-status'
LEDS['red_right'] = 'pistorms:BA:red:brick-status'
LEDS['green_left'] = 'pistorms:BB:green:brick-status'
LEDS['green_right'] = 'pistorms:BA:green:brick-status'
LEDS['blue_left'] = 'pistorms:BB:blue:brick-status'
LEDS['blue_right'] = 'pistorms:BA:blue:brick-status'

LED_GROUPS = OrderedDict()
LED_GROUPS['LEFT'] = ('red_left', 'green_left', 'blue_left')
LED_GROUPS['RIGHT'] = ('red_right', 'green_right', 'blue_right')

LED_COLORS = OrderedDict()
LED_COLORS['BLACK'] = (0, 0, 0)
LED_COLORS['RED'] = (1, 0, 0)
LED_COLORS['GREEN'] = (0, 1, 0)
LED_COLORS['BLUE'] = (0, 0, 1)
LED_COLORS['YELLOW'] = (1, 1, 0) 
LED_COLORS['CYAN'] = (0, 1, 1) 
LED_COLORS['MAGENTA'] = (1, 0, 1) 