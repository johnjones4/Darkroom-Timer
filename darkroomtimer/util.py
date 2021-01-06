import math

def format_seconds(s: float):
    minutes = math.floor(s / 60)
    seconds = math.floor(s - (minutes * 60))
    if seconds < 10:
        seconds = f"0{seconds}"
    return f"{minutes}:{seconds}"

def pad_spaces(string: str, n: int):
    n_spaces = n - len(string)
    spaces = "".join(list(map(lambda _: " ", range(n_spaces))))
    return string + spaces
