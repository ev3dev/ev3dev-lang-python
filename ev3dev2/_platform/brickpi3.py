from collections import OrderedDict

# Up to four brickpi3s can be stacked
OUTPUT_A = 'spi0.1:MA'
OUTPUT_B = 'spi0.1:MB'
OUTPUT_C = 'spi0.1:MC'
OUTPUT_D = 'spi0.1:MD'

OUTPUT_E = 'spi0.1:ME'
OUTPUT_F = 'spi0.1:MF'
OUTPUT_G = 'spi0.1:MG'
OUTPUT_H = 'spi0.1:MH'

OUTPUT_I = 'spi0.1:MI'
OUTPUT_J = 'spi0.1:MJ'
OUTPUT_K = 'spi0.1:MK'
OUTPUT_L = 'spi0.1:ML'

OUTPUT_M = 'spi0.1:MM'
OUTPUT_N = 'spi0.1:MN'
OUTPUT_O = 'spi0.1:MO'
OUTPUT_P = 'spi0.1:MP'

INPUT_1 = 'spi0.1:S1' 
INPUT_2 = 'spi0.1:S2' 
INPUT_3 = 'spi0.1:S3' 
INPUT_4 = 'spi0.1:S4'

BUTTONS_FILENAME = None
EVDEV_DEVICE_NAME = None

LEDS = OrderedDict()
LEDS['blue_led'] = 'led0:blue:brick-status'

LED_GROUPS = OrderedDict()
LED_GROUPS['LED'] = ('blue_led',)

LED_COLORS = OrderedDict()
LED_COLORS['BLACK'] = (0,)
LED_COLORS['BLUE'] = (1,)
