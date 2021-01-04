import requests
from bs4 import BeautifulSoup
import urllib.parse
import json
import traceback

def get_films():
    url = "https://www.digitaltruth.com/devchart.php"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    dropdown_options = soup.select("#Film option")
    mapped = map(lambda option: dict(id=option.get("value"), name=option.text), dropdown_options)
    filtered = filter(lambda option: option["id"], mapped)
    return list(filtered)


def get_film_processing_info(id):
    def _make_time(value):
        try:
            if not value:
                return None
            if "+" in value:
                value = value.split("+")
            elif "-" in value:
                value = [value.split("-")[0]]
            else:
                value = [value]
            return list(map(lambda v: float(v) * 60, value))
        except:
            print(f"Bad value for conversion: {value}")
            return None

    def _get_film_info_row_mapper(row):
        try:
            cells = row.find_all("td")
            return dict(
                developer=cells[1].text,
                dilution=cells[2].text,
                asaiso=cells[3].text,
                time={
                    "35": _make_time(cells[4].text),
                    "120": _make_time(cells[5].text),
                    "sheet": _make_time(cells[6].text)
                }
            )
        except:
            print(id)
            print(row)
            print(traceback.format_exc())
            return None

    id_encoded = urllib.parse.quote(id)
    url = f"https://www.digitaltruth.com/devchart.php?Film={id_encoded}&Developer=&mdc=Search&TempUnits=F&TimeUnits=D"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    table_rows = soup.find(id="mdcmainbox").find_all("tr")[1:]
    mapped = map(_get_film_info_row_mapper, table_rows)
    return list(mapped)


def make_data_results_mapper(film_dict):
    try:
        film_dict["processingInfo"] = get_film_processing_info(film_dict["id"])
        return film_dict
    except:
        print(film_dict["name"])
        print(traceback.format_exc())


def make_tree(data):
    tree = {}
    for film in data:
        if film:
            name = film["name"]
            if name not in tree:
                tree[name] = {}
            for info in film["processingInfo"]:
                if info:
                    developer = info["developer"]
                    dilution = info["dilution"]
                    asaiso = info["asaiso"]
                    if developer not in tree[name]:
                        tree[name][developer] = {}
                    if dilution not in tree[name][developer]:
                        tree[name][developer][dilution] = {}
                    if asaiso not in tree[name][developer][dilution]:
                        tree[name][developer][dilution][asaiso] = {}
                    for film_type in info["time"]:
                        if info["time"][film_type] and film_type not in tree[name][developer][dilution][asaiso]:
                            tree[name][developer][dilution][asaiso][film_type] = info["time"][film_type]
    return tree


films = get_films()
data = list(map(make_data_results_mapper, films))
tree = make_tree(data)

with open("data.json", "w") as file:
    file.write(json.dumps(tree))
