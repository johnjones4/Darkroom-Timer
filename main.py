import json
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
import time
import RPi.GPIO as GPIO
import math
from threading import Thread, Lock
from queue import Queue

def render_page():
    global LCD
    LCD.clear()
    LCD.message = get_page()


def format_seconds(s):
    minutes = math.floor(s / 60)
    seconds = math.floor(s - (minutes * 60))
    if seconds < 10:
        seconds = f"0{seconds}"
    return f"{minutes}:{seconds}"


def render_timer():
    global LAST_TIME_TEXT, LAST_TIME_LABEL
    if ACTIVE_TIMER:
        (label, totaltime) = ACTIVE_TIMER
        elapsed = time.time() - ACTIVE_TIMER_START
        remaining_str = format_seconds(totaltime - elapsed)
        if LAST_TIME_LABEL is None or LAST_TIME_LABEL != label:
            LCD.clear()
            LCD.message = f"{label}: {remaining_str}"
            LAST_TIME_LABEL = label
        else:
            LCD.column = len(label) + 2
            n_spaces = 16 - (len(label) + 2 + len(remaining_str))
            spaces = "".join(map(lambda _: " ", range(n_spaces)))
            LCD.message = remaining_str
    elif TIMERS:
        LCD.clear()
        (label, totaltime) = TIMERS[0]
        totaltime_str = format_seconds(totaltime)
        LCD.message = f"{label}: {totaltime_str}"


def load_recents():
    options = {}
    with open("recent.json", "r") as file:
        data = json.loads(file.read())
        for row in data:
            options[row["label"]] = lambda: setup_timer(row["times"])
    return options


def show_film_development(film_times):
    times = list(map(lambda t: ("Developer", t), film_times)) + [
        ("Stop Bath", 60),
        ("Fixer", 60 * 5)
    ]
    setup_timer(times)


def setup_timer(timers):
    global TIMERS
    show_options(None)
    TIMERS = timers
    render_timer()


def show_options(tree):
    global ACTIVE_TREE, SELECTED_INDEX, PREVIOUS_TREE_STACK, TIMERS
    if ACTIVE_TREE is not None:
        PREVIOUS_TREE_STACK.append((ACTIVE_TREE, SELECTED_INDEX))
    SELECTED_INDEX = 0
    ACTIVE_TREE = tree
    if ACTIVE_TREE:
        TIMERS = None
        render_page()


def up_one_level():
    global ACTIVE_TREE, SELECTED_INDEX, PREVIOUS_TREE_STACK, TIMERS, ACTIVE_TIMER, ACTIVE_TIMER_START, ACTIVE_TIMER_CHECKPOINTS, LAST_TIME_LABEL
    if len(PREVIOUS_TREE_STACK) == 0:
        return
    (tree, index) = PREVIOUS_TREE_STACK.pop(len(PREVIOUS_TREE_STACK) - 1)
    SELECTED_INDEX = index
    ACTIVE_TREE = tree
    TIMERS = None
    ACTIVE_TIMER = None
    ACTIVE_TIMER_START = None
    ACTIVE_TIMER_CHECKPOINTS = None
    LAST_TIME_LABEL = None
    render_page()


def save_recent(times):
    global ACTIVE_TREE, SELECTED_INDEX, PREVIOUS_TREE_STACK
    parts = []
    for (tree, index) in PREVIOUS_TREE_STACK[1:]:
        keys = list(tree.keys())
        item = keys[index]
        parts.append(item)
    new_entry = dict(
        label="/".join(parts),
        times=times
    )
    try:
        with open("recent.json", "r") as file:
            data = json.loads(file.read())
        data.insert(new_entry, 0)
    except:
        data = [new_entry]
    with open("recent.json", "w") as file:
        file.write(json.dumps(data))


def change_page(delta):
    global ACTIVE_TREE, SELECTED_INDEX
    data = ACTIVE_TREE.keys()
    new_index = SELECTED_INDEX + delta
    if new_index >= 0 and new_index < len(data):
        SELECTED_INDEX = new_index
        render_page()


def get_page(char_limit = 16):
    data = list(ACTIVE_TREE.keys())
    if SELECTED_INDEX == len(data) - 1 and len(data) >= 1:
        return " " + data[SELECTED_INDEX - 1][:char_limit - 1] + "\n>" + data[SELECTED_INDEX][:char_limit-1] 
    elif SELECTED_INDEX < len(data) - 1:
        return ">" + data[SELECTED_INDEX][:char_limit - 1] + "\n " + data[SELECTED_INDEX + 1][:char_limit - 1] 
    else:
        return ">" + data[SELECTED_INDEX][:char_limit - 1]


def select_item():
    keys = list(ACTIVE_TREE.keys())
    key = keys[SELECTED_INDEX]
    child = ACTIVE_TREE[key]
    if isinstance(child, dict):
        show_options(child)
    elif callable(child):
        child()
    else:
        print("Unhandled value!", child)


def load_film_data():
    def _make_activator(child):
        def activator():
            show_film_development(child)
            save_recent(child)
        return activator
    def _dive_tree(tree):
        new_tree = {}
        for key in tree:
            child = tree[key]
            if isinstance(child, dict):
                new_tree[key] = _dive_tree(child)
            elif isinstance(child, list):
                new_tree[key] = _make_activator(child)
            else:
                print("Unhandled value!", child)
        return new_tree

    with open("data.json", "r") as file:
        info = json.loads(file.read())
        return _dive_tree(info)


def is_selector_mode():
    return ACTIVE_TREE is not None


def is_timer_start_mode():
    return TIMERS and not ACTIVE_TIMER


