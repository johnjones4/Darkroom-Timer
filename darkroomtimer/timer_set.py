from darkroomtimer.util import format_seconds
from darkroomtimer.display import Display
from darkroomtimer.active_timer import ActiveTimer
from darkroomtimer.util import format_seconds
from darkroomtimer.lights import (
    Lights, LIGHT_DEVELOP, LIGHT_STOP, LIGHT_FIX, LIGHT_MODE_BLINK
)

class TimerSet:
    def __init__(self, timers, auto_run):
        self.timers = timers
        self.pointer = 0
        self.auto_run = auto_run


    @classmethod
    def make_paper_timer_set(self):
        return TimerSet([
            ("Developer", 60, LIGHT_DEVELOP),
            ("Stop Bath", 30, LIGHT_STOP),
            ("Fixer", 120, LIGHT_FIX)
        ], True)

    @classmethod
    def make_film_timer_set(self, film_times):
        times = list(map(lambda t: ("Developer", t, LIGHT_DEVELOP), film_times)) + [
            ("Stop Bath", 60, LIGHT_STOP),
            ("Fixer", 60 * 5, LIGHT_FIX)
        ]
        return TimerSet(times, False)


    def render(self, display: Display):
        (label, totaltime, _) = self.timers[self.pointer % len(self.timers)]
        totaltime_str = format_seconds(totaltime)
        display.update([
            f"{label}:",
            totaltime_str
        ])


    def next(self):
        (label, totaltime, light) = self.timers[self.pointer % len(self.timers)]
        self.pointer += 1
        return ActiveTimer(label, totaltime, light)


    def look_ahead_light(self):
        ahead = (self.pointer) % len(self.timers)
        return self.timers[ahead][2]
