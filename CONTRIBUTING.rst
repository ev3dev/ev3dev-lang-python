Contributing to the Python language bindings for ev3dev
=======================================================

This repository holds the pure Python bindings for peripheral
devices that use the drivers available in the ev3dev_ distribution.
for embedded systems.

Contributions are welcome in the form of pull requests - but please
take a moment to read our suggestions for a happy maintainer (me) and
even happier users.

The ``master`` branch
---------------------

This is where the latest tagged version lives - it changes whenever
we release a tag that gets released.

The ``develop`` branch
----------------------

This is the branch that is undergoing active development intended
for the next tagged version that gets released to ``master``.

Please make sure that your pull requests are against the
``develop`` branch.

Before you issue a Pull Request
-------------------------------

This is a hobby for me, I get no compensation for the work I do
on this repo or any other contributions to ev3dev_. That does not
make me special, it's the same situation that everyone involved
in the project is in.

Therefore, do not count on me to test your PR before I do the 
merge - I will certainly review the code and if it looks OK I will
just merge automatically.

I would ask that you have at least tested your changes by running
a test script on your target of choice as the generic ``robot`` user
that is used by the ``Brickman`` UI for ev3dev_.

Please do not run as ``root`` or your own user that may have group
memberships or special privileges not enjoyed by ``robot``.

If your change breaks or changes an API
---------------------------------------

Breaking changes are discouraged, but sometimes they are necessary. A
more common change is to add a new function or property to a class.

Either way, if it's more than a bug fix, please add enough text to the
comments in the pull request message so that I can paste it into the
draft release notes that I keep running for the next release out of
master.

If your change addresses an Issue
---------------------------------

Bug fixes are always welcome, especially if they are against known 
issues!

When you send a pull request that addresses an issue, please add a 
note something like ``Fixes #24`` in the PR so that we get linkage
back to the specific issue.

.. _ev3dev: http://ev3dev.org

