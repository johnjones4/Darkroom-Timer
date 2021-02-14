import RPi.GPIO as GPIO
from threading import Thread, Lock
import time

LIGHT_MODE_OFF = 0
LIGHT_MODE_ON = 1
LIGHT_MODE_BLINK = 2

LIGHT_DEVELOP = 0
LIGHT_STOP = 1
LIGHT_FIX = 2

class Lights:
    def __init__(self, develop_pin, stop_pin, fix_pin):
        for pin in [develop_pin, stop_pin, fix_pin]:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        self.pin_map = {
            LIGHT_DEVELOP: develop_pin,
            LIGHT_STOP: stop_pin,
            LIGHT_FIX: fix_pin
        }
        self.modes = {
            LIGHT_DEVELOP: LIGHT_MODE_OFF,
            LIGHT_STOP: LIGHT_MODE_OFF,
            LIGHT_FIX: LIGHT_MODE_OFF
        }
        self.lock = Lock()


    def clear_modes(self):
        for light in [LIGHT_DEVELOP, LIGHT_STOP, LIGHT_FIX]:
            self.set_light_mode(light, LIGHT_MODE_OFF)


    def set_light_mode(self, light, mode):
        with self.lock:
            self.modes[light] = mode
            pin = self.pin_map[light]
            if mode == LIGHT_MODE_OFF:
                GPIO.output(pin, GPIO.LOW)
            elif mode == LIGHT_MODE_ON:
                GPIO.output(pin, GPIO.HIGH)


    def run(self):
        blink_on = True
        while True:
            with self.lock:
                for light in self.modes:
                    if self.modes[light] == LIGHT_MODE_BLINK:
                        pin = self.pin_map[light]
                        GPIO.output(pin, GPIO.HIGH if blink_on else GPIO.LOW)
            blink_on = not blink_on
            time.sleep(0.3)


    def run_in_background(self):
        thread = Thread(
            target=self.run,
            daemon=True,
        )
        thread.start()
        return thread
