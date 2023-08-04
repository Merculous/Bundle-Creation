
import os
import shutil
from pathlib import Path

from .file import removeFile


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
        '.json',
        '.patched',
        '.packed'
    )

    for thing in Path().glob('*'):
        for ext in stuff:
            if thing.name.endswith(ext):
                removeFile(thing)

        if thing.name.startswith('kernelcache'):
            removeFile(thing)

    asr = Path('asr')

    if asr.exists():
        removeFile(asr)

    removeDirectory('.tmp')
