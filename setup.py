from setuptools import setup
from git_version import git_version


setup(
    name='python-ev3dev2',
    version=git_version(),
    description='v2.x Python language bindings for ev3dev',
    author='ev3dev Python team',
    author_email='python-team@ev3dev.org',
    license='MIT',
    url='https://github.com/ev3dev/ev3dev-lang-python',
    include_package_data=True,
    packages=['ev3dev2',
              'ev3dev2.fonts',
              'ev3dev2.sensor',
              'ev3dev2.control',
              'ev3dev2._platform'],
    package_data={'': ['*.pil', '*.pbm']},
    install_requires=['Pillow']
    )
