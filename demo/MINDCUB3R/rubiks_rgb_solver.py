#!/usr/bin/env python3

from itertools import permutations
from math import atan2, cos, degrees, exp, factorial, radians, sin, sqrt
from kociemba.pykociemba.verify import verify as verify_parity
import argparse
import json
import logging
import sys

log = logging.getLogger(__name__)

# Calculating color distances is expensive in terms of CPU so
# cache the results
dcache = {}


class LabColor(object):

    def __init__(self, L, a, b):
        self.L = L
        self.a = a
        self.b = b
        self.name = None

    def __str__(self):
        return ("Lab (%s, %s, %s)" % (self.L, self.a, self.b))

    def __lt__(self, other):
        return delta_e_cie2000(self, other)


def rgb2lab(inputColor):
    """
    http://stackoverflow.com/questions/13405956/convert-an-image-rgb-lab-with-python
    """
    RGB = [0, 0, 0]
    XYZ = [0, 0, 0]

    for (num, value) in enumerate(inputColor):
        if value > 0.04045:
            value = pow(((value + 0.055) / 1.055), 2.4)
        else:
            value = value / 12.92

        RGB[num] = value * 100.0

    # http://www.brucelindbloom.com/index.html?Eqn_RGB_XYZ_Matrix.html
    # 0.4124564  0.3575761  0.1804375
    # 0.2126729  0.7151522  0.0721750
    # 0.0193339  0.1191920  0.9503041
    X = (RGB[0] * 0.4124564) + (RGB[1] * 0.3575761) + (RGB[2] * 0.1804375)
    Y = (RGB[0] * 0.2126729) + (RGB[1] * 0.7151522) + (RGB[2] * 0.0721750)
    Z = (RGB[0] * 0.0193339) + (RGB[1] * 0.1191920) + (RGB[2] * 0.9503041)

    XYZ[0] = X / 95.047   # ref_X =  95.047
    XYZ[1] = Y / 100.0    # ref_Y = 100.000
    XYZ[2] = Z / 108.883  # ref_Z = 108.883

    for (num, value) in enumerate(XYZ):
        if value > 0.008856:
            value = pow(value, (1.0 / 3.0))
        else:
            value = (7.787 * value) + (16 / 116.0)

        XYZ[num] = value

    L = (116.0 * XYZ[1]) - 16
    a = 500.0 * (XYZ[0] - XYZ[1])
    b = 200.0 * (XYZ[1] - XYZ[2])

    L = round(L, 4)
    a = round(a, 4)
    b = round(b, 4)

    return LabColor(L, a, b)


def delta_e_cie2000(lab1, lab2):
    """
    Ported from this php implementation
    https://github.com/renasboy/php-color-difference/blob/master/lib/color_difference.class.php
    """
    l1 = lab1.L
    a1 = lab1.a
    b1 = lab1.b

    l2 = lab2.L
    a2 = lab2.a
    b2 = lab2.b

    avg_lp = (l1 + l2) / 2.0
    c1 = sqrt(pow(a1, 2) + pow(b1, 2))
    c2 = sqrt(pow(a2, 2) + pow(b2, 2))
    avg_c = (c1 + c2) / 2.0
    g = (1 - sqrt(pow(avg_c, 7) / (pow(avg_c, 7) + pow(25, 7)))) / 2.0
    a1p = a1 * (1 + g)
    a2p = a2 * (1 + g)
    c1p = sqrt(pow(a1p, 2) + pow(b1, 2))
    c2p = sqrt(pow(a2p, 2) + pow(b2, 2))
    avg_cp = (c1p + c2p) / 2.0
    h1p = degrees(atan2(b1, a1p))

    if h1p < 0:
        h1p += 360

    h2p = degrees(atan2(b2, a2p))

    if h2p < 0:
        h2p += 360

    if abs(h1p - h2p) > 180:
        avg_hp = (h1p + h2p + 360) / 2.0
    else:
        avg_hp = (h1p + h2p) / 2.0

    t = (1 - 0.17 * cos(radians(avg_hp - 30)) +
         0.24 * cos(radians(2 * avg_hp)) +
         0.32 * cos(radians(3 * avg_hp + 6)) - 0.2 * cos(radians(4 * avg_hp - 63)))
    delta_hp = h2p - h1p

    if abs(delta_hp) > 180:
        if h2p <= h1p:
            delta_hp += 360
        else:
            delta_hp -= 360

    delta_lp = l2 - l1
    delta_cp = c2p - c1p
    delta_hp = 2 * sqrt(c1p * c2p) * sin(radians(delta_hp) / 2.0)
    s_l = 1 + ((0.015 * pow(avg_lp - 50, 2)) / sqrt(20 + pow(avg_lp - 50, 2)))
    s_c = 1 + 0.045 * avg_cp
    s_h = 1 + 0.015 * avg_cp * t

    delta_ro = 30 * exp(-(pow((avg_hp - 275) / 25.0, 2)))
    r_c = 2 * sqrt(pow(avg_cp, 7) / (pow(avg_cp, 7) + pow(25, 7)))
    r_t = -r_c * sin(2 * radians(delta_ro))
    kl = 1.0
    kc = 1.0
    kh = 1.0
    delta_e = sqrt(pow(delta_lp / (s_l * kl), 2) +
                   pow(delta_cp / (s_c * kc), 2) +
                   pow(delta_hp / (s_h * kh), 2) +
                   r_t * (delta_cp / (s_c * kc)) * (delta_hp / (s_h * kh)))
    return delta_e


