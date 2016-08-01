#!/usr/bin/env python

# virtualterminal.py
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

from ctypes import Structure, c_char, c_short, c_ushort, c_uint
from enum import Enum
from fcntl import ioctl

class VirtualTerminal(object):

    # ioctls
    _VT_OPENQRY = 0x5600                # find next available vt
    _VT_GETMODE = 0x5601                # get mode of active vt
    _VT_SETMODE = 0x5602                # set mode of active vt
    _VT_GETSTATE = 0x5603               # get global vt state info
    _VT_SENDSIG = 0x5604                # signal to send to bitmask of vts
    _VT_RELDISP = 0x5605                # release display
    _VT_ACTIVATE = 0x5606               # make vt active
    _VT_WAITACTIVE = 0x5607             # wait for vt active
    _VT_DISALLOCATE = 0x5608            # free memory associated to vt
    _VT_SETACTIVATE = 0x560F            # Activate and set the mode of a console
    _KDSETMODE = 0x4B3A                 # set text/graphics mode

    class _VtMode(Structure):
        _fields_ = [
            ('mode', c_char),           # vt mode
            ('waitv', c_char),          # if set, hang on writes if not active
            ('relsig', c_short),        # signal to raise on release request
            ('acqsig', c_short),        # signal to raise on acquisition
            ('frsig', c_short),         # unused (set to 0)
        ]

    class VtMode(Enum):
        AUTO = 0
        PROCESS = 1
        ACKACQ = 2

    class _VtState(Structure):
        _fields_ = [
            ('v_active', c_ushort),     # active vt
            ('v_signal', c_ushort),     # signal to send
            ('v_state', c_ushort),      # vt bitmask
        ]

    class KdMode(Enum):
        TEXT = 0x00
        GRAPHICS = 0x01
        TEXT0 = 0x02                    # obsolete
        TEXT1 = 0x03                    # obsolete

    def __init__(self):
        self._fd = open('/dev/tty', 'r')

    def close(self):
        self._fd.close()

    def get_next_available(self):
        n = c_uint()
        ioctl(self._fd, self._VT_OPENQRY, n)
        return n.value

    def activate(self, num):
        ioctl(self._fd, self._VT_ACTIVATE, num)
        ioctl(self._fd, self._VT_WAITACTIVE, num)

    def get_active(self):
        state = VirtualTerminal._VtState()
        ioctl(self._fd, self._VT_GETSTATE, state)
        return state.v_active

    def set_graphics_mode(self):
        ioctl(self._fd, self._KDSETMODE, self.KdMode.GRAPHICS.value)

    def set_text_mode(self):
        ioctl(self._fd, self._KDSETMODE, self.KdMode.TEXT.value)
