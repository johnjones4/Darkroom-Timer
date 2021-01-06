import RPi.GPIO as GPIO
from darkroomtimer import consts
from darkroomtimer.beeper import Beeper
from darkroomtimer.display import Display
from darkroomtimer.kernel import Kernel

if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)

    display = Display()
    display.run_in_background()

    beeper = Beeper(consts.BEEPER_CHANNEL)
    beeper.run_in_background()
    
    kernel = Kernel(display, beeper)
    kernel.run()
