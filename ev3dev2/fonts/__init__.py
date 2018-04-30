import os.path
from glob import glob
from PIL import ImageFont

def available():
    """
    Returns list of available font names.
    """
    font_dir = os.path.dirname(__file__)
    names = [os.path.basename(os.path.splitext(f)[0])
            for f in glob(os.path.join(font_dir, '*.pil'))]
    return sorted(names)

def load(name):
    """
    Loads the font specified by name and returns it as an instance of
    `PIL.ImageFont <http://pillow.readthedocs.io/en/latest/reference/ImageFont.html>`_
    class.
    """
    try:
        font_dir = os.path.dirname(__file__)
        pil_file = os.path.join(font_dir, '{}.pil'.format(name))
        pbm_file = os.path.join(font_dir, '{}.pbm'.format(name))
        return ImageFont.load(pil_file)
    except FileNotFoundError:
        raise Exception('Failed to load font "{}". '.format(name) +
        'Check ev3dev.fonts.available() for the list of available fonts')
