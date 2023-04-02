import cv2, json, pathlib, pytesseract, sys, requests
import numpy as nm
from PIL import ImageGrab, Image
from os.path import join
from sys import argv
# from google.cloud import firestore
from Levenshtein import distance
from win32gui import FindWindow, GetWindowRect
import http.client
import json

gem_types = ["phantasmal", "divergent", "anomalous"]
item_types = ["replica"]

pytesseract.pytesseract.tesseract_cmd = "Tesseract-OCR\\tesseract"


def extract_gem(isHeist, gem_names):
    results = {}
    for gem_name in gem_names:
        results[gem_name] = []

        if(isHeist):

            for l in run_query_heist(gem_name):
                reward = l["reward"];
                results[gem_name].append(l["username"] + ": " + (reward != "" if reward else "No Reward"))
        else:
            for l in run_query_lab(gem_name):
                base = l["itemBase"]
                reward = l["reward"]
                results[gem_name].append(l["username"] + ": " + base + " : " + (reward != "" if reward else "No Reward"))
    
    return results

def run_query_heist(itemName):
    dict = run_query(itemName, "Heist")
    matchingItems = []
    for item in dict:
        try:
            fields = item["document"]["fields"]
            matchingItems.append({"reward": fields["reward"]["stringValue"], "username": fields["username"]["stringValue"]})
        except:
            continue

    return matchingItems

def run_query_lab(itemName):
    dict = run_query(itemName, "Lab")
    matchingItems = []
    for item in dict:
        try:
            fields = item["document"]["fields"]
            matchingItems.append({"reward": fields["reward"]["stringValue"], "username": fields["username"]["stringValue"], "itemBase": fields["itemBase"]["stringValue"]})
        except:
            continue

    return matchingItems

def run_query(itemName, collection):
    conn = http.client.HTTPSConnection("firestore.googleapis.com")
    payload = json.dumps({
    "structuredQuery": {
        "where": {
        "compositeFilter": {
            "op": "AND",
            "filters": [
            {
                "fieldFilter": {
                "field": {
                    "fieldPath": "itemName"
                },
                "op": "EQUAL",
                "value": {
                    "stringValue": itemName
                }
                }
            },
            {
                "fieldFilter": {
                "field": {
                    "fieldPath": "status"
                },
                "op": "EQUAL",
                "value": {
                    "stringValue": "open"
                }
                }
            }
            ]
        }
        },
        "from": [
        {
            "collectionId": collection
        }
        ],
        "orderBy": {
        "field": {
            "fieldPath": "timestamp"
        },
        "direction": "ASCENDING"
        }
    }
    })
    headers = {
    'Content-Type': 'application/json'
    }
    conn.request("POST", "/v1/projects/east-oriath-exiles/databases/(default)/documents/:runQuery", payload, headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    dict = json.loads(data)
    return dict

def get_gem_name():
    window_handle = FindWindow(None, "Path Of Exile")
    window_rect   = GetWindowRect(window_handle)
    cap = ImageGrab.grab(bbox=window_rect, all_screens=True)
    # cap = ImageGrab.grab(all_screens=False)
    _, img = cv2.threshold(nm.array(cap), 135, 255, cv2.THRESH_BINARY) 

    width = 1800; 
    height = int(img.shape[0] / (img.shape[1] / width))
    dim = (width, height)
    
    img = cv2.resize(nm.array(img), dim, interpolation=cv2.INTER_AREA)
    tesstr = pytesseract.image_to_string(nm.array(img), lang="eng", config="heist")

    split = [x.lower() for x in tesstr.split("\n")]

    with open(join(pathlib.Path(__file__).parent.resolve(), "gem_names/gem_names.txt"), "r") as f:
        gem_names = [x.lower().rstrip() for x in f.readlines()]
    with open(join(pathlib.Path(__file__).parent.resolve(), "item_names/item_names.txt"), "r") as f:
        item_names = [x.lower().rstrip() for x in f.readlines()]
    with open(join(pathlib.Path(__file__).parent.resolve(), "lab_names/lab_names.txt"), "r") as f:
        lab_names = [x.lower().rstrip() for x in f.readlines()]

    heist = False
    items = []
    for s in split:
        names = FindNames(gem_names, s, gem_types)
        if names is not None and len(names) != 0:
            items.extend(names)
            heist = True
    for s in split:
        names = FindNames(item_names, s, item_types)
        if names is not None and len(names) != 0:
            items.extend(names)
            heist = True
    if(len(items) == 0):
        for s in split:
            names = FindLabNames(lab_names, s)
            if names is not None and len(names) != 0:
                items.extend(names)
                heist = False

    return (heist, nm.unique(items))

def FindLabNames(names, s):
    gems = []
    index = -1

    index = 0
    nextIndex = 0
    nextIndex = s.find(" ", index)
    
    while nextIndex < len(s):
        nextIndex = s.find(" ", index)
        if nextIndex == -1:
            break
        
        if True:
            name = FindLabTypes(names, s, index)
            if name is not None:
                gems.append(name)
        index = nextIndex + 1
    return gems

def FindNames(names, s, types):
    gems = []
    index = -1

    index = 0
    nextIndex = 0
    nextIndex = s.find(" ", index)
    
    while nextIndex < len(s):
        nextIndex = s.find(" ", index)
        if nextIndex == -1:
            break
        
        word = s[index:nextIndex]
        if any((type for type in types if distance(type, word) < 3)):
            name = FindTypes(names, s, index, word)
            if name is not None:
                gems.append(name)
        index = nextIndex + 1
    return gems

def FindTypes(gem_names, s, index, type):
    nextIndex = s.index(" ", index)
    index = nextIndex + 1
    while nextIndex < len(s):
        nextIndex = s.find(" ", nextIndex + 1)
        if nextIndex == -1:
            nextIndex = len(s)

        gem_name = next((gem.lower() for gem in gem_names if distance(s[index:nextIndex], gem) < 3), None)
        if gem_name is not None:
            return type + " " + gem_name
        
def FindLabTypes(gem_names, s, index):
    nextIndex = s.index(" ", index)
    while nextIndex < len(s):
        nextIndex = s.find(" ", nextIndex + 1)
        if nextIndex == -1:
            nextIndex = len(s)

        gem_name = next((gem.lower() for gem in gem_names if distance(s[index:nextIndex], gem) < 3), None)
        if gem_name is not None:
            return gem_name


def get_gem_info():
    isHeist, names = get_gem_name()
    gem_info = extract_gem(isHeist, names)
    results = {}
    for name, d in gem_info.items():
        results[name] = d
    return results

def print_output():
    price_info = get_gem_info()
    if not len(price_info):
        print("Trouble parsing gem data due to OCR technical difficulties, sorry! (try holding alt and trying again)")
        sys.exit(1)
    for gem, users in price_info.items():
        print(f"{gem} ({', '.join(users)})")

print_output()