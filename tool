#!/usr/bin/env python3

import json
import plistlib
import shutil
import subprocess
from argparse import ArgumentParser
from hashlib import sha1
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

    return (bundle_name, ramdisk, board)


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
            data.get('RestoreRamdisk'),
            data.get('RestoreRamdiskIV'),
            data.get('RestoreRamdiskKey')
        ],
        'iBSS': [
            data.get('iBSS'),
            data.get('iBSSIV'),
            data.get('iBSSKey')
        ],
        'iBEC': [
            data.get('iBEC'),
            data.get('iBECIV'),
            data.get('iBECKey')
        ],
        'LLB': [
            data.get('LLB'),
            data.get('LLBIV'),
            data.get('LLBKey')
        ],
        'iBoot': [
            data.get('iBoot'),
            data.get('iBootIV'),
            data.get('iBootKey')
        ]
    }

    writeJSON(needed_keys, 'Keys.json')


def decrypt(keys_path):
    with open(keys_path) as f:
        keys = json.load(f)

    exts = ('dmg', 'dfu', 'img3')
    paths = []

    for path in Path().glob('*'):
        for ext in exts:
            if ext in path.name:
                paths.append(path)

    info = {}

    for path in paths:
        iv, k = None, None

        if path.name.endswith('.dmg'):
            filename, iv, k = keys.get('ramdisk')
            info.update({path.name: [iv, k]})

        for name in keys:
            if name in path.name:
                filename, iv, k = keys.get(name)
                info.update({path.name: [iv, k]})

    cmds = []

    for name, kv in info.items():
        iv, k = kv
        if len(iv) == 32 and len(k) == 64:
            cmd = (
                'bin/xpwntool',
                name,
                f'{name}.decrypted',
                f'-iv {iv}',
                f'-k {k}'
            )
            cmds.append(cmd)
        else:
            cmd = (
                'bin/xpwntool',
                name,
                f'{name}.decrypted'
            )
            cmds.append(cmd)

    for cmd in cmds:
        # FIXME
        # Weird, this only works if ran inside a shell
        subprocess.run(' '.join(cmd), shell=True)


def createBundleFolder(name):
    name = Path(f'bundles/{name}')

    try:
        name.mkdir()
    except Exception:
        print(f'{name} already exists!')


def patchRamdisk(bundle):
    ramdisk = None
    for thing in Path().glob('*.decrypted'):
        if '.dmg' in thing.name:
            ramdisk = thing.name
            break

    extract_asr = (
        'bin/hdutil',
        ramdisk,
        'cat',
        '/usr/sbin/asr',
        '>',
        'asr'
    )

    subprocess.run(' '.join(extract_asr), shell=True)

    create_patch = (
        'bin/asrpatch',
        'asr',
        f'bundles/{bundle}/asr.patch'
    )

    subprocess.run(create_patch)


def patchiBoot(bundle):
    bootchain = []
    iBoot = ('iBSS', 'iBEC', 'LLB', 'iBoot')

    for thing in Path().glob('*'):
        for name in iBoot:
            if thing.name.startswith(name) and thing.name.endswith('.decrypted'):
                bootchain.append(thing.name)

    cmds = []

    for name in bootchain:
        cmd = [
            'bin/iBoot32Patcher',
            name,
            f'{name}.patched',
            '--rsa'
        ]

        if 'iBEC' in name or 'iBoot' in name:
            cmd.append('-b -v')

        cmds.append(cmd)

        # FIXME
        # Similar issue in decrypt()
        # I think since everything I have in 'bin' are symlinks
        # that it doesn't work correctly when not passing values
        # to the 'binary', thus needing to run cmd as a shell command
        # if I don't run the command as a shell command, the '-b -v'
        # arg was never passed, thus only the '--rsa' is passed
        subprocess.run(' '.join(cmd), shell=True)

        orig = name.split('.decrypted')[0]
        new = cmd[2]

        pack = (
            'bin/xpwntool',
            new,
            f'{new}.packed',
            f'-t {orig}'
        )

        subprocess.run(' '.join(pack), shell=True)

        bsdiff4.file_diff(orig, pack[2], f'bundles/{bundle}/{orig}.patch')


# FIXME
# This function below is garbage and needs to be updated


