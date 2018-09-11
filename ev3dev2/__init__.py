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

def is_micropython():
    return sys.implementation.name == "micropython"

def chain_exception(exception, cause):
    if is_micropython():
        raise exception
    else:
        raise exception from cause

import os
import io
import fnmatch
import re
import stat
import errno
from os.path import abspath

INPUT_AUTO = ''
OUTPUT_AUTO = ''


def get_current_platform():
    """
    Look in /sys/class/board-info/ to determine the platform type.

    This can return 'ev3', 'evb', 'pistorms', 'brickpi', 'brickpi3' or 'fake'.
    """
    board_info_dir = '/sys/class/board-info/'

    if not os.path.exists(board_info_dir):
        return 'fake'

    for board in os.listdir(board_info_dir):
        uevent_filename = os.path.join(board_info_dir, board, 'uevent')

        if os.path.exists(uevent_filename):
            with open(uevent_filename, 'r') as fh:
                for line in fh.readlines():
                    (key, value) = line.strip().split('=')

                    if key == 'BOARD_INFO_MODEL':

                        if value == 'LEGO MINDSTORMS EV3':
                            return 'ev3'

                        elif value in ('FatcatLab EVB', 'QuestCape'):
                            return 'evb'

                        elif value == 'PiStorms':
                            return 'pistorms'

                        # This is the same for both BrickPi and BrickPi+.
                        # There is not a way to tell the difference.
                        elif value == 'Dexter Industries BrickPi':
                            return 'brickpi'

                        elif value == 'Dexter Industries BrickPi3':
                            return 'brickpi3'

                        elif value == 'FAKE-SYS':
                            return 'fake'

    return None


# -----------------------------------------------------------------------------
def list_device_names(class_path, name_pattern, **kwargs):
    """
    This is a generator function that lists names of all devices matching the
    provided parameters.

    Parameters:
        class_path: class path of the device, a subdirectory of /sys/class.
            For example, '/sys/class/tacho-motor'.
        name_pattern: pattern that device name should match.
            For example, 'sensor*' or 'motor*'. Default value: '*'.
        keyword arguments: used for matching the corresponding device
            attributes. For example, address='outA', or
            driver_name=['lego-ev3-us', 'lego-nxt-us']. When argument value
            is a list, then a match against any entry of the list is
            enough.
    """

    if not os.path.isdir(class_path):
        return

    def matches(attribute, pattern):
        try:
            with io.FileIO(attribute) as f:
                value = f.read().strip().decode()
        except:
            return False

        if isinstance(pattern, list):
            return any([value.find(p) >= 0 for p in pattern])
        else:
            return value.find(pattern) >= 0

    for f in os.listdir(class_path):
        if fnmatch.fnmatch(f, name_pattern):
            path = class_path + '/' + f
            if all([matches(path + '/' + k, kwargs[k]) for k in kwargs]):
                yield f


def library_load_warning_message(library_name, dependent_class):
    return 'Import warning: Failed to import "{}". {} will be unusable!'.format(library_name, dependent_class)

class DeviceNotFound(Exception):
    pass

# -----------------------------------------------------------------------------
# Define the base class from which all other ev3dev classes are defined.

