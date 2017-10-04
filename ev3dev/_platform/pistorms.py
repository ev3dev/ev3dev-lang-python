
"""
An assortment of classes modeling specific features of the PiStorms.
"""
from collections import OrderedDict

OUTPUT_A = 'pistorms:BBM1'
OUTPUT_B = 'pistorms:BBM2'
OUTPUT_C = 'pistorms:BAM2'
OUTPUT_D = 'pistorms:BAM1'

INPUT_1 = 'pistorms:BBS1'
INPUT_2 = 'pistorms:BBS2'
INPUT_3 = 'pistorms:BAS2'
INPUT_4 = 'pistorms:BAS1'


BUTTONS_FILENAME = None
EVDEV_DEVICE_NAME = None


LEDS = OrderedDict()
LEDS['red_left'] = 'pistorms:BA:red:brick-status'
LEDS['green_left'] = 'pistorms:BA:green:brick-statu'
LEDS['blue_left'] = 'pistorms:BA:blue:brick-status'
LEDS['red_right'] = 'pistorms:BB:red:brick-status'
LEDS['green_right'] = 'pistorms:BB:green:brick-statu'
LEDS['blue_right'] = 'pistorms:BB:blue:brick-status'

LED_GROUPS = OrderedDict()
LED_GROUPS['LEFT'] = ('red_left', 'green_left', 'blue_left')
LED_GROUPS['RIGHT'] = ('red_right', 'green_right', 'blue_right')

LED_COLORS = OrderedDict()
LED_COLORS['BLACK'] = (0, 0, 0)
LED_COLORS['RED'] = (1, 0, 0)
LED_COLORS['GREEN'] = (0, 1, 0)
LED_COLORS['BLUE'] = (0, 1, 1)
