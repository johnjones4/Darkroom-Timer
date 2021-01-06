from threading import Lock, Thread
import digitalio
import board
import adafruit_character_lcd.character_lcd as characterlcd
import time
from darkroomtimer.util import pad_spaces

class Display:
    def __init__(self):
        self.lcd = Display.init_lcd()
        self.lines = [None, None]
        self.lock = Lock()

    @classmethod
    def init_lcd(self):
        lcd_rs = digitalio.DigitalInOut(board.D26)
        lcd_en = digitalio.DigitalInOut(board.D19)
        lcd_d7 = digitalio.DigitalInOut(board.D27)
        lcd_d6 = digitalio.DigitalInOut(board.D22)
        lcd_d5 = digitalio.DigitalInOut(board.D24)
        lcd_d4 = digitalio.DigitalInOut(board.D25)
        lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, 16, 2)
        lcd.message = "Initializing ..."
        return lcd

    def update_line(self, line: int, message: str):
        with self.lock:
            self.lines[line] = pad_spaces(message, self.lcd.columns)

    def update(self, lines):
        with self.lock:
            self.lines = list(map(lambda line: pad_spaces(line, self.lcd.columns), lines))

    def run(self):
        last_lines = [None, None]
        while True:
            with self.lock:
                for i in range(len(self.lines)):
                    if self.lines[i] and self.lines[i] != last_lines[i]:
                        self.lcd.row = i
                        self.lcd.column = 0
                        self.lcd.message = self.lines[i]
                        last_lines[i] = self.lines[i]
            time.sleep(0)

    def run_in_background(self):
        thread = Thread(
            target=self.run,
            daemon=True,
        )
        thread.start()
        return thread
