**************
RPyC on ev3dev
**************

`RPyC_ <https://rpyc.readthedocs.io/en/latest/>`_ (pronounced as are-pie-see), or Remote Python Call, is a transparent
python library for symmetrical remote procedure calls, clustering and
distributed-computing. RPyC makes use of object-proxying, a technique that
employs python’s dynamic nature, to overcome the physical boundaries between
processes and computers, so that remote objects can be manipulated as if they
were local.

For ev3dev, RPyC is most often used for:
* robots that involve more than one EV3 (i.e. daisy chaining)
* robots that perform some CPU intensive task (ex: Rubik's cube solver) where you
  wish to run the CPU intensive part on your desktop PC

Networking
==========
You will need to setup networking on your ev3dev device(s). The
`ev3dev networking documentation <https://www.ev3dev.org/docs/networking/>`_ should get
you up and running in terms of networking connectivity.


Install
=======

1. RPyC is installed on ev3dev but we need to create a service that launches
   ``rpyc_classic.py`` at bootup. Cut-n-paste the following commands on the
   ev3dev device(s) that you wish to control via RPyC.

   .. code-block:: shell

      echo "[Unit]
      Description=RPyC Classic Service
      After=multi-user.target

      [Service]
      Type=simple
      ExecStart=/usr/bin/rpyc_classic.py

      [Install]
      WantedBy=multi-user.target" > rpyc-classic.service

      sudo cp rpyc-classic.service /lib/systemd/system/
      sudo systemctl daemon-reload
      sudo systemctl enable rpyc-classic.service
      sudo systemctl start rpyc-classic.service


2. If you will be using an ev3dev device to control another ev3dev device you
   can skip this step.  If you will be using your desktop PC to control an ev3dev
   device you must install RPyC on your desktop PC. How you install RPyC depends
   on your operating system. For Linux you should be able to do:

   .. code-block:: shell

       sudo apt-get install python3-rpyc

   For Windows there is a win32 installer on the project's `sourceforge page`_.
   Also, have a look at the `Download and Install`_ page on their site.

Example
=======
The following python script should make a large motor connected to ``OUTPUT_A``
run while the touch sensor on ``INPUT_1`` is pressed.

   .. code-block:: py

       import rpyc

       # Create a RPyC connection to the remote ev3dev device.
       # Use the hostname or IP address of the ev3dev device.
       # If this fails, verify your IP connectivty via ``ping X.X.X.X``
       conn = rpyc.classic.connect('X.X.X.X')

       # import ev3dev2 on the remote ev3dev device
       ev3dev2_motor = conn.modules['ev3dev2.motor']
       ev3dev2_sensor = conn.modules['ev3dev2.sensor']
       ev3dev2_sensor_lego = conn.modules['ev3dev2.sensor.lego']

       # Use the LargeMotor and TouchSensor on the remote ev3dev device
       motor = ev3dev2_motor.LargeMotor(ev3dev2_motor.OUTPUT_A)
       ts = ev3dev2_sensor_lego.TouchSensor(ev3dev2_sensor.INPUT_1)

       # If the TouchSensor is pressed, run the motor
       while True:
           ts.wait_for_pressed()
           motor.run_forever(speed_sp=200)

           ts.wait_for_released()
           motor.stop()


Pros
====
* The RPyC server is lightweight and only requires an IP connection (no ssh required).
* Some robots may need much more computational power than an EV3 can give
  you. A notable example is the Rubik's cube solver. There is an algorithm that
  provides an almost optimal solution (in terms of number of cube rotations), but
  it takes more RAM than is available on EV3. With RPyC, you could run the
  heavy-duty computations on your desktop.

Cons
====
The most obvious *disadvantage* is latency introduced by network connection.
This may be a show stopper for robots where reaction speed is essential.

References
==========
* `RPyC <http://rpyc.readthedocs.io/>`_
* `sourceforge page <http://sourceforge.net/projects/rpyc/files/main>`_
* `Download and Install <http://rpyc.readthedocs.io/en/latest/install.html>`_
* `connect with SSH <http://www.ev3dev.org/docs/tutorials/connecting-to-ev3dev-with-ssh/>`_
