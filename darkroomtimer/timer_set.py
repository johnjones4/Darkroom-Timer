from darkroomtimer.util import format_seconds
from darkroomtimer.display import Display
from darkroomtimer.active_timer import ActiveTimer
from darkroomtimer.util import format_seconds

class TimerSet:
    def __init__(self, timers):
        self.timers = timers


    @classmethod
    def make_paper_timer_set(self):
        return TimerSet([
            ("Developer", 60),
            ("Stop Bath", 30),
            ("Fixer", 120)
        ])

    @classmethod
    def make_film_timer_set(self, film_times):
        times = list(map(lambda t: ("Developer", t), film_times)) + [
            ("Stop Bath", 60),
            ("Fixer", 60 * 5)
        ]
        return TimerSet(times)

    
    def is_empty(self):
        return len(self.timers) == 0


    def render(self, display: Display):
        if not self.is_empty():
            (label, totaltime) = self.timers[0]
            totaltime_str = format_seconds(totaltime)
            display.update([
                f"{label}:",
                totaltime_str
            ])

    def next(self):
        if self.is_empty():
            return None
        (label, totaltime) = self.timers.pop(0)
        return ActiveTimer(label, totaltime)