def get_color_distance(c1, c2):
    try:
        return dcache[(c1, c2)]
    except KeyError:
        try:
            return dcache[(c2, c1)]
        except KeyError:
            distance = delta_e_cie2000(c1, c2)
            dcache[(c1, c2)] = distance
            return distance


def hex_to_rgb(rgb_string):
    """
    Takes #112233 and returns the RGB values in decimal
    """
    if rgb_string.startswith('#'):
        rgb_string = rgb_string[1:]

    red = int(rgb_string[0:2], 16)
    green = int(rgb_string[2:4], 16)
    blue = int(rgb_string[4:6], 16)
    return (red, green, blue)


def hashtag_rgb_to_labcolor(rgb_string):
    (red, green, blue) = hex_to_rgb(rgb_string)
    return rgb2lab((red, green, blue))


class Edge(object):

    def __init__(self, cube, pos1, pos2):
        self.valid = False
        self.square1 = cube.get_square(pos1)
        self.square2 = cube.get_square(pos2)
        self.cube = cube
        self.dcache = {}

    def __str__(self):
        return "%s%d/%s%d %s/%s" %\
            (self.square1.side, self.square1.position,
             self.square2.side, self.square2.position,
             self.square1.color.name, self.square2.color.name)

    def __lt__(self, other):
        return 0

    def colors_match(self, colorA, colorB):
        if (colorA in (self.square1.color, self.square2.color) and
            colorB in (self.square1.color, self.square2.color)):
            return True
        return False

    def _get_color_distances(self, colorA, colorB):
        distanceAB = (get_color_distance(self.square1.rawcolor, colorA) +
                      get_color_distance(self.square2.rawcolor, colorB))

        distanceBA = (get_color_distance(self.square1.rawcolor, colorB) +
                      get_color_distance(self.square2.rawcolor, colorA))

        return (distanceAB, distanceBA)

    def color_distance(self, colorA, colorB):
        """
        Given two colors, return our total color distance
        """
        try:
            return self.dcache[(colorA, colorB)]
        except KeyError:
            value = min(self._get_color_distances(colorA, colorB))
            self.dcache[(colorA, colorB)] = value
            return value

    def update_colors(self, colorA, colorB):
        (distanceAB, distanceBA) = self._get_color_distances(colorA, colorB)

        if distanceAB < distanceBA:
            self.square1.color = colorA
            self.square2.color = colorB
        else:
            self.square1.color = colorB
            self.square2.color = colorA

    def validate(self):

        if self.square1.color == self.square2.color:
            self.valid = False
            log.info("%s is an invalid edge (duplicate colors)" % self)
        elif ((self.square1.color, self.square2.color) in self.cube.valid_edges or
              (self.square2.color, self.square1.color) in self.cube.valid_edges):
            self.valid = True
        else:
            self.valid = False
            log.info("%s is an invalid edge" % self)


