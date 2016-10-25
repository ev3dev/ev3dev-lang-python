Working with ev3dev remotely using RPyC
=======================================

RPyC_ (pronounced as are-pie-see), or Remote Python Call, is a transparent
python library for symmetrical remote procedure calls, clustering and
distributed-computing. RPyC makes use of object-proxying, a technique that
employs python’s dynamic nature, to overcome the physical boundaries between
processes and computers, so that remote objects can be manipulated as if they
were local. Here are simple steps you need to follow in order to install and
use RPyC with ev3dev:

1. Install RPyC both on the EV3 and on your desktop PC with the following
   command (depending on your operating system, you may need to use ``pip3`` or
   ``pip`` on the PC instead of ``easy_install3``):

   .. code-block:: shell

       sudo easy_install3 rpyc

2. Create file ``rpyc_server.sh`` with the following contents on the EV3:

   .. code-block:: shell

      #!/bin/bash
      python3 `which rpyc_classic.py`

   and make the file executable:

   .. code-block:: shell

      chmod +x rpyc_classic.py

   Launch the created file either from ssh session, or from brickman.

3. Now you are ready to connect to the RPyC server from your desktop PC:

   .. code-block:: py

       import rpyc
       conn = rpyc.classic.connect('ev3') # host name or IP address of the EV3
       ev3 = conn.modules['ev3dev.ev3']   # import ev3dev.ev3 remotely
       m = ev3.LargeMotor('outA')
       m.run_timed(time_sp=1000, speed_sp=600)

You can run scripts like this from any intercative python environment, like
ipython shell/notebook, spyder, pycharm, etc.

Some *advantages* of using RPyC with ev3dev are:

* It uses much less resources than running ipython notebook on EV3; RPyC server
  is lightweight, and only requires an IP connection to the EV3 once set up (no
  ssh required).
* The scripts you are working with are actually stored and edited on your
  desktop PC, with your favorite editor/IDE.
* Some robots may need much more computational power than what EV3 can give
  you. A notable example is the Rubics cube solver: there is an algorithm that
  provides almost optimal solution (in terms of number of cube rotations), but
  it takes more RAM than is available on EV3. With RPYC, you could run the
  heavy-duty computations on your desktop.

The most obvious *disadvantage* is latency introduced by network connection.
This may be a show stopper for robots where reaction speed is essential.

.. _RPyC: http://rpyc.readthedocs.io/