def initInfoPlist(bundle, ipsw, board):
    with open('Info.plist', 'rb') as f:
        plist_data = plistlib.load(f)

    with open('Keys.json') as f:
        keys = json.load(f)

    patch_name = [
        'oof', # 0
        board,
        'RELEASE',
        'lol', # 3
        'patch'
    ]

    dfu_path = 'Firmware/dfu'
    other_path = f'Firmware/all_flash/all_flash.{board}.production'

    bootchain_paths = {
        'iBSS': f'{dfu_path}/iBSS.{board}.RELEASE.dfu',
        'iBEC': f'{dfu_path}/iBEC.{board}.RELEASE.dfu',
        'LLB': f'{other_path}/LLB.{board}.RELEASE.img3',
        'iBoot': f'{other_path}/iBoot.{board}.RELEASE.img3'
    }

    plist_data['Filename'] = ipsw
    plist_data['Name'] = ipsw.split('_Restore.ipsw')[0]

    bootchain = plist_data.get('FirmwarePatches')

    ramdisk = bootchain.get('Restore Ramdisk')
    ramdisk['File'] = keys.get('ramdisk')[0]
    ramdisk['IV'] = keys.get('ramdisk')[1]
    ramdisk['Key'] = keys.get('ramdisk')[2]

    ibss = bootchain.get('iBSS')
    ibss['File'] = bootchain_paths.get('iBSS')
    ibss['IV'] = keys.get('iBSS')[1]
    ibss['Key'] = keys.get('iBSS')[2]
    ibss['Patch'] = f'{Path(ibss.get("File")).name}.patch'

    ibec = bootchain.get('iBEC')
    ibec['File'] = bootchain_paths.get('iBEC')
    ibec['IV'] = keys.get('iBEC')[1]
    ibec['Key'] = keys.get('iBEC')[2]
    ibec['Patch'] = f'{Path(ibec.get("File")).name}.patch'

    llb = bootchain.get('LLB')
    llb['File'] = bootchain_paths.get('LLB')
    llb['IV'] = keys.get('LLB')[1]
    llb['Key'] = keys.get('LLB')[2]
    llb['Patch'] = f'{Path(llb.get("File")).name}.patch'

    iboot = bootchain.get('iBoot')
    iboot['File'] = bootchain_paths.get('iBoot')
    iboot['IV'] = keys.get('iBoot')[1]
    iboot['Key'] = keys.get('iBoot')[2]
    iboot['Patch'] = f'{Path(iboot.get("File")).name}.patch'

    # Check if there are files that aren't encrypted
    # If so, then if there's a "Not Encrypted" string
    # we change it to None, or json's equivalent: null

    for name in bootchain:
        iv = bootchain.get(name)['IV']
        k = bootchain.get(name)['Key']

        thingy = 'Not Encrypted'

        if iv == thingy or k == thingy:
            bootchain[name]['IV'] = ''
            bootchain[name]['Key'] = ''

    plist_data['FirmwarePatches'] = bootchain

    with open(ipsw, 'rb') as f:
        ipsw_sha1 = sha1(f.read()).hexdigest()

    plist_data['SHA1'] = ipsw_sha1

    info_path = f'bundles/{bundle}/Info.plist'

    with open(info_path, 'wb') as f:
        plistlib.dump(plist_data, f)


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
                thing.unlink()

    asr = Path('asr')
    if asr.exists():
        asr.unlink()


def main():
    clean()

    parser = ArgumentParser()

    parser.add_argument('--ipsw', nargs=1)
    parser.add_argument('--bundle', nargs=1)
    parser.add_argument('--template', nargs=1)

    args = parser.parse_args()

    if args.ipsw and args.template:
        extractFiles(args.ipsw[0])
        data = readRestorePlist('.tmp/Restore.plist')
        writeJSON(data, 'Restore.json')
        bundle_name, ramdisk, board = getRestoreInfo('Restore.json')
        createBundleFolder(bundle_name)
        getBootchainReady(ramdisk)
        parseKeyTemplate(args.template[0])
        getKeys('Keys.json')
        decrypt('Keys.json')
        patchRamdisk(bundle_name)
        patchiBoot(bundle_name)
        initInfoPlist(bundle_name, args.ipsw[0], board)
    else:
        parser.print_help()

    clean()

if __name__ == '__main__':
    main()
