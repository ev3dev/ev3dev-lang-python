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

if sys.version_info < (3, 4):
    raise SystemError('Must be using Python 3.4 or higher')

import os
import re
import shlex
from subprocess import check_output, Popen, PIPE


def _make_scales(notes):
    """ Utility function used by Sound class for building the note frequencies table """
    res = dict()
    for note, freq in notes:
        freq = round(freq)
        for n in note.split('/'):
            res[n] = freq
    return res


class Sound(object):
    """
    Support beep, play wav files, or convert text to speech.

    Note that all methods of the class spawn system processes and return
    subprocess.Popen objects. The methods are asynchronous (they return
    immediately after child process was spawned, without waiting for its
    completion), but you can call wait() on the returned result.

    Examples::

        # Play 'bark.wav':
        Sound.play('bark.wav')

        # Introduce yourself:
        Sound.speak('Hello, I am Robot')

        # Play a small song
        Sound.play_song((
            ('D4', 'e3'),
            ('D4', 'e3'),
            ('D4', 'e3'),
            ('G4', 'h'),
            ('D5', 'h')
        ))

    In order to mimic EV3-G API parameters, durations used in methods
    exposed as EV3-G blocks for sound related operations are expressed
    as a float number of seconds.
    """

    channel = None

    # play_types
    PLAY_WAIT_FOR_COMPLETE = 0 #: Play the sound and block until it is complete
    PLAY_NO_WAIT_FOR_COMPLETE = 1 #: Start playing the sound but return immediately
    PLAY_LOOP = 2 #: Never return; start the sound immediately after it completes, until the program is killed

    PLAY_TYPES = (
        PLAY_WAIT_FOR_COMPLETE,
        PLAY_NO_WAIT_FOR_COMPLETE,
        PLAY_LOOP
    )

    def _validate_play_type(self, play_type):
        assert play_type in self.PLAY_TYPES, \
            "Invalid play_type %s, must be one of %s" % (play_type, ','.join(str(t) for t in self.PLAY_TYPES))

    def beep(self, args='', play_type=PLAY_WAIT_FOR_COMPLETE):
        """
        Call beep command with the provided arguments (if any).
        See `beep man page`_ and google `linux beep music`_ for inspiration.

        :param string args: Any additional arguments to be passed to ``beep`` (see the `beep man page`_ for details)
        
        :param play_type: The behavior of ``beep`` once playback has been initiated
        :type play_type: ``Sound.PLAY_WAIT_FOR_COMPLETE`` or  ``Sound.PLAY_NO_WAIT_FOR_COMPLETE``

        :return: When ``Sound.PLAY_NO_WAIT_FOR_COMPLETE`` is specified, returns the returns the spawn subprocess from ``subprocess.Popen``; ``None`` otherwise

        .. _`beep man page`: https://linux.die.net/man/1/beep
        .. _`linux beep music`: https://www.google.com/search?q=linux+beep+music
        """
        with open(os.devnull, 'w') as n:
            subprocess = Popen(shlex.split('/usr/bin/beep %s' % args), stdout=n)
            if play_type == Sound.PLAY_WAIT_FOR_COMPLETE:
                subprocess.wait()
                return None
            else:
                return subprocess


    def tone(self, *args, play_type=PLAY_WAIT_FOR_COMPLETE):
        """
        .. rubric:: tone(tone_sequence)

        Play tone sequence.

        Here is a cheerful example::

            my_sound = Sound()
            my_sound.tone([
                (392, 350, 100), (392, 350, 100), (392, 350, 100), (311.1, 250, 100),
                (466.2, 25, 100), (392, 350, 100), (311.1, 250, 100), (466.2, 25, 100),
                (392, 700, 100), (587.32, 350, 100), (587.32, 350, 100),
                (587.32, 350, 100), (622.26, 250, 100), (466.2, 25, 100),
                (369.99, 350, 100), (311.1, 250, 100), (466.2, 25, 100), (392, 700, 100),
                (784, 350, 100), (392, 250, 100), (392, 25, 100), (784, 350, 100),
                (739.98, 250, 100), (698.46, 25, 100), (659.26, 25, 100),
                (622.26, 25, 100), (659.26, 50, 400), (415.3, 25, 200), (554.36, 350, 100),
                (523.25, 250, 100), (493.88, 25, 100), (466.16, 25, 100), (440, 25, 100),
                (466.16, 50, 400), (311.13, 25, 200), (369.99, 350, 100),
                (311.13, 250, 100), (392, 25, 100), (466.16, 350, 100), (392, 250, 100),
                (466.16, 25, 100), (587.32, 700, 100), (784, 350, 100), (392, 250, 100),
                (392, 25, 100), (784, 350, 100), (739.98, 250, 100), (698.46, 25, 100),
                (659.26, 25, 100), (622.26, 25, 100), (659.26, 50, 400), (415.3, 25, 200),
                (554.36, 350, 100), (523.25, 250, 100), (493.88, 25, 100),
                (466.16, 25, 100), (440, 25, 100), (466.16, 50, 400), (311.13, 25, 200),
                (392, 350, 100), (311.13, 250, 100), (466.16, 25, 100),
                (392.00, 300, 150), (311.13, 250, 100), (466.16, 25, 100), (392, 700)
                ])

        Have also a look at :py:meth:`play_song` for a more musician-friendly way of doing, which uses
        the conventional notation for notes and durations.

        :param list[tuple(float,float,float)] tone_sequence: The sequence of tones to play. The first number of each tuple is frequency in Hz, the second is duration in milliseconds, and the third is delay in milliseconds between this and the next tone in the sequence.

        :param play_type: The behavior of ``tone`` once playback has been initiated
        :type play_type: ``Sound.PLAY_WAIT_FOR_COMPLETE`` or ``Sound.PLAY_NO_WAIT_FOR_COMPLETE``

        :return: When ``Sound.PLAY_NO_WAIT_FOR_COMPLETE`` is specified, returns the returns the spawn subprocess from ``subprocess.Popen``; ``None`` otherwise

        .. rubric:: tone(frequency, duration)

        Play single tone of given frequency and duration.

        :param float frequency: The frequency of the tone in Hz
        :param float duration: The duration of the tone in milliseconds

        :param play_type: The behavior of ``tone`` once playback has been initiated
        :type play_type: ``Sound.PLAY_WAIT_FOR_COMPLETE`` or ``Sound.PLAY_NO_WAIT_FOR_COMPLETE``

        :return: When ``Sound.PLAY_NO_WAIT_FOR_COMPLETE`` is specified, returns the returns the spawn subprocess from ``subprocess.Popen``; ``None`` otherwise
        """
        def play_tone_sequence(tone_sequence):
            def beep_args(frequency=None, duration=None, delay=None):
                args = ''
                if frequency is not None:
                    args += '-f %s ' % frequency
                if duration  is not None:
                    args += '-l %s ' % duration
                if delay     is not None:
                    args += '-D %s ' % delay

                return args

            return self.beep(' -n '.join([beep_args(*t) for t in tone_sequence]), play_type=play_type)

        if len(args) == 1:
            return play_tone_sequence(args[0])
        elif len(args) == 2:
            return play_tone_sequence([(args[0], args[1])])
        else:
            raise Exception("Unsupported number of parameters in Sound.tone(): expected 1 or 2, got " + str(len(args)))

    def play_tone(self, frequency, duration, delay=0.0, volume=100,
                  play_type=PLAY_WAIT_FOR_COMPLETE):
        """ Play a single tone, specified by its frequency, duration, volume and final delay.

        :param int frequency: the tone frequency, in Hertz
        :param float duration: Tone duration, in seconds
        :param float delay: Delay after tone, in seconds (can be useful when chaining calls to ``play_tone``)
        :param int volume: The play volume, in percent of maximum volume

        :param play_type: The behavior of ``play_tone`` once playback has been initiated
        :type play_type: ``Sound.PLAY_WAIT_FOR_COMPLETE``, ``Sound.PLAY_NO_WAIT_FOR_COMPLETE`` or ``Sound.PLAY_LOOP``

        :return: When ``Sound.PLAY_NO_WAIT_FOR_COMPLETE`` is specified, returns the PID of the underlying beep command; ``None`` otherwise

        :raises ValueError: if invalid parameter
        """
        self._validate_play_type(play_type)

        if duration <= 0:
            raise ValueError('invalid duration (%s)' % duration)
        if delay < 0:
            raise ValueError('invalid delay (%s)' % delay)
        if not 0 < volume <= 100:
            raise ValueError('invalid volume (%s)' % volume)

        self.set_volume(volume)

        duration_ms = int(duration * 1000)
        delay_ms = int(delay * 1000)

        self.tone([(frequency, duration_ms, delay_ms)], play_type=play_type)

    def play_note(self, note, duration, volume=100, play_type=PLAY_WAIT_FOR_COMPLETE):
        """ Plays a note, given by its name as defined in ``_NOTE_FREQUENCIES``.

        :param string note: The note symbol with its octave number
        :param float duration: Tone duration, in seconds
        :param int volume: The play volume, in percent of maximum volume

        :param play_type: The behavior of ``play_note`` once playback has been initiated
        :type play_type: ``Sound.PLAY_WAIT_FOR_COMPLETE``, ``Sound.PLAY_NO_WAIT_FOR_COMPLETE`` or ``Sound.PLAY_LOOP``

        :return: When ``Sound.PLAY_NO_WAIT_FOR_COMPLETE`` is specified, returns the PID of the underlying beep command; ``None`` otherwise

        :raises ValueError: is invalid parameter (note, duration,...)
        """
        self._validate_play_type(play_type)
        try:
            freq = self._NOTE_FREQUENCIES[note.upper()]
        except KeyError:
            raise ValueError('invalid note (%s)' % note)
        if duration <= 0:
            raise ValueError('invalid duration (%s)' % duration)
        if not 0 < volume <= 100:
            raise ValueError('invalid volume (%s)' % volume)

        return self.play_tone(freq, duration=duration, volume=volume, play_type=play_type)

    def play(self, wav_file, play_type=PLAY_WAIT_FOR_COMPLETE):
        """ Play a sound file (wav format).

        :param string wav_file: The sound file path

        :param play_type: The behavior of ``play`` once playback has been initiated
        :type play_type: ``Sound.PLAY_WAIT_FOR_COMPLETE``, ``Sound.PLAY_NO_WAIT_FOR_COMPLETE`` or ``Sound.PLAY_LOOP``

        :returns: When ``Sound.PLAY_NO_WAIT_FOR_COMPLETE`` is specified, returns the spawn subprocess from ``subprocess.Popen``; ``None`` otherwise
        """
        self._validate_play_type(play_type)

        with open(os.devnull, 'w') as n:

            if play_type == Sound.PLAY_WAIT_FOR_COMPLETE:
                pid = Popen(shlex.split('/usr/bin/aplay -q "%s"' % wav_file), stdout=n)
                pid.wait()

            # Do not wait, run in the background
            elif play_type == Sound.PLAY_NO_WAIT_FOR_COMPLETE:
                return Popen(shlex.split('/usr/bin/aplay -q "%s"' % wav_file), stdout=n)

            elif play_type == Sound.PLAY_LOOP:
                while True:
                    pid = Popen(shlex.split('/usr/bin/aplay -q "%s"' % wav_file), stdout=n)
                    pid.wait()

    def play_file(self, wav_file, volume=100, play_type=PLAY_WAIT_FOR_COMPLETE):
        """ Play a sound file (wav format) at a given volume.

        
        :param string wav_file: The sound file path
        :param int volume: The play volume, in percent of maximum volume

        :param play_type: The behavior of ``play_file`` once playback has been initiated
        :type play_type: ``Sound.PLAY_WAIT_FOR_COMPLETE``, ``Sound.PLAY_NO_WAIT_FOR_COMPLETE`` or ``Sound.PLAY_LOOP``

        :returns: When ``Sound.PLAY_NO_WAIT_FOR_COMPLETE`` is specified, returns the spawn subprocess from ``subprocess.Popen``; ``None`` otherwise
        """
        self.set_volume(volume)
        self.play(wav_file, play_type)

    def speak(self, text, espeak_opts='-a 200 -s 130', volume=100, play_type=PLAY_WAIT_FOR_COMPLETE):
        """ Speak the given text aloud.

        Uses the ``espeak`` external command.

        :param string text: The text to speak
        :param string espeak_opts: ``espeak`` command options (advanced usage)
        :param int volume: The play volume, in percent of maximum volume

        :param play_type: The behavior of ``speak`` once playback has been initiated
        :type play_type: ``Sound.PLAY_WAIT_FOR_COMPLETE``, ``Sound.PLAY_NO_WAIT_FOR_COMPLETE`` or ``Sound.PLAY_LOOP``

        :returns: When ``Sound.PLAY_NO_WAIT_FOR_COMPLETE`` is specified, returns the spawn subprocess from ``subprocess.Popen``; ``None`` otherwise
        """
        self._validate_play_type(play_type)
        self.set_volume(volume)

        with open(os.devnull, 'w') as n:
            cmd_line = ['/usr/bin/espeak', '--stdout'] + shlex.split(espeak_opts) + [shlex.quote(text)]
            aplay_cmd_line = shlex.split('/usr/bin/aplay -q')

            if play_type == Sound.PLAY_WAIT_FOR_COMPLETE:
                espeak = Popen(cmd_line, stdout=PIPE)
                play = Popen(aplay_cmd_line, stdin=espeak.stdout, stdout=n)
                play.wait()

            elif play_type == Sound.PLAY_NO_WAIT_FOR_COMPLETE:
                espeak = Popen(cmd_line, stdout=PIPE)
                return Popen(aplay_cmd_line, stdin=espeak.stdout, stdout=n)

            elif play_type == Sound.PLAY_LOOP:
                while True:
                    espeak = Popen(cmd_line, stdout=PIPE)
                    play = Popen(aplay_cmd_line, stdin=espeak.stdout, stdout=n)
                    play.wait()

    def _get_channel(self):
        """
        :returns: The detected sound channel
        :rtype: string
        """
        if self.channel is None:
            # Get default channel as the first one that pops up in
            # 'amixer scontrols' output, which contains strings in the
            # following format:
            #
            #     Simple mixer control 'Master',0
            #     Simple mixer control 'Capture',0
            out = check_output(['amixer', 'scontrols']).decode()
            m = re.search(r"'(?P<channel>[^']+)'", out)
            if m:
                self.channel = m.group('channel')
            else:
                self.channel = 'Playback'

        return self.channel

    def set_volume(self, pct, channel=None):
        """
        Sets the sound volume to the given percentage [0-100] by calling
        ``amixer -q set <channel> <pct>%``.
        If the channel is not specified, it tries to determine the default one
        by running ``amixer scontrols``. If that fails as well, it uses the
        ``Playback`` channel, as that is the only channel on the EV3.
        """

        if channel is None:
            channel = self._get_channel()

        cmd_line = '/usr/bin/amixer -q set {0} {1:d}%'.format(channel, pct)
        Popen(shlex.split(cmd_line)).wait()

    def get_volume(self, channel=None):
        """
        Gets the current sound volume by parsing the output of
        ``amixer get <channel>``.
        If the channel is not specified, it tries to determine the default one
        by running ``amixer scontrols``. If that fails as well, it uses the
        ``Playback`` channel, as that is the only channel on the EV3.
        """

        if channel is None:
            channel = self._get_channel()

        out = check_output(['amixer', 'get', channel]).decode()
        m = re.search(r'\[(?P<volume>\d+)%\]', out)
        if m:
            return int(m.group('volume'))
        else:
            raise Exception('Failed to parse output of `amixer get {}`'.format(channel))

    def play_song(self, song, tempo=120, delay=0.05):
        """ Plays a song provided as a list of tuples containing the note name and its
        value using music conventional notation instead of numerical values for frequency
        and duration.

        It supports symbolic notes (e.g. ``A4``, ``D#3``, ``Gb5``) and durations (e.g. ``q``, ``h``).

        For an exhaustive list of accepted note symbols and values, have a look at the ``_NOTE_FREQUENCIES``
        and ``_NOTE_VALUES`` private dictionaries in the source code.

        The value can be suffixed by modifiers:

        - a *divider* introduced by a ``/`` to obtain triplets for instance
          (e.g. ``q/3`` for a triplet of eight note)
        - a *multiplier* introduced by ``*`` (e.g. ``*1.5`` is a dotted note).

        Shortcuts exist for common modifiers:

        - ``3`` produces a triplet member note. For instance `e3` gives a triplet of eight notes,
          i.e. 3 eight notes in the duration of a single quarter. You must ensure that 3 triplets
          notes are defined in sequence to match the count, otherwise the result will not be the
          expected one.
        - ``.`` produces a dotted note, i.e. which duration is one and a half the base one. Double dots
          are not currently supported.

        Example::

            >>> # A long time ago in a galaxy far,
            >>> # far away...
            >>> Sound.play_song((
            >>>     ('D4', 'e3'),      # intro anacrouse
            >>>     ('D4', 'e3'),
            >>>     ('D4', 'e3'),
            >>>     ('G4', 'h'),       # meas 1
            >>>     ('D5', 'h'),
            >>>     ('C5', 'e3'),      # meas 2
            >>>     ('B4', 'e3'),
            >>>     ('A4', 'e3'),
            >>>     ('G5', 'h'),
            >>>     ('D5', 'q'),
            >>>     ('C5', 'e3'),      # meas 3
            >>>     ('B4', 'e3'),
            >>>     ('A4', 'e3'),
            >>>     ('G5', 'h'),
            >>>     ('D5', 'q'),
            >>>     ('C5', 'e3'),      # meas 4
            >>>     ('B4', 'e3'),
            >>>     ('C5', 'e3'),
            >>>     ('A4', 'h.'),
            >>> ))

        .. important::

            Only 4/4 signature songs are supported with respect to note durations.

        :param iterable[tuple(string, string)] song: the song
        :param int tempo: the song tempo, given in quarters per minute
        :param float delay: delay between notes (in seconds)

        :return: the spawn subprocess from ``subprocess.Popen``

        :raises ValueError: if invalid note in song or invalid play parameters
        """
        if tempo <= 0:
            raise ValueError('invalid tempo (%s)' % tempo)
        if delay < 0:
            raise ValueError('invalid delay (%s)' % delay)

        delay_ms = int(delay * 1000)
        meas_duration_ms = 60000 / tempo * 4       # we only support 4/4 bars, hence "* 4"

        def beep_args(note, value):
            """ Builds the arguments string for producing a beep matching
            the requested note and value.

            Args:
                note (str): the note note and octave
                value (str): the note value expression
            Returns:
                str: the arguments to be passed to the beep command
            """
            freq = self._NOTE_FREQUENCIES[note.upper()]
            if '/' in value:
                base, factor = value.split('/')
                duration_ms = meas_duration_ms * self._NOTE_VALUES[base] / float(factor)
            elif '*' in value:
                base, factor = value.split('*')
                duration_ms = meas_duration_ms * self._NOTE_VALUES[base] * float(factor)
            elif value.endswith('.'):
                base = value[:-1]
                duration_ms = meas_duration_ms * self._NOTE_VALUES[base] * 1.5
            elif value.endswith('3'):
                base = value[:-1]
                duration_ms = meas_duration_ms * self._NOTE_VALUES[base] * 2 / 3
            else:
                duration_ms = meas_duration_ms * self._NOTE_VALUES[value]

            return '-f %d -l %d -D %d' % (freq, duration_ms, delay_ms)

        try:
            return self.beep(' -n '.join(
                [beep_args(note, value) for (note, value) in song]
            ))
        except KeyError as e:
            raise ValueError('invalid note (%s)' % e)

    #: Note frequencies.
    #:
    #: This dictionary gives the rounded frequency of a note specified by its
    #: standard US abbreviation and its octave number (e.g. ``C3``).
    #: Alterations use the ``#`` and ``b`` symbols, respectively for
    #: *sharp* and *flat*, between the note code and the octave number (e.g. ``D#4``, ``Gb5``).
    _NOTE_FREQUENCIES = _make_scales((
        ('C0', 16.35),
        ('C#0/Db0', 17.32),
        ('D0', 18.35),
        ('D#0/Eb0', 19.45),     # expanded in one entry per symbol by _make_scales
        ('E0', 20.60),
        ('F0', 21.83),
        ('F#0/Gb0', 23.12),
        ('G0', 24.50),
        ('G#0/Ab0', 25.96),
        ('A0', 27.50),
        ('A#0/Bb0', 29.14),
        ('B0', 30.87),
        ('C1', 32.70),
        ('C#1/Db1', 34.65),
        ('D1', 36.71),
        ('D#1/Eb1', 38.89),
        ('E1', 41.20),
        ('F1', 43.65),
        ('F#1/Gb1', 46.25),
        ('G1', 49.00),
        ('G#1/Ab1', 51.91),
        ('A1', 55.00),
        ('A#1/Bb1', 58.27),
        ('B1', 61.74),
        ('C2', 65.41),
        ('C#2/Db2', 69.30),
        ('D2', 73.42),
        ('D#2/Eb2', 77.78),
        ('E2', 82.41),
        ('F2', 87.31),
        ('F#2/Gb2', 92.50),
        ('G2', 98.00),
        ('G#2/Ab2', 103.83),
        ('A2', 110.00),
        ('A#2/Bb2', 116.54),
        ('B2', 123.47),
        ('C3', 130.81),
        ('C#3/Db3', 138.59),
        ('D3', 146.83),
        ('D#3/Eb3', 155.56),
        ('E3', 164.81),
        ('F3', 174.61),
        ('F#3/Gb3', 185.00),
        ('G3', 196.00),
        ('G#3/Ab3', 207.65),
        ('A3', 220.00),
        ('A#3/Bb3', 233.08),
        ('B3', 246.94),
        ('C4', 261.63),
        ('C#4/Db4', 277.18),
        ('D4', 293.66),
        ('D#4/Eb4', 311.13),
        ('E4', 329.63),
        ('F4', 349.23),
        ('F#4/Gb4', 369.99),
        ('G4', 392.00),
        ('G#4/Ab4', 415.30),
        ('A4', 440.00),
        ('A#4/Bb4', 466.16),
        ('B4', 493.88),
        ('C5', 523.25),
        ('C#5/Db5', 554.37),
        ('D5', 587.33),
        ('D#5/Eb5', 622.25),
        ('E5', 659.25),
        ('F5', 698.46),
        ('F#5/Gb5', 739.99),
        ('G5', 783.99),
        ('G#5/Ab5', 830.61),
        ('A5', 880.00),
        ('A#5/Bb5', 932.33),
        ('B5', 987.77),
        ('C6', 1046.50),
        ('C#6/Db6', 1108.73),
        ('D6', 1174.66),
        ('D#6/Eb6', 1244.51),
        ('E6', 1318.51),
        ('F6', 1396.91),
        ('F#6/Gb6', 1479.98),
        ('G6', 1567.98),
        ('G#6/Ab6', 1661.22),
        ('A6', 1760.00),
        ('A#6/Bb6', 1864.66),
        ('B6', 1975.53),
        ('C7', 2093.00),
        ('C#7/Db7', 2217.46),
        ('D7', 2349.32),
        ('D#7/Eb7', 2489.02),
        ('E7', 2637.02),
        ('F7', 2793.83),
        ('F#7/Gb7', 2959.96),
        ('G7', 3135.96),
        ('G#7/Ab7', 3322.44),
        ('A7', 3520.00),
        ('A#7/Bb7', 3729.31),
        ('B7', 3951.07),
        ('C8', 4186.01),
        ('C#8/Db8', 4434.92),
        ('D8', 4698.63),
        ('D#8/Eb8', 4978.03),
        ('E8', 5274.04),
        ('F8', 5587.65),
        ('F#8/Gb8', 5919.91),
        ('G8', 6271.93),
        ('G#8/Ab8', 6644.88),
        ('A8', 7040.00),
        ('A#8/Bb8', 7458.62),
        ('B8', 7902.13)
    ))

    #: Common note values.
    #:
    #: See https://en.wikipedia.org/wiki/Note_value
    #:
    #: This dictionary provides the multiplier to be applied to de whole note duration
    #: to obtain subdivisions, given the corresponding symbolic identifier:
    #:
    #:  = ===============================
    #:  w whole note (UK: semibreve)
    #:  h half note (UK: minim)
    #:  q quarter note (UK: crotchet)
    #:  e eight note (UK: quaver)
    #:  s sixteenth note (UK: semiquaver)
    #:  = ===============================
    #:
    #:
    #: Triplets can be obtained by dividing the corresponding reference by 3.
    #: For instance, the note value of a eight triplet will be ``NOTE_VALUE['e'] / 3``.
    #: It is simpler however to user the ``3`` modifier of notes, as supported by the
    #: :py:meth:`Sound.play_song` method.
    _NOTE_VALUES = {
        'w': 1.,
        'h': 1./2,
        'q': 1./4,
        'e': 1./8,
        's': 1./16,
    }
