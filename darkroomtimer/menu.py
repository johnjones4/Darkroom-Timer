from darkroomtimer.display import Display
from darkroomtimer.timer_set import TimerSet
import json

class Menu:
    def __init__(self, load_timerset_callback):
        self.load_timerset_callback = load_timerset_callback
        self.menu = {
            "Film Development": self.load_film_menu(),
            "Recent Film Dev": self.load_recents(),
            "Paper Development": lambda: load_timerset_callback(TimerSet.make_paper_timer_set())
        }
        self.selected_index = 0
        self.menu_stack = []


    def next_menu(self, menu):
        self.menu_stack.append((self.menu, self.selected_index))
        self.selected_index = 0
        self.menu = menu


    def select(self):
        keys = list(self.menu.keys())
        key = keys[self.selected_index]
        child = self.menu[key]
        if isinstance(child, dict):
            self.next_menu(child)
        elif callable(child):
            child()
        else:
            print("Unhandled value!", child)


    def up(self):
        if len(self.menu_stack) == 0:
            return
        (tree, index) = self.menu_stack.pop(len(self.menu_stack) - 1)
        self.selected_index = index
        self.menu = tree


    def scroll(self, delta: int):
        data = self.menu.keys()
        new_index = self.selected_index + delta
        if new_index >= 0 and new_index < len(data):
            self.selected_index = new_index


    def render(self, display: Display):
        data = list(self.menu.keys())
        if self.selected_index == len(data) - 1 and len(data) > 1:
            display.update([
                " " + data[self.selected_index - 1],
                ">" + data[self.selected_index]
            ])
        elif self.selected_index < len(data) - 1:
            display.update([
                ">" + data[self.selected_index],
                " " + data[self.selected_index + 1]
            ])
        else:
            display.update([
                ">" + data[self.selected_index],
                ""
            ])

    def save_recent(self, times):
        parts = []
        for (tree, index) in self.menu_stack[1:]:
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
    

    def load_recents(self):
        options = {}
        try:
            with open("recent.json", "r") as file:
                data = json.loads(file.read())
                for row in data:
                    options[row["label"]] = lambda: self.load_timerset_callback(TimerSet.make_film_timer_set(row["times"]))
        except:
            pass
        return options


    def load_film_menu(self):
        def _make_activator(child):
            def activator():
                self.load_timerset_callback(TimerSet.make_film_timer_set(child))
                self.save_recent(child)
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
