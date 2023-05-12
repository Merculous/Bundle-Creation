#!/usr/bin/env python3

import json
import plistlib
import shutil
import subprocess
from argparse import ArgumentParser
from pathlib import Path
from zipfile import ZipFile

import bsdiff4


def extractFiles(archive):
    try:
        tmp_dir = Path('.tmp').mkdir()
    except Exception:
        pass

    with ZipFile(archive) as f:
        f.extractall('.tmp')

    Path('.tmp/BuildManifest.plist').unlink()


def readRestorePlist(path):
    with open(path, 'rb') as f:
        data = plistlib.load(f)
        return data


def writeJSON(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def getRestoreInfo(path):
    with open(path) as f:
        data = json.load(f)

    device = data.get('ProductType')
    board = data.get('DeviceMap')[0]['BoardConfig']
    version = data.get('ProductVersion')
    buildid = data.get('ProductBuildVersion')
    platform = data.get('DeviceMap')[0]['Platform']
    ramdisk = data.get('RamDisksByPlatform')[platform]['User']

    bundle_name = f'{device}_{board}_{version}_{buildid}.bundle'

    Path('Restore.json').unlink()

    return (bundle_name, ramdisk)


def getBootchainReady(ramdisk):
    tmp_contents = Path('.tmp').rglob('*')

    needed = (
        'iBSS',
        'iBEC',
        'LLB',
        'iBoot',
        ramdisk
    )

    needed_paths = []

    for thing in tmp_contents:
        for filename in needed:
            if filename in thing.name:
                needed_paths.append(thing)

    for path in needed_paths:
        shutil.copy(path, '.')


def parseKeyTemplate(path):
    with open(path) as f:
        data = f.readlines()

    data = [x.strip() for x in data]

    info = {
        'start': data[0],
        'end': data[-1],
        'spaces': [],
        'data': {}
    }

    for i, line in enumerate(data):
        if line == '':
            info['spaces'].append(i)
        else:
            line = line[2:].split('=')
            if len(line) == 2:
                k = line[0].strip()
                v = line[1].strip()
                info['data'].update({k: v})

    writeJSON(info, 'Keys.json')


def getKeys(path):
    with open(path) as f:
        data = json.load(f)

    data = data.get('data')

    needed_keys = {
        'ramdisk': [
            data.get('RestoreRamdiskIV'),
            data.get('RestoreRamdiskKey')
        ],
        'iBSS': [
            data.get('iBSSIV'),
            data.get('iBSSKey')
        ],
        'iBEC': [
            data.get('iBECIV'),
            data.get('iBECKey')
        ],
        'LLB': [
            data.get('LLBIV'),
            data.get('LLBKey')
        ],
        'iBoot': [
            data.get('iBootIV'),
            data.get('iBootKey')
        ]
    }

    writeJSON(needed_keys, 'Keys.json')


def decrypt(keys_path):
    pass


def main():
    parser = ArgumentParser()

    parser.add_argument('--ipsw', nargs=1)
    parser.add_argument('--bundle', nargs=1)
    parser.add_argument('--template', nargs=1)

    args = parser.parse_args()

    if args.ipsw and args.template:
        extractFiles(args.ipsw[0])
        data = readRestorePlist('.tmp/Restore.plist')
        writeJSON(data, 'Restore.json')
        restore_info = getRestoreInfo('Restore.json')
        getBootchainReady(restore_info[1])
        parseKeyTemplate(args.template[0])
        getKeys('Keys.json')
        decrypt('Keys.json')
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
