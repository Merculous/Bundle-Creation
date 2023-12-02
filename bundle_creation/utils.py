
import os
import shutil
from hashlib import sha1
from pathlib import Path


def binCheck() -> None:
    # bool values indicate the tool exists

    tools = {
        'required': {
            '7z': False,
            'dmg': False,
            'hdutil': False,
            'iBoot32Patcher': False,
            'ldid': False
        },
        'optional': {
            'imagetool': False
        }
    }

    bin_contents = listDir('*', 'bin')

    for path in bin_contents:
        for value in tools:
            for tool in tools[value]:
                if path.name == tool:
                    tools[value][tool] = True

    # Make sure the tools in required are all True

    for tool in tools['required']:
        if tools['required'][tool] is False:
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


# FIXME

def getUntether(device, buildid):
    tar = f'{buildid}.tar'
    untether = None

    for path in listDir(tar, 'Jailbreak', True):
        if device in path.parts and tar in path.parts:
            untether = path
            return untether


def getSHA1(data):
    return sha1(data).hexdigest()
