Contributing to the Python language bindings for ev3dev
=======================================================

This repository holds the Python bindings for ev3dev_, ev3dev-lang-python.

Opening issues
--------------

Please make sure you have read the FAQ_. If you are still encountering your
problem, open an issue, and ensure that the questions asked by the issue
template are completely answered with correct info. This will make it much
easier for us to help you!

Submitting Pull Requests
------------------------

Contributions are welcome in the form of pull requests - but please
take a moment to read our suggestions for happy maintainers and
even happier users.

Sometimes, it isn't easy for us to pull your suggested change and run
rigorous testing on it. So please help us out by validating your changes
and mentioning what kinds of testing you did when you open your PR.
Please also consider adding relevant tests to ``api_tests.py`` and documentation
changes within the ``docs`` directory.

The ``ev3dev-stretch`` branch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is where the latest version of our library lives. It targets
``ev3dev-stretch``, which is the current stable version of ev3dev.
We publish releases from this branch.

If your change breaks or changes an API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Breaking changes are discouraged, but sometimes they are necessary. A
more common change is to add a new function or property to a class.
If you add a new parameter to an existing function, give it a default value
so as not to break existing code that calls the function.

Either way, if it's more than a bug fix, please add enough text to the
comments in the pull request message so that we know what was updated
and can easily discuss the breaking change and add it to the release
notes.

If your change addresses an Issue
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Bug fixes are always welcome, especially if they are against known
issues!

When you send a pull request that addresses an issue, please add a
note of the format ``Fixes #24`` in the PR so that the PR links back
to its relevant issue and will automatically close the issue when the
PR is merged.

Building and testing changes on the EV3
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In an SSH terminal window with an EV3 with Internet access,
run the following commands:
(recall that the default ``sudo`` password is ``maker``)

```shell
git clone https://github.com/ev3dev/ev3dev-lang-python.git
cd ev3dev-lang-python
sudo make install
```

To update the module, use the following commands:

```shell
cd ev3dev-lang-python
git pull
sudo make install
```

If you are developing micropython support, you can take a shortcut
and use the following command to build and deploy the micropython
files only:

```shell
cd ev3dev-lang-python
sudo make micropython-install
```

To re-install the latest release, use the following command:

```shell
sudo apt-get --reinstall install python3-ev3dev2
```

Or, to update your current ev3dev2 to the latest release, use the
following commands:

```shell
sudo apt update
sudo apt install --only-upgrade micropython-ev3dev2
```

.. _ev3dev: http://ev3dev.org
.. _FAQ: https://python-ev3dev.readthedocs.io/en/ev3dev-stretch/faq.html