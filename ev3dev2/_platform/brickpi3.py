from collections import OrderedDict

OUTPUT_A = 'spi0.1:MA'
OUTPUT_B = 'spi0.1:MB'
OUTPUT_C = 'spi0.1:MC'
OUTPUT_D = 'spi0.1:MD'

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
