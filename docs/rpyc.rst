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

.. _RPyC: http://rpyc.readthedocs.io/
