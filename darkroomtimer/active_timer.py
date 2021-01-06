from darkroomtimer.beeper import Beeper
from darkroomtimer.display import Display
import time
from darkroomtimer.util import format_seconds
import math

class ActiveTimer:
    def __init__(self, label: str, totaltime: int):
        self.label = label
        self.totaltime = totaltime
        self.start_time = None
        self.checkpoints = []
        self.first_run = True

    def start(self):
        self.start_time = time.time()

    def step_and_render(self, beeper: Beeper, display: Display):
        if not self.start_time:
            return True

        elapsed = time.time() - self.start_time
        if elapsed >= self.totaltime:
            # beeper.beep(5)
            return False
        else:
            elapsed_floor = math.floor(elapsed)
            if (elapsed_floor % 60 == 0 or elapsed_floor % 60 == 10) and elapsed_floor not in self.checkpoints:
                # beeper.beeps(0.1, 5)
                self.checkpoints.append(elapsed_floor)

        remaining_str = format_seconds(self.totaltime - elapsed)
        if self.first_run:
            display.update([
                f"{self.label}:",
                remaining_str
            ])
            self.first_run = False
        else:
            display.update_line(1, remaining_str)

        return True
