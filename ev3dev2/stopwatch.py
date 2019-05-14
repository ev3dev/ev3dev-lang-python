"""
A StopWatch class for tracking the amount of time between events
"""

from ev3dev2 import is_micropython

if is_micropython():
    import utime
else:
    import datetime as dt


def get_ticks_ms():
    if is_micropython():
        return utime.ticks_ms()
    else:
        return int(dt.datetime.timestamp(dt.datetime.now()) * 1000)


class StopWatch(object):

    def __init__(self, desc=None):
        self.desc = desc
        self._value = 0
        self.start_time = None
        self.prev_update_time = None

    def __str__(self):
        if self.desc is not None:
            return self.desc
        else:
            return self.__class__.__name__

    def start(self):
        assert self.start_time is None, "%s is already running" % self
        self.start_time = get_ticks_ms()

    def update(self):

        if self.start_time is None:
            return

        current_time = get_ticks_ms()

        if self.prev_update_time is None:
            delta = current_time - self.start_time
        else:
            delta = current_time - self.prev_update_time

        self._value += delta
        self.prev_update_time = current_time

    def stop(self):

        if self.start_time is None:
            return

        self.update()
        self.start_time = None
        self.prev_update_time = None

    def reset(self):
        self.stop()
        self._value = 0

    @property
    def value_ms(self):
        """
        Returns the value of the stopwatch in milliseconds
        """
        self.update()
        return self._value

    @property
    def value_hms(self):
        """
        Returns the value of the stopwatch in HH:MM:SS.msec format
        """
        self.update()
        (hours, x) = divmod(int(self._value), 3600000)
        (mins, x) = divmod(x, 60000)
        (secs, x) = divmod(x, 1000)

        return '%02d:%02d:%02d.%03d' % (hours, mins, secs, x)