class Corner(object):

    def __init__(self, cube, pos1, pos2, pos3):
        self.valid = False
        self.square1 = cube.get_square(pos1)
        self.square2 = cube.get_square(pos2)
        self.square3 = cube.get_square(pos3)
        self.cube = cube
        self.dcache = {}

    def __str__(self):
        return "%s%d/%s%d/%s%d %s/%s/%s" %\
            (self.square1.side, self.square1.position,
             self.square2.side, self.square2.position,
             self.square3.side, self.square3.position,
             self.square1.color.name, self.square2.color.name, self.square3.color.name)

    def colors_match(self, colorA, colorB, colorC):
        if (colorA in (self.square1.color, self.square2.color, self.square3.color) and
            colorB in (self.square1.color, self.square2.color, self.square3.color) and
            colorC in (self.square1.color, self.square2.color, self.square3.color)):
            return True
        return False

    def _get_color_distances(self, colorA, colorB, colorC):
        distanceABC = (get_color_distance(self.square1.rawcolor, colorA) +
                       get_color_distance(self.square2.rawcolor, colorB) +
                       get_color_distance(self.square3.rawcolor, colorC))

        distanceCAB = (get_color_distance(self.square1.rawcolor, colorC) +
                       get_color_distance(self.square2.rawcolor, colorA) +
                       get_color_distance(self.square3.rawcolor, colorB))

        distanceBCA = (get_color_distance(self.square1.rawcolor, colorB) +
                       get_color_distance(self.square2.rawcolor, colorC) +
                       get_color_distance(self.square3.rawcolor, colorA))
        return (distanceABC, distanceCAB, distanceBCA)

    def color_distance(self, colorA, colorB, colorC):
        """
        Given three colors, return our total color distance
        """
        try:
            return self.dcache[(colorA, colorB, colorC)]
        except KeyError:
            value = min(self._get_color_distances(colorA, colorB, colorC))
            self.dcache[(colorA, colorB, colorC)] = value
            return value

    def update_colors(self, colorA, colorB, colorC):
        (distanceABC, distanceCAB, distanceBCA) = self._get_color_distances(colorA, colorB, colorC)
        min_distance = min(distanceABC, distanceCAB, distanceBCA)

        if min_distance == distanceABC:
            self.square1.color = colorA
            self.square2.color = colorB
            self.square3.color = colorC

        elif min_distance == distanceCAB:
            self.square1.color = colorC
            self.square2.color = colorA
            self.square3.color = colorB

        elif min_distance == distanceBCA:
            self.square1.color = colorB
            self.square2.color = colorC
            self.square3.color = colorA

    def validate(self):

        if (self.square1.color == self.square2.color or
            self.square1.color == self.square3.color or
                self.square2.color == self.square3.color):
            self.valid = False
            log.info("%s is an invalid edge (duplicate colors)" % self)
        elif ((self.square1.color, self.square2.color, self.square3.color) in self.cube.valid_corners or
              (self.square1.color, self.square3.color, self.square2.color) in self.cube.valid_corners or
              (self.square2.color, self.square1.color, self.square3.color) in self.cube.valid_corners or
              (self.square2.color, self.square3.color, self.square1.color) in self.cube.valid_corners or
              (self.square3.color, self.square1.color, self.square2.color) in self.cube.valid_corners or
              (self.square3.color, self.square2.color, self.square1.color) in self.cube.valid_corners):
            self.valid = True
        else:
            self.valid = False
            log.info("%s (%s, %s, %s) is an invalid corner" %
                     (self, self.square1.color, self.square2.color, self.square3.color))


class Square(object):

    def __init__(self, side, cube, position, red, green, blue):
        self.cube = cube
        self.side = side
        self.position = position
        self.red = red
        self.green = green
        self.blue = blue
        self.rawcolor = rgb2lab((red, green, blue))
        self.color = None
        self.cie_data = []

    def __str__(self):
        return "%s%d" % (self.side, self.position)

    def find_closest_match(self, crayon_box, debug=False, set_color=True):
        self.cie_data = []

        for (color, color_obj) in crayon_box.items():
            distance = get_color_distance(self.rawcolor, color_obj)
            self.cie_data.append((distance, color_obj))
        self.cie_data = sorted(self.cie_data)

        distance = self.cie_data[0][0]
        color_obj = self.cie_data[0][1]

        if set_color:
            self.distance = distance
            self.color = color_obj

        if debug:
            log.info("%s is %s" % (self, color_obj))

        return (color_obj, distance)


class CubeSide(object):

    def __init__(self, cube, name):
        self.cube = cube
        self.name = name  # U, L, etc
        self.color = None  # Will be the color of the middle square
        self.squares = {}

        if self.name == 'U':
            index = 0
        elif self.name == 'L':
            index = 1
        elif self.name == 'F':
            index = 2
        elif self.name == 'R':
            index = 3
        elif self.name == 'B':
            index = 4
        elif self.name == 'D':
            index = 5

        self.min_pos = (index * 9) + 1
        self.max_pos = (index * 9) + 9
        self.mid_pos = (self.min_pos + self.max_pos) / 2
        self.edge_pos = (self.min_pos + 1, self.min_pos + 3, self.min_pos + 5, self.min_pos + 7)
        self.corner_pos = (self.min_pos, self.min_pos + 2, self.min_pos + 6, self.min_pos + 8)

        self.middle_square = None
        self.edge_squares = []
        self.corner_squares = []

        log.info("Side %s, min/mid/max %d/%d/%d" % (self.name, self.min_pos, self.mid_pos, self.max_pos))

    def __str__(self):
        return self.name

    def set_square(self, position, red, green, blue):
        self.squares[position] = Square(self, self.cube, position, red, green, blue)

        if position == self.mid_pos:
            self.middle_square = self.squares[position]

        elif position in self.edge_pos:
            self.edge_squares.append(self.squares[position])

        elif position in self.corner_pos:
            self.corner_squares.append(self.squares[position])


