Contributing to the Python language bindings for ev3dev
=======================================================

This repository holds the pure Python bindings for peripheral
devices that use the drivers available in the ev3dev_ distribution.
for embedded systems.

Contributions are welcome in the form of pull requests - but please
take a moment to read our suggestions for happy maintainers and
even happier users.

The ``ev3dev-stretch`` branch
---------------------

This is where the latest version of our library lives. It targets
`ev3dev-stretch`, which is currently considered a beta. Nonetheless,
it is very stable and isn't expected to have significant breaking
changes. We publish releases from this branch.

Before you issue a Pull Request
-------------------------------

Sometimes, it isn't easy for us to pull your suggested change and run
rigorous testing on it. So please help us out by validating your changes
and mentioning what kinds of testing you did when you open your PR.
Please also consider adding relevant tests to `api_tests.py`.

If your change breaks or changes an API
---------------------------------------

Breaking changes are discouraged, but sometimes they are necessary. A
more common change is to add a new function or property to a class.

Either way, if it's more than a bug fix, please add enough text to the
comments in the pull request message so that we know what was updated
and can easily discuss the breaking change and add it to the release
notes.

If your change addresses an Issue
---------------------------------

Bug fixes are always welcome, especially if they are against known 
issues!

When you send a pull request that addresses an issue, please add a 
note of the format ``Fixes #24`` in the PR so that the PR links back
to its relevant issue and will automatically close the issue when the
PR is merged.

.. _ev3dev: http://ev3dev.org

