import RPi.GPIO as GPIO
from threading import Lock, Thread
import time
from queue import Queue

class Beeper:
    def __init__(self, channel: int):
        self.channel = channel
        GPIO.setup(self.channel, GPIO.OUT)
        GPIO.output(self.channel, 0)
        self.beep_queue = Queue()


    def beep(self, length: float):
        self.beep_queue.put((True, length))


    def beeps(self, length: float, count: int):
        for _ in range(count):
            self.beep_queue.put((True, length))
            self.beep_queue.put((False, length))


    def run(self):
        while True:
            if not self.beep_queue.empty():
                (beep, length) = self.beep_queue.get()
                if beep:
                    GPIO.output(self.channel, 1)
                time.sleep(length)
                GPIO.output(self.channel, 0)
            time.sleep(0)

    def run_in_background(self):
        thread = Thread(
            target=self.run,
            daemon=True,
        )
        thread.start()
        return thread
