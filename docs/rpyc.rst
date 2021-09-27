**************
RPyC on ev3dev
**************

`RPyC_ <https://rpyc.readthedocs.io/en/latest/>`_ (pronounced as are-pie-see) can be used to:
* run a python program on an ev3dev device that controls another ev3dev device.
This is more commonly known as daisy chaining.
* run a python program on your laptop that controls an ev3dev device. This can be
useful if your robot requires CPU intensive code that would be slow to run on the
EV3. A good example of this is a Rubik's cube solver, calculating the solution to
solve a Rubik's cube can be slow on an EV3.

For both of these scenarios you can use RPyC to control multiple remote ev3dev devices.


Networking
==========
You will need IP connectivity between the device where your python code runs
(laptop, an ev3dev device, etc) and the remote ev3dev devices. Some common scenarios
might be:
* Multiple EV3s on the same WiFi network
* A laptop and an EV3 on the same WiFi network
* A bluetooth connection between two EV3s

The `ev3dev networking documentation <https://www.ev3dev.org/docs/networking/>`_ should get
you up and running in terms of networking connectivity.


Install
=======

1. RPyC is installed on ev3dev but we need to create a service that launches
   ``rpyc_classic.py`` at bootup. `SSH <http://www.ev3dev.org/docs/tutorials/connecting-to-ev3dev-with-ssh/>`_ to your remote ev3dev devices and
   cut-n-paste the following commands at the bash prompt.

   .. code-block:: shell

      echo "[Unit]
      Description=RPyC Classic Service
      After=multi-user.target

      [Service]
      User=robot
      Type=simple
      ExecStart=/usr/bin/rpyc_classic.py

      [Install]
      WantedBy=multi-user.target" > rpyc-classic.service --host=0.0.0.0

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
We will run code on our laptop to control the remote ev3dev device with IP
address X.X.X.X. The goal is to have the LargeMotor connected to ``OUTPUT_A``
run when the TouchSensor on ``INPUT_1`` is pressed.

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
* RPyC is lightweight and only requires an IP connection (no ssh required).
* Some robots may need much more computational power than an EV3 can give
  you. A notable example is the Rubik's cube solver.

Cons
====
* Latency will be introduced by the network connection.  This may be a show stopper for robots where reaction speed is essential.
* RPyC is only supported by python, it is *NOT* supported by micropython
* The version included with ev3dev is 3.3.0; if using a RPyC client on a desktop chances are there is a major difference, so it is
  advisable to upgrade it:
 - sudo apt-get install python3-pip
 - sudo pip3 install rpyc
 - sudo reboot

References
==========
* `RPyC <http://rpyc.readthedocs.io/>`_
* `sourceforge page <http://sourceforge.net/projects/rpyc/files/main>`_
* `Download and Install <http://rpyc.readthedocs.io/en/latest/install.html>`_
* `connect with SSH <http://www.ev3dev.org/docs/tutorials/connecting-to-ev3dev-with-ssh/>`_
