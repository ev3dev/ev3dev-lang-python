#!/usr/bin/env python

# framebuffer.py
#
# Helper class for handling framebuffers for ev3dev

# The MIT License (MIT)
#
# Copyright (c) 2016 David Lechner <david@lechnology.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from ctypes import Structure, c_char, c_ulong, c_uint16, c_uint32
from enum import Enum
from fcntl import ioctl
from collections import namedtuple

class FrameBuffer(object):

    # ioctls
    _FBIOGET_VSCREENINFO = 0x4600
    _FBIOGET_FSCREENINFO = 0x4602
    _FBIOGET_CON2FBMAP = 0x460F

    class Type(Enum):
        PACKED_PIXELS = 0                   # Packed Pixels
        PLANES = 1                          # Non interleaved planes
        INTERLEAVED_PLANES = 2              # Interleaved planes
        TEXT = 3                            # Text/attributes
        VGA_PLANES = 4                      # EGA/VGA planes
        FOURCC = 5                          # Type identified by a V4L2 FOURCC

    class Visual(Enum):
        MONO01 = 0                          # Monochrome 1=Black 0=White
        MONO10 = 1                          # Monochrome 1=White 0=Black
        TRUECOLOR = 2                       # True color
        PSEUDOCOLOR = 3                     # Pseudo color (like atari)
        DIRECTCOLOR = 4                     # Direct color
        STATIC_PSEUDOCOLOR = 5              # Pseudo color readonly
        FOURCC = 6                          # Visual identified by a V4L2 FOURCC

    class _FixedScreenInfo(Structure):
        _fields_ = [
            ('id', c_char * 16),            # identification string eg "TT Builtin"
            ('smem_start', c_ulong),        # Start of frame buffer mem (physical address)
            ('smem_len', c_uint32),		    # Length of frame buffer mem
            ('type', c_uint32),             # see FB_TYPE_*
            ('type_aux', c_uint32),         # Interleave for interleaved Planes
            ('visual', c_uint32),           # see FB_VISUAL_*
            ('xpanstep', c_uint16),		    # zero if no hardware panning
            ('ypanstep', c_uint16),		    # zero if no hardware panning
            ('ywrapstep', c_uint16),        # zero if no hardware ywrap
            ('line_length', c_uint32),      # length of a line in bytes
            ('mmio_start', c_ulong),        # Start of Memory Mapped I/O (physical address)
            ('mmio_len', c_uint32),         # Length of Memory Mapped I/O
            ('accel', c_uint32),            # Indicate to driver which specific chip/card we have
            ('capabilities', c_uint16),     # see FB_CAP_*
            ('reserved', c_uint16 * 2),     # Reserved for future compatibility
        ]

    class _VariableScreenInfo(Structure):

        class _Bitfield(Structure):
            _fields_ = [
                ('offset', c_uint32),       # beginning of bitfield
                ('length', c_uint32),       # length of bitfield
                ('msb_right', c_uint32),    # != 0 : Most significant bit is right
            ]

        _fields_ = [
            ('xres', c_uint32),             # visible resolution
            ('yres', c_uint32),
            ('xres_virtual', c_uint32),     # virtual resolution
            ('yres_virtual', c_uint32),
            ('xoffset', c_uint32),          # offset from virtual to visible
            ('yoffset', c_uint32),          # resolution
            ('bits_per_pixel', c_uint32),   # guess what
            ('grayscale', c_uint32),        # 0 = color, 1 = grayscale, >1 = FOURCC
            ('red', _Bitfield),             # bitfield in fb mem if true color,
            ('green', _Bitfield),           # else only length is significant
            ('blue', _Bitfield),
            ('transp', _Bitfield),          # transparency
            ('nonstd', c_uint32),           # != 0 Non standard pixel format
            ('activate', c_uint32),         # see FB_ACTIVATE_*
            ('height', c_uint32),           # height of picture in mm
            ('width', c_uint32),            # width of picture in mm
            ('accel_flags', c_uint32),      # (OBSOLETE) see fb_info.flags
            # Timing: All values, in pixclocks, except pixclock (of course)
            ('pixclock', c_uint32),         # pixel clock in ps (pico seconds)
            ('left_margin', c_uint32),      # time from sync to picture
            ('right_margin', c_uint32),     # time from picture to sync
            ('upper_margin', c_uint32),     # time from sync to picture
            ('lower_margin', c_uint32),
            ('hsync_len', c_uint32),        # length of horizontal sync
            ('vsync_len', c_uint32),        # length of vertical sync
            ('sync', c_uint32),             # see FB_SYNC_*
            ('vmode', c_uint32),            # see FB_VMODE_*
            ('rotate', c_uint32),           # angle we rotate counter clockwise
            ('colorspace', c_uint32),       # colorspace for FOURCC-based modes
            ('reserved', c_uint32 * 4),     # Reserved for future compatibility
        ]

    class _Console2FrameBufferMap(Structure):
        _fields_ = [
            ('console', c_uint32),
            ('framebuffer', c_uint32),
        ]

    def __init__(self, device='/dev/fb0'):
        self._fd = open(device, mode='r+b', buffering=0)
        self._fixed_info = self._FixedScreenInfo()
        ioctl(self._fd, self._FBIOGET_FSCREENINFO, self._fixed_info)
        self._variable_info = self._VariableScreenInfo()
        ioctl(self._fd, self._FBIOGET_VSCREENINFO, self._variable_info)
        
    def close(self):
        self._fd.close()

    def clear(self):
        self._fd.seek(0)
        self._fd.write(b'\0' * self._fixed_info.smem_len)

    def write_raw(self, data):
        self._fd.seek(0)
        self._fd.write(data)

    @staticmethod
    def get_fb_for_console(console):
        with open('/dev/fb0', mode='r+b') as fd:
            m = FrameBuffer._Console2FrameBufferMap()
            m.console = console
            ioctl(fd, FrameBuffer._FBIOGET_CON2FBMAP, m)
            return FrameBuffer('/dev/fb{}'.format(m.framebuffer))

    @property
    def type(self):
        return self.Type(self._fixed_info.type)

    @property
    def visual(self):
        return self.Visual(self._fixed_info.visual)

    @property
    def line_length(self):
        return self._fixed_info.line_length

    @property
    def resolution(self):
        """Visible resolution"""
        Resolution = namedtuple('Resolution', 'x y')
        return Resolution(self._variable_info.xres, self._variable_info.yres)

    @property
    def bits_per_pixel(self):
        return self._variable_info.bits_per_pixel

    @property
    def grayscale(self):
        return self._variable_info.grayscale

    @property
    def size(self):
        """Size of picture in mm"""
        Size = namedtuple('Size', 'width height')
        return Size(self._variable_info.width, self._variable_info.height)
