# -----------------------------------------------------------------------------
# Copyright (c) 2015 Ralph Hempel <rhempel@hempeldesigngroup.com>
# Copyright (c) 2015 Anton Vanhoucke <antonvh@gmail.com>
# Copyright (c) 2015 Denis Demidov <dennis.demidov@gmail.com>
# Copyright (c) 2015 Eric Pascual <eric@pobot.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -----------------------------------------------------------------------------

import sys

if sys.version_info < (3,4):
    raise SystemError('Must be using Python 3.4 or higher')

import os
import mmap
import ctypes
import logging
from PIL import Image, ImageDraw
from . import fonts
from . import get_current_platform, library_load_warning_message
from struct import pack

log = logging.getLogger(__name__)

try:
    # This is a linux-specific module.
    # It is required by the Display class, but failure to import it may be
    # safely ignored if one just needs to run API tests on Windows.
    import fcntl
except ImportError:
    log.warning(library_load_warning_message("fcntl", "Display"))

class FbMem(object):

    """The framebuffer memory object.

    Made of:
        - the framebuffer file descriptor
        - the fix screen info struct
        - the var screen info struct
        - the mapped memory
    """

    # ------------------------------------------------------------------
    # The code is adapted from
    # https://github.com/LinkCareServices/cairotft/blob/master/cairotft/linuxfb.py
    #
    # The original code came with the following license:
    # ------------------------------------------------------------------
    # Copyright (c) 2012 Kurichan
    #
    # This program is free software. It comes without any warranty, to
    # the extent permitted by applicable law. You can redistribute it
    # and/or modify it under the terms of the Do What The Fuck You Want
    # To Public License, Version 2, as published by Sam Hocevar. See
    # http://sam.zoy.org/wtfpl/COPYING for more details.
    # ------------------------------------------------------------------

    __slots__ = ('fid', 'fix_info', 'var_info', 'mmap')

    FBIOGET_VSCREENINFO = 0x4600
    FBIOGET_FSCREENINFO = 0x4602

    FB_VISUAL_MONO01 = 0
    FB_VISUAL_MONO10 = 1

    class FixScreenInfo(ctypes.Structure):

        """The fb_fix_screeninfo from fb.h."""

        _fields_ = [
            ('id_name', ctypes.c_char * 16),
            ('smem_start', ctypes.c_ulong),
            ('smem_len', ctypes.c_uint32),
            ('type', ctypes.c_uint32),
            ('type_aux', ctypes.c_uint32),
            ('visual', ctypes.c_uint32),
            ('xpanstep', ctypes.c_uint16),
            ('ypanstep', ctypes.c_uint16),
            ('ywrapstep', ctypes.c_uint16),
            ('line_length', ctypes.c_uint32),
            ('mmio_start', ctypes.c_ulong),
            ('mmio_len', ctypes.c_uint32),
            ('accel', ctypes.c_uint32),
            ('reserved', ctypes.c_uint16 * 3),
        ]

    class VarScreenInfo(ctypes.Structure):

        class FbBitField(ctypes.Structure):

            """The fb_bitfield struct from fb.h."""

            _fields_ = [
                ('offset', ctypes.c_uint32),
                ('length', ctypes.c_uint32),
                ('msb_right', ctypes.c_uint32),
            ]

        """The fb_var_screeninfo struct from fb.h."""

        _fields_ = [
            ('xres', ctypes.c_uint32),
            ('yres', ctypes.c_uint32),
            ('xres_virtual', ctypes.c_uint32),
            ('yres_virtual', ctypes.c_uint32),
            ('xoffset', ctypes.c_uint32),
            ('yoffset', ctypes.c_uint32),

            ('bits_per_pixel', ctypes.c_uint32),
            ('grayscale', ctypes.c_uint32),

            ('red', FbBitField),
            ('green', FbBitField),
            ('blue', FbBitField),
            ('transp', FbBitField),
        ]

    def __init__(self, fbdev=None):
        """Create the FbMem framebuffer memory object."""
        fid = FbMem._open_fbdev(fbdev)
        fix_info = FbMem._get_fix_info(fid)
        fbmmap = FbMem._map_fb_memory(fid, fix_info)
        self.fid = fid
        self.fix_info = fix_info
        self.var_info = FbMem._get_var_info(fid)
        self.mmap = fbmmap

    def __del__(self):
        """Close the FbMem framebuffer memory object."""
        self.mmap.close()
        FbMem._close_fbdev(self.fid)

    @staticmethod
    def _open_fbdev(fbdev=None):
        """Return the framebuffer file descriptor.

        Try to use the FRAMEBUFFER
        environment variable if fbdev is not given. Use '/dev/fb0' by
        default.
        """
        dev = fbdev or os.getenv('FRAMEBUFFER', '/dev/fb0')
        fbfid = os.open(dev, os.O_RDWR)
        return fbfid

    @staticmethod
    def _close_fbdev(fbfid):
        """Close the framebuffer file descriptor."""
        os.close(fbfid)

    @staticmethod
    def _get_fix_info(fbfid):
        """Return the fix screen info from the framebuffer file descriptor."""
        fix_info = FbMem.FixScreenInfo()
        fcntl.ioctl(fbfid, FbMem.FBIOGET_FSCREENINFO, fix_info)
        return fix_info

    @staticmethod
    def _get_var_info(fbfid):
        """Return the var screen info from the framebuffer file descriptor."""
        var_info = FbMem.VarScreenInfo()
        fcntl.ioctl(fbfid, FbMem.FBIOGET_VSCREENINFO, var_info)
        return var_info

    @staticmethod
    def _map_fb_memory(fbfid, fix_info):
        """Map the framebuffer memory."""
        return mmap.mmap(
            fbfid,
            fix_info.smem_len,
            mmap.MAP_SHARED,
            mmap.PROT_READ | mmap.PROT_WRITE,
            offset=0
        )


