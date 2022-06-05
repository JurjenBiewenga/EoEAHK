import cv2, json, pathlib, pytesseract, sys, requests, pprint, yaml
import numpy as nm
from PIL import ImageGrab, Image
from os.path import join
from string import punctuation

gem_types = ["phantasmal", "divergent", "anomalous"]
gem_url = "https://poe.ninja/api/data/itemoverview?league={0}&type=SkillGem"
config = {}
with open("config.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.CLoader)
pytesseract.pytesseract.tesseract_cmd = config["tesseract_exe"]


def load_gem_names(gem_names):
    words = []
    for n in gem_names:
        for s in n.split(" "):
            words.append(s.rstrip().lower())
    return words


def get_gem_data(league="Sentinel"):
    r = requests.get(gem_url.format(league))
    return json.loads(r.text)["lines"]


def extract_gem_info(lines: dict, gem_names: list):
    results = {}
    for gem_name in gem_names:
        results[gem_name] = {}
        for l in lines:
            if l["name"].lower() == gem_name:
                if results[gem_name].get(l.get("gemLevel")):
                    results[gem_name][l.get("gemLevel")]["chaos"] = min(
                        results[gem_name][l.get("gemLevel")]["chaos"], l.get("chaosValue")
                    )
                    results[gem_name][l.get("gemLevel")]["ex"] = min(
                        results[gem_name][l.get("gemLevel")]["ex"], l.get("exaltedValue")
                    )
                else:
                    results[gem_name][l.get("gemLevel")] = {
                        "chaos": l["chaosValue"],
                        "ex": l["exaltedValue"],
                    }
    return results


def contains_gem_type(s):
    s = s.lower()
    for gem in gem_types:
        if gem in s:
            return True
    return False


def no_punct(word):
    return all([not x in word for x in punctuation])


def extract_gem_name(l, gem_names):
    pos = -1
    for i, word in enumerate(l):
        if word in gem_types:
            pos = i
    prefix = l[pos]
    result = l[pos + 1]
    pos += 1
    while result not in gem_names and pos + 1 < len(l):
        pos += 1
        result += " " + l[pos]
    if result not in gem_names:
        print("Trouble parsing gem data due to OCR technical difficulties, sorry! (try holding alt and trying again)")
        sys.exit(1)
    return prefix + " " + result


def get_gem_name():
    cap = ImageGrab.grab()
    _, img = cv2.threshold(nm.array(cap), 140, 255, cv2.THRESH_BINARY)
    tesstr = pytesseract.image_to_string(nm.array(img), lang="eng", config="heist")
    gem_name = [x.lower() for x in tesstr.split("\n") if contains_gem_type(x)]
    split_list = []
    for name in gem_name:
        temp_list = []
        for word in name.split(" "):
            if "(" not in word and ")" not in word and no_punct(word):
                temp_list.append(word)
        split_list.append(temp_list)
    gems = []
    with open(join(pathlib.Path(__file__).parent.resolve(), "gem_names.txt"), "r") as f:
        gems = [x.lower().rstrip() for x in f.readlines()]
    return nm.unique([extract_gem_name(gem_str, gems) for gem_str in split_list])


def get_gem_price(min_level=3, max_level=19):
    data = get_gem_data()
    gem_info = extract_gem_info(data, get_gem_name())
    results = {}
    for name, d in gem_info.items():
        results[name] = {}
        for level, data in d.items():
            if level in range(min_level, max_level):
                results[name][level] = data
    return results

def print_output():
    price_info = get_gem_price()
    if not len(price_info):
        print("Trouble parsing gem data due to OCR technical difficulties, sorry! (try holding alt and trying again)")
        sys.exit(1)
    for gem, level_dict in price_info.items():
        min_level = min(level_dict.keys())
        chaos_value = level_dict[min_level]["chaos"]
        ex_value = level_dict[min_level]["ex"]
        print(f"{gem} (level {min_level}) - chaos: {chaos_value}, ex: {ex_value}")

print_output()
