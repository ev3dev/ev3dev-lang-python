from setuptools import setup
from git_version import git_version


setup(
    name='python-ev3dev',
    version=git_version(),
    description='Python language bindings for ev3dev',
    author='Ralph Hempel/Denis Demidov/Anton Vanhoucke',
    license='MIT',
    url='https://github.com/rhempel/ev3dev-lang-python',
    include_package_data=True,
    py_modules=['ev3dev']
    )