class Device(object):
    """The ev3dev device base class"""

    __slots__ = ['_path', '_device_index', 'kwargs']

    DEVICE_ROOT_PATH = '/sys/class'

    _DEVICE_INDEX = re.compile(r'^.*(\d+)$')

    def __init__(self, class_name, name_pattern='*', name_exact=False, **kwargs):
        """Spin through the Linux sysfs class for the device type and find
        a device that matches the provided name pattern and attributes (if any).

        Parameters:
            class_name: class name of the device, a subdirectory of /sys/class.
                For example, 'tacho-motor'.
            name_pattern: pattern that device name should match.
                For example, 'sensor*' or 'motor*'. Default value: '*'.
            name_exact: when True, assume that the name_pattern provided is the
                exact device name and use it directly.
            keyword arguments: used for matching the corresponding device
                attributes. For example, address='outA', or
                driver_name=['lego-ev3-us', 'lego-nxt-us']. When argument value
                is a list, then a match against any entry of the list is
                enough.

        Example::

            d = ev3dev.Device('tacho-motor', address='outA')
            s = ev3dev.Device('lego-sensor', driver_name=['lego-ev3-us', 'lego-nxt-us'])

        If there was no valid connected device, an error is thrown.
        """

        classpath = abspath(Device.DEVICE_ROOT_PATH + '/' + class_name)
        self.kwargs = kwargs

        def get_index(file):
            match = Device._DEVICE_INDEX.match(file)
            if match:
                return int(match.group(1))
            else:
                return None

        if name_exact:
            self._path = classpath + '/' + name_pattern
            self._device_index = get_index(name_pattern)
        else:
            try:
                name = next(list_device_names(classpath, name_pattern, **kwargs))
                self._path = classpath + '/' + name
                self._device_index = get_index(name)
            except StopIteration:
                self._path = None
                self._device_index = None

                chain_exception(DeviceNotFound("%s is not connected." % self), None)

    def __str__(self):
        if 'address' in self.kwargs:
            return "%s(%s)" % (self.__class__.__name__, self.kwargs.get('address'))
        else:
            return self.__class__.__name__
    
    def __repr__(self):
        return self.__str__()

    def _attribute_file_open(self, name):
        path = os.path.join(self._path, name)
        mode = stat.S_IMODE(os.stat(path)[stat.ST_MODE])
        r_ok = mode & stat.S_IRGRP
        w_ok = mode & stat.S_IWGRP

        if r_ok and w_ok:
            mode_str = 'r+'
        elif w_ok:
            mode_str = 'w'
        else:
            mode_str = 'r'

        return io.FileIO(path, mode_str)

    def _get_attribute(self, attribute, name):
        """Device attribute getter"""
        try:
            if attribute is None:
                attribute = self._attribute_file_open( name )
            else:
                attribute.seek(0)
            return attribute, attribute.read().strip().decode()
        except Exception as ex:
            self._raise_friendly_access_error(ex, name)

    def _set_attribute(self, attribute, name, value):
        """Device attribute setter"""
        try:
            if attribute is None:
                attribute = self._attribute_file_open( name )
            else:
                attribute.seek(0)

            if isinstance(value, str):
                value = value.encode()
            attribute.write(value)
            attribute.flush()
        except Exception as ex:
            self._raise_friendly_access_error(ex, name)
        return attribute

    def _raise_friendly_access_error(self, driver_error, attribute):
        if not isinstance(driver_error, OSError):
            raise driver_error

        driver_errorno = driver_error.args[0] if is_micropython() else driver_error.errno

        if driver_errorno == errno.EINVAL:
            if attribute == "speed_sp":
                try:
                    max_speed = self.max_speed
                except (AttributeError, Exception):
                    chain_exception(ValueError("The given speed value was out of range"), driver_error)
                else:
                    chain_exception(ValueError("The given speed value was out of range. Max speed: +/-" + str(max_speed)), driver_error)
            chain_exception(ValueError("One or more arguments were out of range or invalid"), driver_error)
        elif driver_errorno == errno.ENODEV or driver_errorno == errno.ENOENT:
            # We will assume that a file-not-found error is the result of a disconnected device
            # rather than a library error. If that isn't the case, at a minimum the underlying
            # error info will be printed for debugging.
            chain_exception(DeviceNotFound("%s is no longer connected" % self), driver_error)
        raise driver_error

    def get_attr_int(self, attribute, name):
        attribute, value = self._get_attribute(attribute, name)
        return attribute, int(value)

    def set_attr_int(self, attribute, name, value):
        return self._set_attribute(attribute, name, str(int(value)))

    def set_attr_raw(self, attribute, name, value):
        return self._set_attribute(attribute, name, value)

    def get_attr_string(self, attribute, name):
        return self._get_attribute(attribute, name)

    def set_attr_string(self, attribute, name, value):
        return self._set_attribute(attribute, name, value)

    def get_attr_line(self, attribute, name):
        return self._get_attribute(attribute, name)

    def get_attr_set(self, attribute, name):
        attribute, value = self.get_attr_line(attribute, name)
        return attribute, [v.strip('[]') for v in value.split()]

    def get_attr_from_set(self, attribute, name):
        attribute, value = self.get_attr_line(attribute, name)
        for a in value.split():
            v = a.strip('[]')
            if v != a:
                return v
        return ""

    @property
    def device_index(self):
        return self._device_index


def list_devices(class_name, name_pattern, **kwargs):
    """
    This is a generator function that takes same arguments as `Device` class
    and enumerates all devices present in the system that match the provided
    arguments.

    Parameters:
        class_name: class name of the device, a subdirectory of /sys/class.
            For example, 'tacho-motor'.
        name_pattern: pattern that device name should match.
            For example, 'sensor*' or 'motor*'. Default value: '*'.
        keyword arguments: used for matching the corresponding device
            attributes. For example, address='outA', or
            driver_name=['lego-ev3-us', 'lego-nxt-us']. When argument value
            is a list, then a match against any entry of the list is
            enough.
    """
    classpath = abspath(Device.DEVICE_ROOT_PATH + '/' + class_name)

    return (Device(class_name, name, name_exact=True)
            for name in list_device_names(classpath, name_pattern, **kwargs))
