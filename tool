#!/usr/bin/env python3

import json
import plistlib
import shutil
import subprocess
from argparse import ArgumentParser
from hashlib import sha1
from hurry.filesize import size
from pathlib import Path
from zipfile import ZipFile

import bsdiff4


def extractFiles(archive):
    try:
        Path('.tmp').mkdir()
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
        ],
        'RootFS': [
            data.get('RootFS'),
            data.get('RootFSKey')
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
        'usr/sbin/asr',
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

        # Pre iOS 5, iBSS/LLB can actually use boot-args
        # Maybe add some code to do just that?

        if 'iBEC' in name or 'iBoot' in name:
            # rd=md0 nand-enable-reformat=1 -progress
            boot_args = (
                '--debug',
                '-b',
                '"rd=md0 -v debug=0x14e serial=3 cs_enforcement_disable=1"'
            )

            cmd.extend(boot_args)

        cmds.append(cmd)

        # OK, for some reason boot-args aren't being passed again
        # Adding double quotes somehow make this work???

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

        patch_name = orig.split('.')
        patch_name[-1] = 'patch'
        patch_name = '.'.join(patch_name)

        pack = (
            'bin/xpwntool',
            new,
            f'{new}.packed',
            f'-t {orig}'
        )

        subprocess.run(' '.join(pack), shell=True)

        bsdiff4.file_diff(orig, pack[2], f'bundles/{bundle}/{patch_name}')


def getRootFSInfo():
    with open('Keys.json') as f:
        keys = json.load(f)

    root_fs = f'.tmp/{keys.get("RootFS")[0]}.dmg'
    root_fs_key = keys.get('RootFS')[1]

    cmd = (
        'bin/dmg',
        'extract',
        root_fs,
        'rootfs.dmg',
        f'-k {root_fs_key}'
    )

    subprocess.run(' '.join(cmd), shell=True)

    root_fs_size = round(int(size(Path('rootfs.dmg').stat().st_size)[:-1]) / 10) * 10

    p7z_cmd = subprocess.run(('7z', 'l', 'rootfs.dmg'), capture_output=True, universal_newlines=True)
    p7z_out = p7z_cmd.stdout.splitlines()

    for line in p7z_out:
        if 'usr/' in line:
            mount_name = line.split()[-1].split('/')[0]
            break

    return (root_fs.split('/')[1], mount_name, root_fs_size, root_fs_key)


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
    ramdisk['File'] = f'{keys.get("ramdisk")[0]}.dmg'
    ramdisk['IV'] = keys.get('ramdisk')[1]
    ramdisk['Key'] = keys.get('ramdisk')[2]

    ibss = bootchain.get('iBSS')
    ibss['File'] = bootchain_paths.get('iBSS')
    ibss['IV'] = keys.get('iBSS')[1]
    ibss['Key'] = keys.get('iBSS')[2]
    ibss['Patch'] = Path(ibss.get("File")).name.replace(".dfu", ".patch")

    ibec = bootchain.get('iBEC')
    ibec['File'] = bootchain_paths.get('iBEC')
    ibec['IV'] = keys.get('iBEC')[1]
    ibec['Key'] = keys.get('iBEC')[2]
    ibec['Patch'] = Path(ibec.get("File")).name.replace(".dfu", ".patch")

    llb = bootchain.get('LLB')
    llb['File'] = bootchain_paths.get('LLB')
    llb['IV'] = keys.get('LLB')[1]
    llb['Key'] = keys.get('LLB')[2]
    llb['Patch'] = Path(llb.get("File")).name.replace(".img3", ".patch")

    iboot = bootchain.get('iBoot')
    iboot['File'] = bootchain_paths.get('iBoot')
    iboot['IV'] = keys.get('iBoot')[1]
    iboot['Key'] = keys.get('iBoot')[2]
    iboot['Patch'] = Path(iboot.get("File")).name.replace(".img3", ".patch")

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

    fs_info = getRootFSInfo()

    plist_data['RootFilesystem'] = fs_info[0]
    plist_data['RootFilesystemMountVolume'] = fs_info[1]
    plist_data['RootFilesystemSize'] = fs_info[2]
    plist_data['RootFilesystemKey'] = fs_info[3]

    with open(info_path, 'wb') as f:
        plistlib.dump(plist_data, f)


def replaceAsr(bundle):
    with open('Keys.json') as f:
        keys = json.load(f)

    ramdisk = Path(f'{keys.get("ramdisk")[0]}.dmg.decrypted')
    ramdisk_size = ramdisk.stat().st_size
    new_size = str(ramdisk_size + 250_000)

    # We need to remove '.dmg' from the filename
    # After testing everything I could think of, I came up
    # with one more test, renaming the files. I had been
    # copying the ramdisk to a new filename called 'ramdisk.copy'
    # I soon realized that the name might have been what I was having
    # trouble with, as the following line kept popping up

    # error: /tmp/test/xpwn/hfs/rawfile.c:264: WRITE
    # error: Bad file descriptor

    # I did test until I had realized that having '.dmg' in the name
    # made hdutil just refuse to work. So, apparently we MUST remove
    # at least '.dmg' from the name to continue working with the ramdisk
    # and hdutil. -________-

    new_ramdisk_name = ramdisk.name.replace('.dmg', '')
    shutil.copy(ramdisk.name, new_ramdisk_name)

    grow = (
        'bin/hdutil',
        new_ramdisk_name,
        'grow',
        new_size
    )

    grow_cmd = subprocess.run(
        ' '.join(grow), shell=True, capture_output=True, universal_newlines=True)

    remove_asr = (
        'bin/hdutil',
        new_ramdisk_name,
        'rm',
        'usr/sbin/asr'
    )

    remove_asr_cmd = subprocess.run(
        ' '.join(remove_asr), shell=True, capture_output=True, universal_newlines=True)

    asr_patch_path = f'{bundle}/asr.patch'

    bsdiff4.file_patch('asr', 'asr.patched', asr_patch_path)

    add_patched_asr = (
        'bin/hdutil',
        new_ramdisk_name,
        'add',
        'asr.patched',
        'usr/sbin/asr'
    )

    add_patched_asr_cmd = subprocess.run(
        ' '.join(add_patched_asr), shell=True, capture_output=True, universal_newlines=True)

    fix_asr_permissions = (
        'bin/hdutil',
        new_ramdisk_name,
        'chmod',
        '755',
        'usr/sbin/asr'
    )

    fix_asr_permissions_cmd = subprocess.run(
        ' '.join(fix_asr_permissions), shell=True, capture_output=True, universal_newlines=True)

    repack_ramdisk = (
        'bin/xpwntool',
        new_ramdisk_name,
        f'{new_ramdisk_name}.packed',
        f'-t {new_ramdisk_name.split(".")[0]}.dmg'
    )

    subprocess.run(' '.join(repack_ramdisk), shell=True)


def makeIpsw(bundle):
    with open(f'{bundle}/Info.plist', 'rb') as f:
        data = plistlib.load(f)

    packed = [p for p in Path().glob('*.packed')]

    bootchain = data.get('FirmwarePatches')

    for thing in bootchain:
        path = bootchain.get(thing)['File']

        for filename in packed:
            prefix = filename.name.split('.')[0]
            if prefix in path:
                path = f'.tmp/{path}'
                shutil.move(filename, path)

    pack = (
        'cd',
        '.tmp',
        '&&',
        '7z',
        'a',
        '-tzip',
        '../custom.ipsw',
        '*'
    )

    subprocess.run(' '.join(pack), shell=True)


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

    try:
        shutil.rmtree('.tmp')
    except Exception:
        pass


def main():
    parser = ArgumentParser()

    parser.add_argument('--clean', action='store_true')
    parser.add_argument('--ipsw', nargs=1)
    parser.add_argument('--template', nargs=1)

    args = parser.parse_args()

    if args.ipsw and args.template:
        clean()
        extractFiles(args.ipsw[0])
        data = readRestorePlist('.tmp/Restore.plist')
        writeJSON(data, 'Restore.json')
        bundle_name, ramdisk, board = getRestoreInfo('Restore.json')
        createBundleFolder(bundle_name)
        getBootchainReady(ramdisk)
        parseKeyTemplate(args.template[0])
        getKeys('Keys.json')
        decrypt('Keys.json')
        # patchRamdisk(bundle_name)
        patchiBoot(bundle_name)
        initInfoPlist(bundle_name, args.ipsw[0], board)
        # replaceAsr(f'bundles/{bundle_name}')
        makeIpsw(f'bundles/{bundle_name}')
        clean()
    elif args.clean:
        clean()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