def init_buttons():
    channels = [
        (SCROLL_SELECT_CHANNEL, handle_select_button, GPIO.RISING),
        (BACK_CHANNEL, handle_back_button, GPIO.RISING),
        (TIMER_START_CHANNEL, handle_timer_button, GPIO.RISING),
        (SCROLL_A_CHANNEL, handle_scroll_channel_a, GPIO.BOTH),
        (SCROLL_B_CHANNEL, handle_scroll_channel_b, GPIO.BOTH)
    ]
    for (channel, callback, mode) in channels:
        GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(channel, mode, callback=callback, bouncetime=200)


def init_lcd():
    lcd_columns = 16
    lcd_rows = 2
    lcd_rs = digitalio.DigitalInOut(board.D26)
    lcd_en = digitalio.DigitalInOut(board.D19)
    lcd_d7 = digitalio.DigitalInOut(board.D27)
    lcd_d6 = digitalio.DigitalInOut(board.D22)
    lcd_d5 = digitalio.DigitalInOut(board.D24)
    lcd_d4 = digitalio.DigitalInOut(board.D25)
    lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows)
    lcd.message = "Initializing ..."
    return lcd


def generic_button_detect(channel):
    return GPIO.input(channel) == GPIO.HIGH


def handle_scroll_state():
    if is_selector_mode():
        if CHANNEL_A_STATE == None or CHANNEL_B_STATE == None:
            return 
        if CHANNEL_A_STATE and not CHANNEL_B_STATE:
            print("down")
            change_page(1)
        elif not CHANNEL_A_STATE and CHANNEL_B_STATE:
            print("up")
            change_page(-1)


def handle_scroll_channel_a(channel):
    global CHANNEL_A_STATE
    CHANNEL_A_STATE = GPIO.input(SCROLL_A_CHANNEL) == GPIO.HIGH
    if CHANNEL_A_STATE:
        handle_scroll_state()


def handle_scroll_channel_b(channel):
    global CHANNEL_B_STATE
    CHANNEL_B_STATE = GPIO.input(SCROLL_B_CHANNEL) == GPIO.HIGH
    if CHANNEL_B_STATE:
        handle_scroll_state()


def handle_back_button(channel):
    up_one_level()


def handle_select_button(channel):
    if is_selector_mode():
        select_item()


def handle_timer_button(channel):
    global ACTIVE_TIMER, ACTIVE_TIMER_START, TIMERS, ACTIVE_TIMER_CHECKPOINTS, LAST_TIME_LABEL
    if is_timer_start_mode():
        if TIMERS:
            beep(1)
            ACTIVE_TIMER = TIMERS.pop(0)
            ACTIVE_TIMER_START = time.time()
            ACTIVE_TIMER_CHECKPOINTS = []
            LAST_TIME_LABEL = None
        else:
            reset_menu()


def handle_timer():
    global ACTIVE_TIMER, ACTIVE_TIMER_START, TIMERS, ACTIVE_TIMER_CHECKPOINTS, LAST_TIME_LABEL
    (label, totaltime) = ACTIVE_TIMER
    elapsed = time.time() - ACTIVE_TIMER_START
    if elapsed >= totaltime:
        ACTIVE_TIMER_START = None
        ACTIVE_TIMER = None
        ACTIVE_TIMER_CHECKPOINTS = None
        LAST_TIME_LABEL = None
        beep(5)
        return len(TIMERS) > 0
    else:
        elapsed_floor = math.floor(elapsed)
        if (elapsed_floor % 60 == 0 or elapsed_floor % 60 == 10) and elapsed_floor not in ACTIVE_TIMER_CHECKPOINTS:
            beeps(0.1, 5)
            ACTIVE_TIMER_CHECKPOINTS.append(elapsed_floor)
    return True


def beep(length):
    BEEP_QUEUE.put((True, length))


def beeps(length, count):
    for _ in range(count):
        BEEP_QUEUE.put((True, length))
        BEEP_QUEUE.put((False, length))


def beep_thread():
    GPIO.setup(BUZZER_CHANNEL, GPIO.OUT)
    GPIO.output(BUZZER_CHANNEL, 0)
    while True:
        if not BEEP_QUEUE.empty():
            (beep, length) = BEEP_QUEUE.get()
            if beep:
                print("high")
                # GPIO.output(BUZZER_CHANNEL, 1)
            time.sleep(length)
            print("low")
            GPIO.output(BUZZER_CHANNEL, 0)


def runloop():
    print("Ready")
    while True:
        if ACTIVE_TIMER:
            if not handle_timer():
                reset_menu()
            else:
                render_timer()


def reset_menu():
    global PREVIOUS_TREE_STACK
    PREVIOUS_TREE_STACK = []
    show_options({
        "Film Development": load_film_data(),
        "Recent Film Dev": lambda: load_recents(),
        "Paper Development": lambda: setup_timer([
            ("Developer", 60),
            ("Stop Bath", 30),
            ("Fixer", 120)
        ])
    })


if __name__ == "__main__":
    SCROLL_A_CHANNEL = 9
    SCROLL_B_CHANNEL = 11
    SCROLL_SELECT_CHANNEL = 4
    BACK_CHANNEL = 5
    TIMER_START_CHANNEL = 6
    BUZZER_CHANNEL = 16
    
    CHANNEL_A_STATE = None
    CHANNEL_B_STATE = None
    PREVIOUS_TREE_STACK = []
    ACTIVE_TREE = None
    TIMERS = None
    ACTIVE_TIMER = None
    ACTIVE_TIMER_START = None
    ACTIVE_TIMER_CHECKPOINTS = None
    SELECTED_INDEX = 0
    LAST_TIME_LABEL = None
    BEEP_QUEUE = Queue()

    GPIO.setmode(GPIO.BCM)
    LCD = init_lcd()
    init_buttons()
    reset_menu()

    Thread(
        target=beep_thread,
        daemon=True,
    ).start()

    runloop()