class RubiksColorSolver(object):

    """
    This class accepts a RGB value for all 54 squares on a Rubiks cube and
    figures out which of the 6 cube colors each square is.

    The names of the sides are (Up, Left, Front, Right, Back, Down)
      U
    L F R B
      D
    """

    def __init__(self):
        self.width = 3
        self.blocks_per_side = self.width * self.width
        self.colors = []
        self.scan_data = {}
        self.tools_file = None

        # 4! = 24
        # 5! = 120
        # 6! = 720
        # 7! = 5040
        # 8! = 40320

        # With a limit of 40320 it takes 3.6s to resolve the colors for a cube
        # With a limit of  5040 it takes 1.5s to resolve the colors for a cube
        # With a limit of   720 it takes 1.2s to resolve the colors for a cube
        # These numbers are from a beefy server, not EV3
        self.edge_permutation_limit = 720
        self.corner_permutation_limit = 720

        self.sides = {
            'U': CubeSide(self, 'U'),
            'L': CubeSide(self, 'L'),
            'F': CubeSide(self, 'F'),
            'R': CubeSide(self, 'R'),
            'B': CubeSide(self, 'B'),
            'D': CubeSide(self, 'D')
        }

        self.sideU = self.sides['U']
        self.sideL = self.sides['L']
        self.sideF = self.sides['F']
        self.sideR = self.sides['R']
        self.sideB = self.sides['B']
        self.sideD = self.sides['D']

        self.side_order = ('U', 'L', 'F', 'R', 'B', 'D')
        self.edges = []
        self.corners = []

        # These are the RGB values for each color as seen via the EV3 color
        # sensor. Translate these to hex for the dict below.
        #
        # white = (60, 100, 70)
        # green = (6, 35, 13)
        # yellow = (34, 43, 8)
        # orange = (40, 20, 6)
        # blue = (6, 19, 20)
        # red = (30, 12, 6)

        self.crayola_colors = {
            # The RGB values in comments are the originals used, they came
            # from crayola's website
            'Wh': hashtag_rgb_to_labcolor('#3C6446'),  # White  - FFFFFF
            'Gr': hashtag_rgb_to_labcolor('#06230D'),  # Green  - 1C8E0D
            'Ye': hashtag_rgb_to_labcolor('#222B08'),  # Yellow - F6EB20
            'OR': hashtag_rgb_to_labcolor('#281406'),  # Orange - FF80000
            'Bu': hashtag_rgb_to_labcolor('#061314'),  # Blue   - 2862B9
            'Rd': hashtag_rgb_to_labcolor('#1E0C06')   # Red    - C91111

            # These are the RGB values according to crayola
            # 'Yg': hashtag_rgb_to_labcolor('#51C201'),  # Yellow Green
            # 'Or': hashtag_rgb_to_labcolor('#D84E09'),  # Red Orange
            # 'Sy': hashtag_rgb_to_labcolor('#09C5F4'),  # Sky Blue
            # 'Pu': hashtag_rgb_to_labcolor('#7E44BC'),  # Purple
            # 'Bl': hashtag_rgb_to_labcolor('#000000')   # Black
        }

    # ================
    # Printing methods
    # ================
    def print_layout(self):
        log.info("""

           01 02 03
           04 05 06
           07 08 09
 10 11 12  19 20 21  28 29 30  37 38 39
 13 14 15  22 23 24  31 32 33  40 41 42
 16 17 18  25 26 27  34 35 36  43 44 45
           46 47 48
           49 50 51
           52 53 54

""")

    def print_cube(self):
        """
           Wh Wh Wh
           Wh Wh Wh
           Wh Wh Wh
 Rd Rd Rd  Bu Bu Bu  OR OR OR  Gr Gr Gr
 Rd Rd Rd  Bu Bu Bu  OR OR OR  Gr Gr Gr
 Rd Rd Rd  Bu Bu Bu  OR OR OR  Gr Gr Gr
           Ye Ye Ye
           Ye Ye Ye
           Ye Ye Ye
        """
        data = [[], [], [], [], [], [], [], [], []]

        color_codes = {
          'OR': 90,
          'Rd': 91,
          'Gr': 92,
          'Ye': 93,
          'Bu': 94,
          'Wh': 97
        }

        for side_name in self.side_order:
            side = self.sides[side_name]

            if side_name == 'U':
                line_number = 0
                prefix = '          '
            elif side_name in ('L', 'F', 'R', 'B'):
                line_number = 3
                prefix = ''
            else:
                line_number = 6
                prefix = '          '

            for x in range(3):
                data[line_number].append(prefix)

                for color_name in (side.squares[side.min_pos + (x * 3)].color.name,
                                   side.squares[side.min_pos + (x * 3) + 1].color.name,
                                   side.squares[side.min_pos + (x * 3) + 2].color.name):
                    color_code = color_codes.get(color_name)

                    # default to white
                    if color_code is None:
                        color_code = 97

                    data[line_number].append('\033[%dm%s\033[0m' % (color_code, color_name))
                line_number += 1

        output = []
        for row in data:
            output.append(' '.join(row))

        log.info("Cube\n\n%s\n" % '\n'.join(output))

    def cube_for_kociemba(self):
        data = []

        color_to_num = {}

        for side in self.sides.values():
            color_to_num[side.middle_square.color] = side.name

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for x in range(side.min_pos, side.max_pos + 1):
                color = side.squares[x].color
                data.append(color_to_num[color])

        return data

    def get_side(self, position):
        """
        Given a position on the cube return the CubeSide object
        that contians that position
        """
        for side in self.sides.values():
            if position >= side.min_pos and position <= side.max_pos:
                return side
        raise Exception("Could not find side for %d" % position)

    def get_square(self, position):
        side = self.get_side(position)
        return side.squares[position]

    def enter_scan_data(self, scan_data):
        self.scan_data = scan_data

        for (position, (red, green, blue)) in self.scan_data.items():
            side = self.get_side(position)
            side.set_square(position, red, green, blue)

    def get_squares_with_color(self, target_color):
        squares = []
        for side in self.sides.values():
            for square in side.squares.values():
                if square.color == target_color:
                    squares.append(square)
        return squares

    def name_middle_square_colors(self):
        """
        Assign a color name to the square's LabColor object.
        This name is only used for debug output.
        """
        self.crayon_box = {}

        min_distance = None
        min_distance_permuation = None

        for permutation in permutations(self.crayola_colors.keys()):
            distance = 0

            for (side_name, color_name) in zip(self.side_order, permutation):
                side = self.sides[side_name]
                color_obj = self.crayola_colors[color_name]
                distance += get_color_distance(side.middle_square.rawcolor, color_obj)

            if min_distance is None or distance < min_distance:
                min_distance = distance
                min_distance_permutation = permutation

        log.info("Crayon box (middle square colors)")
        for (side_name, color_name) in zip(self.side_order, min_distance_permutation):
            side = self.sides[side_name]
            self.crayon_box[side.name] = side.middle_square.rawcolor
            side.middle_square.rawcolor.name = color_name
            log.info("%s --> %s" % (side_name, color_name))
        log.info("")

    def identify_middle_squares(self):
        log.info('ID middle square colors')

        for side_name in self.side_order:
            side = self.sides[side_name]
            side.color = self.crayon_box[side_name]

            # The middle square must match the color in the crayon_box for this side
            # so pass a dictionary with just this one color
            side.middle_square.find_closest_match({'foo': side.color})
            log.info("%s is %s" % (side.middle_square, side.middle_square.color.name))
        log.info('\n')

        self.valid_edges = []
        self.valid_edges.append((self.sideU.color, self.sideF.color))
        self.valid_edges.append((self.sideU.color, self.sideL.color))
        self.valid_edges.append((self.sideU.color, self.sideR.color))
        self.valid_edges.append((self.sideU.color, self.sideB.color))

        self.valid_edges.append((self.sideF.color, self.sideL.color))
        self.valid_edges.append((self.sideF.color, self.sideR.color))
        self.valid_edges.append((self.sideB.color, self.sideL.color))
        self.valid_edges.append((self.sideB.color, self.sideR.color))

        self.valid_edges.append((self.sideD.color, self.sideF.color))
        self.valid_edges.append((self.sideD.color, self.sideL.color))
        self.valid_edges.append((self.sideD.color, self.sideR.color))
        self.valid_edges.append((self.sideD.color, self.sideB.color))
        self.valid_edges = sorted(self.valid_edges)

        self.valid_corners = []
        self.valid_corners.append((self.sideU.color, self.sideF.color, self.sideL.color))
        self.valid_corners.append((self.sideU.color, self.sideR.color, self.sideF.color))
        self.valid_corners.append((self.sideU.color, self.sideL.color, self.sideB.color))
        self.valid_corners.append((self.sideU.color, self.sideB.color, self.sideR.color))

        self.valid_corners.append((self.sideD.color, self.sideL.color, self.sideF.color))
        self.valid_corners.append((self.sideD.color, self.sideF.color, self.sideR.color))
        self.valid_corners.append((self.sideD.color, self.sideB.color, self.sideL.color))
        self.valid_corners.append((self.sideD.color, self.sideR.color, self.sideB.color))
        self.valid_corners = sorted(self.valid_corners)

    def identify_edge_squares(self):
        log.info('ID edge square colors')

        for side in self.sides.values():
            for square in side.edge_squares:
                square.find_closest_match(self.crayon_box)

    def identify_corner_squares(self):
        log.info('ID corner square colors')

        for side in self.sides.values():
            for square in side.corner_squares:
                square.find_closest_match(self.crayon_box)

    def create_edges_and_corners(self):
        """
        The Edge objects below are used to represent a tuple of two Square objects.
        Not to be confused with self.valid_edges which are the tuples of color
        combinations we know we must have based on the colors of the six sides.
        """

        # Edges
        # U
        self.edges.append(Edge(self, 2, 38))
        self.edges.append(Edge(self, 4, 11))
        self.edges.append(Edge(self, 6, 29))
        self.edges.append(Edge(self, 8, 20))

        # F
        self.edges.append(Edge(self, 15, 22))
        self.edges.append(Edge(self, 24, 31))
        self.edges.append(Edge(self, 26, 47))

        # L
        self.edges.append(Edge(self, 13, 42))
        self.edges.append(Edge(self, 17, 49))

        # R
        self.edges.append(Edge(self, 35, 51))
        self.edges.append(Edge(self, 33, 40))

        # B
        self.edges.append(Edge(self, 44, 53))

        # Corners
        # U
        self.corners.append(Corner(self, 1, 10, 39))
        self.corners.append(Corner(self, 3, 37, 30))
        self.corners.append(Corner(self, 7, 19, 12))
        self.corners.append(Corner(self, 9, 28, 21))

        # B
        self.corners.append(Corner(self, 46, 18, 25))
        self.corners.append(Corner(self, 48, 27, 34))
        self.corners.append(Corner(self, 52, 45, 16))
        self.corners.append(Corner(self, 54, 36, 43))

    def valid_cube_parity(self, fake_corner_parity):
        """
        verify_parity() returns
         0: Cube is solvable
        -1: There is not exactly one facelet of each colour
        -2: Not all 12 edges exist exactly once
        -3: Flip error: One edge has to be flipped
        -4: Not all 8 corners exist exactly once
        -5: Twist error: One corner has to be twisted
        -6: Parity error: Two corners or two edges have to be exchanged

        Given how we assign colors it is not possible for us to generate a cube
        that returns -1, -2, or -4
        """
        cube_string = ''.join(map(str, self.cube_for_kociemba()))

        if fake_corner_parity:

            # Fill in the corners with data that we know to be valid parity
            # We do this when we are validating the parity of the edges
            cube_string = list(cube_string)
            cube_string[0] = 'U'
            cube_string[2] = 'U'
            cube_string[6] = 'U'
            cube_string[8] = 'U'

            cube_string[9] = 'R'
            cube_string[11] = 'R'
            cube_string[15] = 'R'
            cube_string[17] = 'R'

            cube_string[18] = 'F'
            cube_string[20] = 'F'
            cube_string[24] = 'F'
            cube_string[26] = 'F'

            cube_string[27] = 'D'
            cube_string[29] = 'D'
            cube_string[33] = 'D'
            cube_string[35] = 'D'

            cube_string[36] = 'L'
            cube_string[38] = 'L'
            cube_string[42] = 'L'
            cube_string[44] = 'L'

            cube_string[45] = 'B'
            cube_string[47] = 'B'
            cube_string[51] = 'B'
            cube_string[53] = 'B'
            cube_string = ''.join(cube_string)

        result = verify_parity(cube_string)

        if not result:
            return True

        # Must ignore this one since we made up the corners
        if fake_corner_parity and result == -6:
            return True

        log.debug("parity is %s" % result)
        return False

    def valid_edge_parity(self):
        return self.valid_cube_parity(fake_corner_parity=True)

    def resolve_edge_squares(self):
        log.info('Resolve edges')

        # Initially we flag all of our Edge objects as invalid
        for edge in self.edges:
            edge.valid = False

        # And our 'needed' list will hold all 12 edges
        needed_edges = sorted(self.valid_edges)

        unresolved_edges = [edge for edge in self.edges if edge.valid is False]
        permutation_count = factorial(len(needed_edges))
        best_match_total_distance = 0

        # 12 edges will mean 479,001,600 permutations which is too many.  Examine
        # all 12 edges and find the one we can match against a needed_edge that produces
        # the lowest color distance. update_colors() for this edge, mark it as
        # valid and remove it from the needed_edges.  Repeat this until the
        # number of permutations of needed_edges is down to our permutation_limit.
        if permutation_count > self.edge_permutation_limit:
            scores_by_edge_pair = {}

            for edge in unresolved_edges:
                for (colorA, colorB) in needed_edges:
                    distance = edge.color_distance(colorA, colorB)

                    if edge not in scores_by_edge_pair:
                        scores_by_edge_pair[edge] = []

                    scores_by_edge_pair[edge].append((distance, (colorA, colorB)))

            # For each edge keep the top two scores
            for (edge, value) in scores_by_edge_pair.items():
                scores_by_edge_pair[edge] = sorted(value)[0:2]

            # Now compute the delta between the first place score and the second place score for each edge
            score_delta = []

            for (edge, value) in scores_by_edge_pair.items():
                first_place_distance = value[0][0]
                second_place_distance = value[1][0]
                first_place_color = value[0][1]

                for (distance, (colorA, colorB)) in value:
                    log.info("edge_best_match %s, score %s, colorA %s, colorB %s" % (edge, distance, colorA.name, colorB.name))
                log.info('')
                score_delta.append((second_place_distance - first_place_distance, edge, (first_place_color[0], first_place_color[1])))

            score_delta = list(reversed(sorted(score_delta)))

            log.info("SCORES DELTA")
            for (distance, edge_best_match, (colorA, colorB)) in score_delta:
                log.info("%s, edge_best_match %s, colorA %s, colorB %s" % (distance, edge_best_match, colorA.name, colorB.name))

            while permutation_count > self.edge_permutation_limit:

                for (distance, edge_best_match, (colorA, colorB)) in score_delta:
                    if edge_best_match in unresolved_edges and (colorA, colorB) in needed_edges:
                        break
                else:
                    raise Exception("Did not find an edge in unresolved_edges")

                best_match_total_distance += distance
                edge_best_match.update_colors(colorA, colorB)
                edge_best_match.valid = True
                needed_edges.remove((colorA, colorB))

                unresolved_edges = [edge for edge in self.edges if edge.valid is False]
                permutation_count = factorial(len(needed_edges))
                log.info("%s/%s best match is %s with distance %d (permutations %d/%d)" %
                         (colorA.name, colorB.name, edge_best_match, distance, permutation_count, self.edge_permutation_limit))

        score_per_permutation = []

        log.info("Calculate edge score for each permutation")
        for edge_permutation in permutations(unresolved_edges):
            total_distance = 0

            for (edge, (colorA, colorB)) in zip(edge_permutation, needed_edges):
                total_distance += edge.color_distance(colorA, colorB)

            score_per_permutation.append((total_distance, edge_permutation))

        score_per_permutation = sorted(score_per_permutation)

        # Now traverse the permutations from best score to worst. The first
        # permutation that produces a set of edges with valid parity is the
        # permutation we want (most of the time the first entry has valid parity).
        log.info("Find edge permutation with the lowest score with valid parity")

        for (_, permutation) in score_per_permutation:
            total_distance = best_match_total_distance

            for (edge_best_match, (colorA, colorB)) in zip(permutation, needed_edges):
                distance = edge_best_match.color_distance(colorA, colorB)
                total_distance += distance
                edge_best_match.update_colors(colorA, colorB)
                edge_best_match.valid = True

            if self.valid_edge_parity():
                log.info("%s/%s potential match is %s with distance %d" %
                         (colorA.name, colorB.name, edge_best_match, distance))
                log.info("Total distance: %d, edge parity is valid" % total_distance)
                break
            else:
                log.debug("Total distance: %d, edge parity is NOT valid" % total_distance)

        log.info('\n')

    def resolve_corner_squares(self):
        log.info('Resolve corners')

        # Initially we flag all of our Edge objects as invalid
        for corner in self.corners:
            corner.valid = False

        # And our 'needed' list will hold all 8 corners.
        needed_corners = sorted(self.valid_corners)

        unresolved_corners = [corner for corner in self.corners if corner.valid is False]
        permutation_count = factorial(len(needed_corners))
        best_match_total_distance = 0

        # 8 corners will mean 40320 permutations which is too many.  Examine
        # all 8 and find the one we can match against a needed_corner that produces
        # the lowest color distance. update_colors() for this corner, mark it as
        # valid and remove it from the needed_corners.  Repeat this until the
        # number of permutations of needed_corners is down to our permutation_limit.
        if permutation_count > self.corner_permutation_limit:

            scores_by_corner = {}

            for corner in unresolved_corners:
                for (colorA, colorB, colorC) in needed_corners:
                    distance = corner.color_distance(colorA, colorB, colorC)

                    if corner not in scores_by_corner:
                        scores_by_corner[corner] = []
                    scores_by_corner[corner].append((distance, (colorA, colorB, colorC)))

            # For each corner keep the top two scores
            for (corner, value) in scores_by_corner.items():
                scores_by_corner[corner] = sorted(value)[0:2]

            # Now compute the delta between the first place score and the second place score for each edge
            score_delta = []

            for (corner, value) in scores_by_corner.items():
                first_place_distance = value[0][0]
                second_place_distance = value[1][0]
                first_place_color = value[0][1]

                for (distance, (colorA, colorB, colorC)) in value:
                    log.info("corner_best_match %s, score %s, colorA %s, colorB %s, colorC %s" % (corner, distance, colorA.name, colorB.name, colorC.name))
                log.info('')
                score_delta.append((second_place_distance - first_place_distance, corner, (first_place_color[0], first_place_color[1], first_place_color[2])))

            score_delta = list(reversed(sorted(score_delta)))

            log.info("SCORES DELTA")
            for (distance, corner_best_match, (colorA, colorB, colorC)) in score_delta:
                log.info("%s, corner_best_match %s, colorA %s, colorB %s, colorC %s" % (distance, corner_best_match, colorA.name, colorB.name, colorC.name))

            while permutation_count > self.corner_permutation_limit:

                for (distance, corner_best_match, (colorA, colorB, colorC)) in score_delta:
                    if corner_best_match in unresolved_corners and (colorA, colorB, colorC) in needed_corners:
                        break
                else:
                    raise Exception("Did not find a corner in unresolved_corners")

                best_match_total_distance += distance
                corner_best_match.update_colors(colorA, colorB, colorC)
                corner_best_match.valid = True
                needed_corners.remove((colorA, colorB, colorC))

                unresolved_corners = [corner for corner in self.corners if corner.valid is False]
                permutation_count = factorial(len(needed_corners))
                log.info("%s/%s/%s best match is %s with distance %d (permutations %d/%d)" %
                         (colorA.name, colorB.name, colorC.name, corner_best_match, distance, permutation_count, self.corner_permutation_limit))

        score_per_permutation = []

        for corner_permutation in permutations(unresolved_corners):
            total_distance = 0

            for (corner, (colorA, colorB, colorC)) in zip(corner_permutation, needed_corners):
                total_distance += corner.color_distance(colorA, colorB, colorC)

            score_per_permutation.append((total_distance, corner_permutation))

        score_per_permutation = sorted(score_per_permutation)

        # Now traverse the permutations from best score to worst. The first
        # permutation that produces a cube with valid parity is the permutation
        # we want (most of the time the first entry has valid parity).
        for (_, permutation) in score_per_permutation:
            total_distance = best_match_total_distance

            for (corner_best_match, (colorA, colorB, colorC)) in zip(permutation, needed_corners):
                distance = corner_best_match.color_distance(colorA, colorB, colorC)
                total_distance += distance
                corner_best_match.update_colors(colorA, colorB, colorC)
                corner_best_match.valid = True

            if self.valid_cube_parity(fake_corner_parity=False):
                log.info("%s/%s/%s best match is %s with distance %d" %
                         (colorA.name, colorB.name, colorC.name, corner_best_match, distance))
                log.info("Total distance: %d, cube parity is valid" % total_distance)
                break
            else:
                log.debug("Total distance: %d, cube parity is NOT valid" % total_distance)

        log.info('\n')

    def crunch_colors(self):
        log.info('Discover the six colors')
        self.name_middle_square_colors()

        # 6 middles, 12 edges, 8 corners
        self.identify_middle_squares()
        self.identify_edge_squares()
        self.identify_corner_squares()

        self.create_edges_and_corners()
        self.resolve_edge_squares()
        self.resolve_corner_squares()

        self.print_layout()
        self.print_cube()
        return self.cube_for_kociemba()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('rgb', help='RGB json', default=None)
    args = parser.parse_args()

    # logging.basicConfig(filename='rubiks-rgb-solver.log',
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)5s: %(message)s')
    log = logging.getLogger(__name__)

    try:
        cube = RubiksColorSolver()
        scan_data_str_keys = json.loads(args.rgb)
        scan_data = {}

        for (key, value) in scan_data_str_keys.items():
            scan_data[int(key)] = value

        cube.enter_scan_data(scan_data)
        kociemba = cube.crunch_colors()
        print(''.join(map(str, kociemba)))

    except Exception as e:
        log.exception(e)
        sys.exit(1)
