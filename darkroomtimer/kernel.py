from darkroomtimer.beeper import Beeper
from darkroomtimer.display import Display
from darkroomtimer.menu import Menu
from darkroomtimer.timer_set import TimerSet
from darkroomtimer.active_timer import ActiveTimer
from darkroomtimer import consts
from darkroomtimer.lights import (Lights, LIGHT_MODE_BLINK)
from threading import Lock
import time
import RPi.GPIO as GPIO
import board
import time

class Kernel:
    def __init__(self, display: Display, beeper: Beeper, lights: Lights):
        self.init_buttons()
        self.display = display
        self.beeper = beeper
        self.menu = Menu(lambda ts: self.goto_timer_mode(ts))
        self.lights = lights
        self.lights.clear_modes()
        self.timer_set = None
        self.active_timer = None
        self.needs_render = False
        self.interrupt_lock = Lock()
        self.last_scroll_chanel = None
        self.render_flag = True
        self.render_flag_lock = Lock()
        self.next_auto_start_timer = None


    def run(self):
        while True:
            with self.interrupt_lock:
                if self.next_auto_start_timer and self.next_auto_start_timer <= time.time() and self.active_timer is None:
                    active_timer = self.timer_set.next()
                    active_timer.start(self.lights)
                    self.active_timer = active_timer
                    self.next_auto_start_timer = None

                if self.active_timer and not self.active_timer.step_and_render(self.beeper, self.display):
                    self.next_auto_start_timer = time.time() + 5
                    self.prepare_for_next_timer()
                        
            with self.render_flag_lock:
                if self.render_flag:
                    if self.timer_set:
                        self.timer_set.render(self.display)
                    else:
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

    def prepare_for_next_timer(self):
        self.active_timer = None
        light = self.timer_set.look_ahead_light()
        self.lights.clear_modes()
        self.lights.set_light_mode(light, LIGHT_MODE_BLINK)
        self.set_render_flag()

    def is_in_menu_mode(self):
        return self.timer_set is None and self.active_timer is None

    
    def set_render_flag(self):
        with self.render_flag_lock:
            self.render_flag = True


    def goto_timer_mode(self, timer_set: TimerSet):
        self.timer_set = timer_set
        self.prepare_for_next_timer()


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
            self.lights.clear_modes()
            self.set_render_flag()


    def handle_timer_button(self, channel):
        with self.interrupt_lock:
            if self.timer_set is not None:
                if self.active_timer is None:
                    active_timer = self.timer_set.next()
                    active_timer.start(self.lights)
                    self.active_timer = active_timer
                else:
                    self.prepare_for_next_timer()


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
