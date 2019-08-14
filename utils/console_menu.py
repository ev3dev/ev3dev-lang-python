#!/usr/bin/env micropython
from time import sleep
from sys import stderr
from os import listdir
from ev3dev2.button import Button
from ev3dev2.console import Console
from ev3dev2.led import Leds
from ev3dev2.sensor import list_sensors, INPUT_1, INPUT_2, INPUT_3, INPUT_4


"""
Used to create a console menu for switching between programs quickly
without having to return to Brickman to find and launch a program.
Demonstrates the EV3DEV2 Console(), Led(), and Button() classes.

"""


def get_positions(console):
    """
    Compute a dictionary keyed by button names with horizontal alignment,
    and column/row location to show each choice on the EV3 LCD console.

    Parameter:

    - `console` (Console): an instance of the EV3 Console() class

    returns a dictionary keyed by button names with column/row location
    """

    midrow = 1 + console.rows // 2
    midcol = 1 + console.columns // 2
    # horiz_alignment, col, row
    return {
        "up": ("C", midcol, 1),
        "right": ("R", console.columns, midrow),
        "down": ("C", midcol, console.rows),
        "left": ("L", 1, midrow),
        "enter": ("C", midcol, midrow)
    }


def wait_for_button_press(button):
    """
    Wait for a button to be pressed and released.

    Parameter:

    - `button` (Button): an instance of the EV3 Button() class

    return the Button name that was pressed.
    """
    pressed = None
    while True:
        allpressed = button.buttons_pressed
        if bool(allpressed):
            pressed = allpressed[0]  # just get the first one
            while not button.wait_for_released(pressed):
                pass
            break
    return pressed


def menu(choices, before_run_function=None, after_run_function=None):
    """
    Console Menu that accepts choices and corresponding functions to call.
    The user must press the same button twice: once to see their choice highlited,
    a second time to confirm and run the function. The EV3 LEDs show each state change:
    Green = Ready for button, Amber = Ready for second button, Red = Running

    Parameters:

    - `choices` a dictionary of tuples "button-name": ("mission-name", function-to-call)
        Example:
            choices = {
                # "button-name": ("mission-name", function-to-call)
                # or "button-name": ("mission-name", lambda: call(x, y, z))
                "enter": ("CAL", lambda: auto_calibrate(robot, 1.0)),
                "up": ("MI2", fmission2),
                "right": ("MI3", fmission3),
                "down": ("MI4", fmission4),
                "left": ("MI5", fmission5)
            }
        where fmission2, fmission3 are functions;
        note don't call them with parentheses, unless preceded by lambda: to defer the call
    - `before_run_function` when not None, call this function before each mission run, passed with mission-name
    - `after_run_function` when not None, call this function after each mission run, passed with mission-name
    """

    console = Console()
    leds = Leds()
    button = Button()

    leds.all_off()
    leds.set_color("LEFT", "GREEN")
    leds.set_color("RIGHT", "GREEN")
    menu_positions = get_positions(console)

    last = None  # the last choice--initialize to None

    while True:
        # display the menu of choices, but show the last choice in inverse
        console.reset_console()
        for btn, (name, _) in choices.items():
            align, col, row = menu_positions[btn]
            console.text_at(name, col, row, inverse=(btn == last), alignment=align)

        pressed = wait_for_button_press(button)

        # get the choice for the button pressed
        if pressed in choices:
            if last == pressed:   # was same button pressed?
                console.reset_console()
                leds.set_color("LEFT", "RED")
                leds.set_color("RIGHT", "RED")

                # call the user's subroutine to run the mission, but catch any errors
                try:
                    name, mission_function = choices[pressed]
                    if before_run_function is not None:
                        before_run_function(name)
                    mission_function()
                except Exception as ex:
                    print("**** Exception when running")
                    print(ex)
                finally:
                    if after_run_function is not None:
                        after_run_function(name)
                    last = None
                    leds.set_color("LEFT", "GREEN")
                    leds.set_color("RIGHT", "GREEN")
            else:   # different button pressed
                last = pressed
                leds.set_color("LEFT", "AMBER")
                leds.set_color("RIGHT", "AMBER")


if __name__ == "__main__":

    # This is the main program to demonstrate the console menu logic above.
    #
    # Define functions that represent different missions
    # Note: these can be imported from different modules (files)
    # and use lambda notation to defer the function call
    # i.e. lambda : call(a, b, c)

    def calibrate():
        """ Placeholder for call to your calibration logic to set the black and white values for your color sensors """
        print("calibrating...")
        sleep(1)

    def show_sensors(iterations):
        """ Show the EV3 sensors, current mode and value """
        sensors = list(list_sensors(address=[INPUT_1, INPUT_2, INPUT_3]))   # , INPUT_4
        for _ in range(iterations):
            for sensor in sensors:
                print("{} {}: {}".format(sensor.address, sensor.mode, sensor.value()))
                sleep(.5)
        sleep(10)

    def mission1():
        print("mission 1...")
        sleep(1)

    def mission2():
        print("mission 2...")
        sleep(1)

    def mission3():
        print("mission 3...")
        sleep(1)
        # for testing when a function generates an error
        raise Exception('Raised error')

    # Define the functions to be called before and after each run.
    # Functions will be called with the mission_name as the argument.
    # Useful for resetting motor positions between runs, etc.

    def before(mission_name):
        print("before " + mission_name)

    def after(mission_name):
        print("after " + mission_name)
        sleep(1)

    # Define the buttons, mission names, functions for the console menu.
    # Key is the button assignment: one of "enter", "up", "right", "down", "left"
    # Note the "backspace" button interrupts the program and returns to Brickman
    # Example:
    # CHOICES = {
    #     # "button-name": ("mission-name", function-to-call)
    #     # or "button-name": ("mission-name", lambda: call(x, y, z))
    #     "up": ("MI1", mission1),
    #     "right": ("MI2", mission2),
    #     "left": ("MI3", mission3),
    #     "down": ("SHOW", lambda: show_sensors(5)),
    #     "enter": ("CAL", calibrate)
    # }
    # menu(CHOICES, before_run_function=before, after_run_function=after)

    CHOICES = {
        "up": ("MI1", mission1),
        "right": ("MI2", mission2),
        "left": ("MI3", mission3),
        "down": ("SHOW", lambda: show_sensors(5)),
        "enter": ("CAL", calibrate)
    }

    menu(CHOICES, before_run_function=before, after_run_function=after)
