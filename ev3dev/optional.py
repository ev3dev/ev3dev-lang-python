"""
A set of optional modules for interfacing with peripherals (screen and sound)
"""

import sys
optional_enabled = sys.implementation.name is not 'micropython'

if optional_enabled:
    from subprocess import Popen, check_output, PIPE
    import mmap
    import ctypes

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

    if optional_enabled:
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


class Screen(FbMem):
    """
    A convenience wrapper for the FbMem class.
    Provides drawing functions from the python imaging library (PIL).
    """

    def __init__(self):
        if not optional_enabled:
            raise NotImplementedError("The screen module isn't supported on your Python implementation.")
        
        from PIL import Image, ImageDraw
        FbMem.__init__(self)

        self._img = Image.new(
                self.var_info.bits_per_pixel == 1 and "1" or "RGB",
                (self.fix_info.line_length * 8 // self.var_info.bits_per_pixel, self.yres),
                "white")

        self._draw = ImageDraw.Draw(self._img)

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
            self.mmap[:] = self._img.tobytes("raw", "1;IR")
        elif self.var_info.bits_per_pixel == 16:
            self.mmap[:] = self._img_to_rgb565_bytes()
        else:
            raise Exception("Not supported")


def _make_scales(notes):
    """ Utility function used by Sound class for building the note frequencies table """
    res = dict()
    for note, freq in notes:
        freq = round(freq)
        for n in note.split('/'):
            res[n] = freq
    return res


class Sound:
    """
    Sound-related functions. The class has only static methods and is not
    intended for instantiation. It can beep, play wav files, or convert text to
    speech.

    Note that all methods of the class spawn system processes and return
    subprocess.Popen objects. The methods are asynchronous (they return
    immediately after child process was spawned, without waiting for its
    completion), but you can call wait() on the returned result.

    Examples::

        # Play 'bark.wav', return immediately:
        Sound.play('bark.wav')

        # Introduce yourself, wait for completion:
        Sound.speak('Hello, I am Robot').wait()

        # Play a small song
        Sound.play_song((
            ('D4', 'e3'),
            ('D4', 'e3'),
            ('D4', 'e3'),
            ('G4', 'h'),
            ('D5', 'h')
        ))
    """

    @staticmethod
    def _raise_if_unsupported():
        if not optional_enabled:
            raise NotImplementedError("The screen module isn't supported on your Python implementation.")

    channel = None

    @staticmethod
    def beep(args=''):
        """
        Call beep command with the provided arguments (if any).
        See `beep man page`_ and google `linux beep music`_ for inspiration.

        .. _`beep man page`: https://linux.die.net/man/1/beep
        .. _`linux beep music`: https://www.google.com/search?q=linux+beep+music
        """
        Sound._raise_if_unsupported()
        with open(os.devnull, 'w') as n:
            return Popen(shlex.split('/usr/bin/beep %s' % args), stdout=n)

    @staticmethod
    def tone(*args):
        """
        .. rubric:: tone(tone_sequence)

        Play tone sequence. The tone_sequence parameter is a list of tuples,
        where each tuple contains up to three numbers. The first number is
        frequency in Hz, the second is duration in milliseconds, and the third
        is delay in milliseconds between this and the next tone in the
        sequence.

        Here is a cheerful example::

            Sound.tone([
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
                ]).wait()

        .. rubric:: tone(frequency, duration)

        Play single tone of given frequency (Hz) and duration (milliseconds).
        """
        Sound._raise_if_unsupported()
        def play_tone_sequence(tone_sequence):
            def beep_args(frequency=None, duration=None, delay=None):
                args = ''
                if frequency is not None: args += '-f %s ' % frequency
                if duration  is not None: args += '-l %s ' % duration
                if delay     is not None: args += '-D %s ' % delay

                return args

            return Sound.beep(' -n '.join([beep_args(*t) for t in tone_sequence]))

        if len(args) == 1:
            return play_tone_sequence(args[0])
        elif len(args) == 2:
            return play_tone_sequence([(args[0], args[1])])
        else:
            raise Exception("Unsupported number of parameters in Sound.tone()")

    @staticmethod
    def play(wav_file):
        """
        Play wav file.
        """
        Sound._raise_if_unsupported()
        with open(os.devnull, 'w') as n:
            return Popen(shlex.split('/usr/bin/aplay -q "%s"' % wav_file), stdout=n)

    @staticmethod
    def speak(text, espeak_opts='-a 200 -s 130'):
        """
        Speak the given text aloud.
        """
        Sound._raise_if_unsupported()
        with open(os.devnull, 'w') as n:
            cmd_line = '/usr/bin/espeak --stdout {0} "{1}"'.format(espeak_opts, text)
            espeak = Popen(shlex.split(cmd_line), stdout=PIPE)
            play = Popen(['/usr/bin/aplay', '-q'], stdin=espeak.stdout, stdout=n)
            return espeak

    @staticmethod
    def _get_channel():
        """
        :return: the detected sound channel
        :rtype: str
        """
        if Sound.channel is None:
            # Get default channel as the first one that pops up in
            # 'amixer scontrols' output, which contains strings in the
            # following format:
            #
            #     Simple mixer control 'Master',0
            #     Simple mixer control 'Capture',0
            out = check_output(['amixer', 'scontrols']).decode()
            m = re.search("'(?P<channel>[^']+)'", out)
            if m:
                Sound.channel = m.group('channel')
            else:
                Sound.channel = 'Playback'

        return Sound.channel

    @staticmethod
    def set_volume(pct, channel=None):
        """
        Sets the sound volume to the given percentage [0-100] by calling
        ``amixer -q set <channel> <pct>%``.
        If the channel is not specified, it tries to determine the default one
        by running ``amixer scontrols``. If that fails as well, it uses the
        ``Playback`` channel, as that is the only channel on the EV3.
        """
        Sound._raise_if_unsupported()

        if channel is None:
            channel = Sound._get_channel()

        cmd_line = '/usr/bin/amixer -q set {0} {1:d}%'.format(channel, pct)
        Popen(shlex.split(cmd_line)).wait()

    @staticmethod
    def get_volume(channel=None):
        """
        Gets the current sound volume by parsing the output of
        ``amixer get <channel>``.
        If the channel is not specified, it tries to determine the default one
        by running ``amixer scontrols``. If that fails as well, it uses the
        ``Playback`` channel, as that is the only channel on the EV3.
        """
        Sound._raise_if_unsupported()

        if channel is None:
            channel = Sound._get_channel()

        out = check_output(['amixer', 'get', channel]).decode()
        m = re.search('\[(?P<volume>\d+)%\]', out)
        if m:
            return int(m.group('volume'))
        else:
            raise Exception('Failed to parse output of `amixer get {}`'.format(channel))

    @classmethod
    def play_song(cls, song, tempo=120, delay=50):
        """ Plays a song provided as a list of tuples containing the note name and its
        value using music conventional notation instead of numerical values for frequency
        and duration.

        It supports symbolic notes (e.g. ``A4``, ``D#3``, ``Gb5``) and durations (e.g. ``q``, ``h``).

        For an exhaustive list of accepted note symbols and values, have a look at the :py:attr:`_NOTE_FREQUENCIES`
        and :py:attr:`_NOTE_VALUES` private dictionaries in the source code.

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

        Args:
            song (iterable[tuple(str, str)]): the song
            tempo (int): the song tempo, given in quarters per minute
            delay (int): delay in ms between notes

        Returns:
            subprocess.Popen: the spawn subprocess
        """
        Sound._raise_if_unsupported()
        meas_duration = 60000 / tempo * 4

        def beep_args(note, value):
            """ Builds the arguments string for producing a beep matching
            the requested note and value.

            Args:
                note (str): the note note and octave
                value (str): the note value expression
            Returns:
                str: the arguments to be passed to the beep command
            """
            freq = Sound._NOTE_FREQUENCIES[note.upper()]
            if '/' in value:
                base, factor = value.split('/')
                duration = meas_duration * Sound._NOTE_VALUES[base] / float(factor)
            elif '*' in value:
                base, factor = value.split('*')
                duration = meas_duration * Sound._NOTE_VALUES[base] * float(factor)
            elif value.endswith('.'):
                base = value[:-1]
                duration = meas_duration * Sound._NOTE_VALUES[base] * 1.5
            elif value.endswith('3'):
                base = value[:-1]
                duration = meas_duration * Sound._NOTE_VALUES[base] * 2 / 3
            else:
                duration = meas_duration * Sound._NOTE_VALUES[value]

            return '-f %d -l %d -D %d' % (freq, duration, delay)

        return Sound.beep(' -n '.join(
            [beep_args(note, value) for note, value in song]
        ))

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


