import RPi.GPIO as GPIO
from darkroomtimer import consts
from darkroomtimer.beeper import Beeper
from darkroomtimer.display import Display
from darkroomtimer.kernel import Kernel
from darkroomtimer.lights import Lights

if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)

    display = Display()
    display.run_in_background()

    beeper = Beeper(consts.BEEPER_CHANNEL)
    beeper.run_in_background()

    lights = Lights(consts.DEVELOP_LIGHT_CHANNEL, consts.STOP_LIGHT_CHANNEL, consts.FIX_LIGHT_CHANNEL)
    lights.run_in_background()
    
    kernel = Kernel(display, beeper, lights)

    print("Ready")

    kernel.run()
