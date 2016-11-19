import pkg_resources
import os.path
from PIL import ImageFont

def available():
    """
    Returns list of available font names.
    """
    names = []
    for f in pkg_resources.resource_listdir('ev3dev.fonts', ''):
        name, ext = os.path.splitext(os.path.basename(f))
        if ext == '.pil':
            names.append(name)
    return sorted(names)

def load(name):
    """
    Loads the font specified by name and returns it as an instance of
    `PIL.ImageFont <http://pillow.readthedocs.io/en/latest/reference/ImageFont.html>`_
    class.
    """
    try:
        pil_file = pkg_resources.resource_filename('ev3dev.fonts', '{}.pil'.format(name))
        pbm_file = pkg_resources.resource_filename('ev3dev.fonts', '{}.pbm'.format(name))
        return ImageFont.load(pil_file)
    except FileNotFoundError:
        raise Exception('Failed to load font "{}". '.format(name) +
        'Check ev3dev.fonts.available() for the list of available fonts')
