
import os
import shutil
from pathlib import Path

from .file import removeFile
from .json import readJSON


def binCheck():
    tools = readJSON('tools.json')

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


def createBundleFolder(name):
    makeDirs(f'bundles/{name}')


def clean():
    stuff = (
        '.dmg',
        '.decrypted',
        '.dfu',
        '.img3',
        '.patched',
        '.packed',
        'kernelcache',
        'asr',
        'Restore',
        'Keys'
    )

    tmp = []

    for thing in stuff:
        matches = listDir(f'*{thing}*')

        if matches:
            tmp.extend(matches)

    for path in tmp:
        removeFile(path)

    removeDirectory('.tmp')


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
