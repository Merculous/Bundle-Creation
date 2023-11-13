
import os
import shutil
from pathlib import Path

from .json import readJSONFile


def binCheck():
    tools = readJSONFile('tools.json')

    for tool in tools:
        if tools[tool]['required']:
            path_exists = Path(f'bin/{tool}').exists()

            if path_exists:
                tools[tool]['exists'] = True

    for tool in tools:
        if tools[tool]['required']:
            if not tools[tool]['exists']:
                raise FileNotFoundError(f'{tool} is missing!')


def makeDirs(path):
    os.makedirs(path, exist_ok=True)


def listDir(pattern, path='.', recursive=False):
    if recursive:
        return [x for x in Path(path).rglob(pattern)]
    else:
        return [x for x in Path(path).glob(pattern)]


def removeDirectory(path):
    shutil.rmtree(path, True)


def selectFromList(choices):
    choices_len = len(choices)
    possible_indicies = list(range(choices_len))

    for i, choice in enumerate(choices):
        print(i, choice)

    selected = int(input('Select the index of the value you choose.\n'))

    if selected not in possible_indicies:
        raise IndexError(f'Invaild index: {selected}')

    print(f'Selected: {choices[selected]}')

    return choices[selected]


def cd(path):
    os.chdir(path)


def getUntether(device, buildid):
    for path in listDir('*.tar', 'Jailbreak/g1lbertJB', True):
        if path.parts[2] == device and buildid in path.parts[3]:
            return path
