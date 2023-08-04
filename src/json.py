
import json


def writeJSON(data, path, indent=2):
    with open(path, 'w') as f:
        json.dump(data, f, indent=indent)


def readJSON(path):
    with open(path) as f:
        return json.load(f)
