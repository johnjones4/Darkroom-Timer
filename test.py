import board
import pulseio
from adafruit_motor import servo
import time

pwm = pulseio.PWMOut(board.D20, frequency=50)
servo = servo.Servo(pwm, min_pulse=750, max_pulse=2250)

servo.angle = 0
time.sleep(2)
servo.angle = 90
time.sleep(2)
servo.angle = 180

