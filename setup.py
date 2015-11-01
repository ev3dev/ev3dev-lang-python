from setuptools import setup
from git_version import git_version


setup(
    name='python-ev3dev',
    version=git_version(),
    description='Python language bindings for ev3dev',
    author='Ralph Hempel et al - See ev3dev.py for credits',
    author_email='rhempel@hempeldesigngroup.com',
    license='MIT',
    url='https://github.com/rhempel/ev3dev-lang-python',
    include_package_data=True,
    py_modules=['ev3dev'],
    install_requires=['pil']
    )

