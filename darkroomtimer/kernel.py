from darkroomtimer.beeper import Beeper
from darkroomtimer.display import Display
from darkroomtimer.menu import Menu
from darkroomtimer.timer_set import TimerSet
from darkroomtimer.active_timer import ActiveTimer
from darkroomtimer import consts
from threading import Lock
import time
import RPi.GPIO as GPIO

class Kernel:
    def __init__(self, display: Display, beeper: Beeper):
        self.init_buttons()
        self.display = display
        self.beeper = beeper
        self.menu = Menu(lambda ts: self.goto_timer_mode(ts))
        self.timer_set = None
        self.active_timer = None
        self.needs_render = False
        self.interrupt_lock = Lock()
        self.last_scroll_chanel = None
        self.render_flag = True
        self.render_flag_lock = Lock()


    def run(self):
        while True:
            with self.interrupt_lock:
                if self.active_timer and not self.active_timer.step_and_render(self.beeper, self.display):
                    self.active_timer = None
                    self.set_render_flag()
                        
            with self.render_flag_lock:
                if self.render_flag:
                    if self.timer_set:
                        if self.timer_set.is_empty():
                            self.timer_set = None
                            self.active_timer = None
                            self.menu.render(self.display)
                        else:
                            self.timer_set.render(self.display)
                    elif self.is_in_menu_mode():
                        self.menu.render(self.display)
                    self.render_flag = False

            time.sleep(0)


    def init_buttons(self):
        channels = [
            (consts.SCROLL_SELECT_CHANNEL, self.handle_select_button, GPIO.RISING, 500),
            (consts.BACK_CHANNEL, self.handle_back_button, GPIO.RISING, 500),
            (consts.TIMER_START_CHANNEL, self.handle_timer_button, GPIO.RISING, 500),
            (consts.SCROLL_A_CHANNEL, self.handle_scroll_pulse, GPIO.RISING, None),
            (consts.SCROLL_B_CHANNEL, self.handle_scroll_pulse, GPIO.RISING, None)
        ]
        for (channel, callback, mode, bouncetime) in channels:
            GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            if bouncetime:
                GPIO.add_event_detect(channel, mode, callback=callback, bouncetime=bouncetime)
            else:
                GPIO.add_event_detect(channel, mode, callback=callback)


    def is_in_menu_mode(self):
        return self.timer_set is None and self.active_timer is None

    
    def set_render_flag(self):
        with self.render_flag_lock:
            self.render_flag = True


    def goto_timer_mode(self, timer_set: TimerSet):
        self.timer_set = timer_set
        self.set_render_flag()


    def handle_select_button(self, channel):
        with self.interrupt_lock:
            if self.is_in_menu_mode():
                self.menu.select()
                self.set_render_flag()


    def handle_back_button(self, channel):
        with self.interrupt_lock:
            if self.is_in_menu_mode():
                self.menu.up()
            self.active_timer = None
            self.timer_set = None
            self.set_render_flag()


    def handle_timer_button(self, channel):
        with self.interrupt_lock:
            if self.timer_set is not None and not self.timer_set.is_empty():
                active_timer = self.timer_set.next()
                active_timer.start()
                self.active_timer = active_timer


    def handle_scroll_pulse(self, channel):
        with self.interrupt_lock:
            if channel == self.last_scroll_chanel:
                return

            if self.last_scroll_chanel is None:
                self.last_scroll_chanel = channel
                return

            if self.is_in_menu_mode():
                if channel == consts.SCROLL_B_CHANNEL:
                    self.menu.scroll(-1)
                    self.set_render_flag()
                elif channel == consts.SCROLL_A_CHANNEL:
                    self.menu.scroll(1)
                    self.set_render_flag()

            self.last_scroll_chanel = None