class Display(FbMem):
    """
    A convenience wrapper for the FbMem class.
    Provides drawing functions from the python imaging library (PIL).
    """

    GRID_COLUMNS = 22
    GRID_COLUMN_PIXELS = 8
    GRID_ROWS = 12
    GRID_ROW_PIXELS = 10

    def __init__(self, desc='Display'):
        FbMem.__init__(self)

        self.platform = get_current_platform()

        if self.var_info.bits_per_pixel == 1:
            im_type = "1"
        elif self.var_info.bits_per_pixel == 16:
            im_type = "RGB"
        elif self.platform == "ev3" and self.var_info.bits_per_pixel == 32:
            im_type = "L"
        else:
            raise Exception("Not supported")

        self._img = Image.new(
                im_type,
                (self.fix_info.line_length * 8 // self.var_info.bits_per_pixel, self.yres),
                "white")

        self._draw = ImageDraw.Draw(self._img)
        self.desc = desc

    def __str__(self):
        return self.desc

    @property
    def xres(self):
        """
        Horizontal screen resolution
        """
        return self.var_info.xres

    @property
    def yres(self):
        """
        Vertical screen resolution
        """
        return self.var_info.yres

    @property
    def shape(self):
        """
        Dimensions of the screen.
        """
        return (self.xres, self.yres)

    @property
    def draw(self):
        """
        Returns a handle to PIL.ImageDraw.Draw class associated with the screen.

        Example::

            screen.draw.rectangle((10,10,60,20), fill='black')
        """
        return self._draw

    @property
    def image(self):
        """
        Returns a handle to PIL.Image class that is backing the screen. This can
        be accessed for blitting images to the screen.

        Example::

            screen.image.paste(picture, (0, 0))
        """
        return self._img

    def clear(self):
        """
        Clears the screen
        """
        self._draw.rectangle(((0, 0), self.shape), fill="white")

    def _color565(self, r, g, b):
        """Convert red, green, blue components to a 16-bit 565 RGB value. Components
        should be values 0 to 255.
        """
        return (((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3))

    def _img_to_rgb565_bytes(self):
        pixels = [self._color565(r, g, b) for (r, g, b) in self._img.getdata()]
        return pack('H' * len(pixels), *pixels)

    def update(self):
        """
        Applies pending changes to the screen.
        Nothing will be drawn on the screen until this function is called.
        """
        if self.var_info.bits_per_pixel == 1:
            b = self._img.tobytes("raw", "1;R")
            self.mmap[:len(b)] = b
        elif self.var_info.bits_per_pixel == 16:
            self.mmap[:] = self._img_to_rgb565_bytes()
        elif self.platform == "ev3" and self.var_info.bits_per_pixel == 32:
            self.mmap[:] = self._img.convert("RGB").tobytes("raw", "XRGB")
        else:
            raise Exception("Not supported")

    def image_filename(self, filename, clear_screen=True, x1=0, y1=0, x2=None, y2=None):

        if clear_screen:
            self.clear()

        filename_im = Image.open(filename)

        if x2 is not None and y2 is not None:
            return self._img.paste(filename_im, (x1, y1, x2, y2))
        else:
            return self._img.paste(filename_im, (x1, y1))

    def line(self, clear_screen=True, x1=10, y1=10, x2=50, y2=50, line_color='black', width=1):
        """
        Draw a line from (x1, y1) to (x2, y2)
        """

        if clear_screen:
            self.clear()

        return self.draw.line((x1, y1, x2, y2), fill=line_color, width=width)

    def circle(self, clear_screen=True, x=50, y=50, radius=40, fill_color='black', outline_color='black'):
        """
        Draw a circle of 'radius' centered at (x, y)
        """

        if clear_screen:
            self.clear()

        x1 = x - radius
        y1 = y - radius
        x2 = x + radius
        y2 = y + radius

        return self.draw.ellipse((x1, y1, x2, y2), fill=fill_color, outline=outline_color)

    def rectangle(self, clear_screen=True, x=10, y=10, width=80, height=40, fill_color='black', outline_color='black'):
        """
        Draw a rectangle 'width x height' where the top left corner is at (x, y)
        """

        if clear_screen:
            self.clear()

        return self.draw.rectangle((x, y, width, height), fill=fill_color, outline=outline_color)

    def point(self, clear_screen=True, x=10, y=10, point_color='black'):
        """
        Draw a single pixel at (x, y)
        """

        if clear_screen:
            self.clear()

        return self.draw.point((x, y), fill=point_color)

    def text_pixels(self, text, clear_screen=True, x=0, y=0, text_color='black', font=None):
        """
        Display `text` starting at pixel (x, y).

        The EV3 display is 178x128 pixels
        - (0, 0) would be the top left corner of the display
        - (89, 64) would be right in the middle of the display

        'text_color' : PIL says it supports "common HTML color names". There
        are 140 HTML color names listed here that are supported by all modern
        browsers. This is probably a good list to start with.
        https://www.w3schools.com/colors/colors_names.asp

        'font' : can be any font displayed here
            http://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/ev3dev-stretch/other.html#bitmap-fonts
        """

        if clear_screen:
            self.clear()

        if font is not None:
            assert font in fonts.available(), "%s is an invalid font" % font
            return self.draw.text((x, y), text, fill=text_color, font=fonts.load(font))
        else:
            return self.draw.text((x, y), text, fill=text_color)

    def text_grid(self, text, clear_screen=True, x=0, y=0, text_color='black', font=None):
        """
        Display 'text' starting at grid (x, y)

        The EV3 display can be broken down in a grid that is 22 columns wide
        and 12 rows tall. Each column is 8 pixels wide and each row is 10
        pixels tall.

        'text_color' : PIL says it supports "common HTML color names". There
        are 140 HTML color names listed here that are supported by all modern
        browsers. This is probably a good list to start with.
        https://www.w3schools.com/colors/colors_names.asp

        'font' : can be any font displayed here
            http://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/ev3dev-stretch/other.html#bitmap-fonts
        """

        assert 0 <= x < Display.GRID_COLUMNS,\
            "grid columns must be between 0 and %d, %d was requested" %\
            ((Display.GRID_COLUMNS - 1, x))

        assert 0 <= y < Display.GRID_ROWS,\
            "grid rows must be between 0 and %d, %d was requested" %\
            ((Display.GRID_ROWS - 1), y)

        return self.text_pixels(text, clear_screen,
                                x * Display.GRID_COLUMN_PIXELS,
                                y * Display.GRID_ROW_PIXELS,
                                text_color, font)

    def reset_screen(self):
        self.clear()
        self.update()
