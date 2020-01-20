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


class StopWatchAlreadyStartedException(Exception):
    """
    Exception raised when start() is called on a StopWatch which was already start()ed and not yet
    stopped.
    """
    pass


class StopWatch(object):
    """
    A timer class which lets you start timing and then check the amount of time
    elapsed.
    """
    def __init__(self, desc=None):
        """
        Initializes the StopWatch but does not start it.

        desc:
            A string description to print when stringifying.
        """
        self.desc = desc
        self._start_time = None
        self._stopped_total_time = None

    def __str__(self):
        name = self.desc if self.desc is not None else self.__class__.__name__
        return "{}: {}".format(name, self.hms_str)

    def start(self):
        """
        Starts the timer. If the timer is already running, resets it.

        Raises a :py:class:`ev3dev2.stopwatch.StopWatchAlreadyStartedException` if already started.
        """
        if self.is_started:
            raise StopWatchAlreadyStartedException()

        self._stopped_total_time = None
        self._start_time = get_ticks_ms()

    def stop(self):
        """
        Stops the timer. The time value of this Stopwatch is paused and will not continue increasing.
        """
        if self._start_time is None:
            return

        self._stopped_total_time = get_ticks_ms() - self._start_time
        self._start_time = None

    def reset(self):
        """
        Resets the timer and leaves it stopped.
        """
        self._start_time = None
        self._stopped_total_time = None

    def restart(self):
        """
        Resets and then starts the timer.
        """
        self.reset()
        self.start()

    @property
    def is_started(self):
        """
        True if the StopWatch has been started but not stoped (i.e., it's currently running), false otherwise.
        """
        return self._start_time is not None

    @property
    def value_ms(self):
        """
        Returns the value of the stopwatch in milliseconds
        """
        if self._stopped_total_time is not None:
            return self._stopped_total_time

        return get_ticks_ms() - self._start_time if self._start_time is not None else 0

    @property
    def value_secs(self):
        """
        Returns the value of the stopwatch in seconds
        """
        return self.value_ms / 1000

    @property
    def value_hms(self):
        """
        Returns this StopWatch's elapsed time as a tuple
        ``(hours, minutes, seconds, milliseconds)``.
        """
        (hours, x) = divmod(int(self.value_ms), 3600000)
        (mins, x) = divmod(x, 60000)
        (secs, x) = divmod(x, 1000)
        return hours, mins, secs, x

    @property
    def hms_str(self):
        """
        Returns the stringified value of the stopwatch in HH:MM:SS.msec format
        """
        return '%02d:%02d:%02d.%03d' % self.value_hms

    def is_elapsed_ms(self, duration_ms):
        """
        Returns True if this timer has measured at least ``duration_ms``
        milliseconds.
        Otherwise, returns False. If ``duration_ms`` is None, returns False.
        """

        return duration_ms is not None and self.value_ms >= duration_ms

    def is_elapsed_secs(self, duration_secs):
        """
        Returns True if this timer has measured at least ``duration_secs`` seconds.
        Otherwise, returns False. If ``duration_secs`` is None, returns False.
        """

        return duration_secs is not None and self.value_secs >= duration_secs
