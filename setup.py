from setuptools import setup
from git_version import git_version


setup(
    name='python-ev3dev',
    version=git_version(),
    description='Python language bindings for ev3dev',
    author='Ralph Hempel',
    author_email='rhempel@hempeldesigngroup.com',
    license='MIT',
    url='https://github.com/rhempel/ev3dev-lang-python',
    include_package_data=True,
    packages=['ev3dev', 'ev3dev.fonts'],
    package_data={'': ['*.pil', '*.pbm']},
    install_requires=['Pillow']
    )

