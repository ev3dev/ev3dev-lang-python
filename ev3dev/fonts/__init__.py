import pkg_resources
import os.path
from PIL import ImageFont

def list():
    names = []
    for f in pkg_resources.resource_listdir('ev3dev.fonts', ''):
        name, ext = os.path.splitext(os.path.basename(f))
        if ext == '.pil':
            names.append(name)
    return sorted(names)

def load(name):
    pil_file = pkg_resources.resource_filename('ev3dev.fonts', '{}.pil'.format(name))
    pbm_file = pkg_resources.resource_filename('ev3dev.fonts', '{}.pbm'.format(name))
    return ImageFont.load(pil_file)
