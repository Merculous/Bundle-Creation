
import json


def formatToJSONStr(data):
    return json.dumps(data)


def readJSONStr(data):
    return json.loads(data)


def writeJSONFile(data, path, indent=2):
    with open(path, 'w') as f:
        json.dump(data, f, indent=indent)


def readJSONFile(path):
    with open(path) as f:
        return json.load(f)
