# EV3D4
EV3D4 is designed to look like R2-D2 from Star Wars. There are two options for
controlling EV3D4. The first is to use the IR remote to send commands to the IR
sensor, run EV3D4RemoteControl.py to use this method. The second means of
controlling EV3D4 is via a web browser, run EV3D4WebControl.py to use this method.
You can run both of these from the Brickman interface or if logged in via ssh
you can run them via ./EV3D4RemoteControl.py or ./EV3D4WebControl.py.

**Building instructions**: https://www.lego.com/en-us/mindstorms/build-a-robot/ev3d4

### EV3D4RemoteControl
EV3D4RemoteControl.py creates a child class of ev3dev/helper.py's
RemoteControlledTank.


### EV3D4WebControl
EV3D4WebControl creates a child class of ev3dev/webserver.py's WebControlledTank.
The WebControlledTank class runs a web server that serves the web pages,
images, etc but it also services the AJAX calls made via the client. The user
loads the initial web page at which point they choose the "Desktop interface"
or the "Mobile Interface".

Desktop Interface - The user is presented with four arrows for moving forwards,
backwards, spinning clockwise or spinning counter-clockwise. Two additional
buttons are provided for controlling the medium motor. There are two sliders,
one to control the speed of the tank and the other to control the speed of the
medium motor.

Mobile Interface - The user is presented with a virtual joystick that is used
to control the movements of the robot. Slide your thumb forward and the robot
moves forward, slide it to the right and the robot spins clockwise, etc. The
further you move the joystick towards the edge of the circle the faster the
robot moves. Buttons and a speed slider for the medium motor are also provided.

Both interfaces have touch support so you can use either Desktop or Mobile from
your smartphone. When the user clicks/touches a button some jQuery code will
fire off an AJAX call to let the EV3D4 web server know what the user clicked or
where the joystick is if using the Mobile Interface. The web server in
WebControlledTank services this AJAX call and adjust motor speed/power
accordingly.

You can see a demo of the web interface below. Note that the demo is on a
simple Tank robot, not EV3D4, but that doesn't really matter as EV3D4 is also
just a Tank robot.

**Demo Video**: https://www.youtube.com/watch?v=x5VauXr7W4A
