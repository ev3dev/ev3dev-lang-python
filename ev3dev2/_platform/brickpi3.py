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

INPUT_5 = 'spi0.1:S5'
INPUT_6 = 'spi0.1:S6'
INPUT_7 = 'spi0.1:S7'
INPUT_8 = 'spi0.1:S8'

INPUT_9 = 'spi0.1:S9'
INPUT_10 = 'spi0.1:S10'
INPUT_11 = 'spi0.1:S11'
INPUT_12 = 'spi0.1:S12'

INPUT_13 = 'spi0.1:S13'
INPUT_14 = 'spi0.1:S14'
INPUT_15 = 'spi0.1:S15'
INPUT_16 = 'spi0.1:S16'

BUTTONS_FILENAME = None
EVDEV_DEVICE_NAME = None

LEDS = OrderedDict()
LEDS['amber_led'] = 'led1:amber:brick-status'

LED_GROUPS = OrderedDict()
LED_GROUPS['LED'] = ('amber_led', )

LED_COLORS = OrderedDict()
LED_COLORS['BLACK'] = (0, )
LED_COLORS['AMBER'] = (1, )

LED_DEFAULT_COLOR = 'AMBER'
