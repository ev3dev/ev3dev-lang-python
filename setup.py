from setuptools import setup
from git_version import git_version
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='python-ev3dev2',
    version=git_version(),
    description='v2.x Python language bindings for ev3dev',
    author='ev3dev Python team',
    author_email='python-team@ev3dev.org',
    license='MIT',
    url='https://github.com/ev3dev/ev3dev-lang-python',
    include_package_data=True,
    long_description=long_description,
    long_description_content_type='text/x-rst',
    packages=['ev3dev2',
              'ev3dev2.fonts',
              'ev3dev2.sensor',
              'ev3dev2.control',
              'ev3dev2._platform'],
    package_data={'': ['*.pil', '*.pbm']},
    install_requires=['Pillow']
    )
