#!/usr/bin/env python3

import json
import plistlib
import shutil
import subprocess
from argparse import ArgumentParser
from hashlib import sha1
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen
from zipfile import ZipFile

import bsdiff4
from hurry.filesize import size


def runCommand(args, use_shell=False):
    if use_shell:
        cmd = subprocess.run(
            args, capture_output=True, universal_newlines=True, shell=True)
    else:
        cmd = subprocess.run(
            args, capture_output=True, universal_newlines=True)

    return (cmd.stdout, cmd.stderr)


def extractFiles(archive):
    try:
        Path('.tmp').mkdir()
    except Exception:
        pass

    with ZipFile(archive) as f:
        f.extractall('.tmp')


def getCodename():
    with open('.tmp/BuildManifest.plist', 'rb') as f:
        data = plistlib.load(f)

    stuff = data.get('BuildIdentities')[0]
    info = stuff.get('Info')
    codename = info.get('BuildTrain')

    # For iTunes users (gets rid of meaningless popup)
    Path('.tmp/BuildManifest.plist').unlink()

    return codename


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

    platform = data.get('DeviceMap')[0]['Platform']

    info = {
        'device': data.get('ProductType'),
        'board': data.get('DeviceMap')[0]['BoardConfig'],
        'version': data.get('ProductVersion'),
        'buildid': data.get('ProductBuildVersion'),
        'platform': platform,
        'ramdisk': data.get('RamDisksByPlatform')[platform]['User']
    }

    things = (
        info.get('device'),
        info.get('board'),
        info.get('version'),
        info.get('buildid')
    )

    bundle_name = f'{things[0]}_{things[1]}_{things[2]}_{things[3]}.bundle'

    Path('Restore.json').unlink()

    return (bundle_name, info)


def getBootchainReady(ramdisk):
    tmp_contents = Path('.tmp').rglob('*')

    needed = (
        'iBSS',
        'iBEC',
        'LLB',
        'iBoot',
        ramdisk,
        'kernelcache'
    )

    needed_paths = []

    for thing in tmp_contents:
        for filename in needed:
            if filename in thing.name:
                needed_paths.append(thing)

    for path in needed_paths:
        shutil.copy(path, '.')


def readFromURL(url, mode, use_json):
    try:
        r = urlopen(url)
    except HTTPError:
        print(f'Got error from url: {url}')
    else:
        data = r.read()

        if mode == 's':
            data = data.decode('utf-8')

            if use_json:
                return json.loads(data)
            else:
                return data

        elif mode == 'b':
            return data

        else:
            raise Exception(f'Got mode: {mode}')


def parseKeyTemplate(template):
    template = template.splitlines()

    data = [x.strip() for x in template]

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


def getKeys(codename, buildid, device):
    url = f'https://www.theiphonewiki.com/w/index.php?title={codename}_{buildid}_({device})&action=raw'
    template = readFromURL(url, 's', False)
    parseKeyTemplate(template)

    with open('Keys.json') as f:
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
        ],
        'kernelcache': [
            data.get('Kernelcache'),
            data.get('KernelcacheIV'),
            data.get('KernelcacheKey')
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

        if path.name.startswith('kernelcache'):
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
        runCommand(' '.join(cmd), True)


def createBundleFolder(name):
    try:
        Path('bundles').mkdir()
    except Exception:
        pass

    try:
        Path(f'bundles/{name}').mkdir()
    except Exception:
        pass


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

    runCommand(' '.join(extract_asr), True)

    create_patch = (
        'bin/asrpatch',
        'asr',
        f'bundles/{bundle}/asr.patch'
    )

    runCommand(create_patch)


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

        ibec_args = (
            '--debug',
            '-b',
            '"rd=md0 -v debug=0x14e serial=3 cs_enforcement_disable=1"'
        )

        iboot_args = (
            '--debug',
            '-b',
            '"-v debug=0x14e serial=3 cs_enforcement_disable=1"'
        )

        if 'iBEC' in name:
            cmd.extend(ibec_args)

        if 'iBoot' in name:
            cmd.extend(iboot_args)

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
        runCommand(' '.join(cmd), True)

        orig = name.split('.decrypted')[0]
        new = cmd[2]

        patch_name = orig.split('.')
        patch_name[-1] = 'patch'
        patch_name = '.'.join(patch_name)

        pack = [
            'bin/xpwntool',
            new,
            f'{new}.packed',
            f'-t {orig}'
        ]

        if 'LLB' in new:
            pack.append('-xn8824k')

        runCommand(' '.join(pack), True)

        bsdiff4.file_diff(orig, pack[2], f'bundles/{bundle}/{patch_name}')


def patchKernel(bundle, version):
    name = None
    for path in Path().glob('*.decrypted'):
        if path.name.startswith('kernelcache'):
            name = path.name
            break

    patch_kernel = (
        'bin/fuzzy_patcher',
        '--patch',
        f'--delta kernel\\ patches/{version}/{version}.json',
        f'--orig {name}',
        f'--patched {name}.patched'
    )

    runCommand(' '.join(patch_kernel), True)

    packed = f'{name}.patched.packed'

    pack = (
        'bin/xpwntool',
        f'{name}.patched',
        packed,
        f'-t {name.replace(".decrypted", "")}'
    )

    runCommand(' '.join(pack), True)

    original = name.replace('.decrypted', '')

    bsdiff4.file_diff(name, packed, f'bundles/{bundle}/{original}.patch')


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

    runCommand(' '.join(cmd), True)

    root_fs_size = round(
        int(size(Path('rootfs.dmg').stat().st_size)[:-1]) / 10) * 10

    p7z_cmd = runCommand(('7z', 'l', 'rootfs.dmg'))
    p7z_out = p7z_cmd[0].splitlines()

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

    kernel = bootchain.get('KernelCache')
    kernel['File'] = keys.get('kernelcache')[0]
    kernel['IV'] = keys.get('kernelcache')[1]
    kernel['Key'] = keys.get('kernelcache')[2]
    kernel['Patch'] = f'{keys.get("kernelcache")[0]}.patch'

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

    runCommand(' '.join(grow), True)

    remove_asr = (
        'bin/hdutil',
        new_ramdisk_name,
        'rm',
        'usr/sbin/asr'
    )

    runCommand(' '.join(remove_asr), True)

    asr_patch_path = f'{bundle}/asr.patch'

    bsdiff4.file_patch('asr', 'asr.patched', asr_patch_path)

    add_patched_asr = (
        'bin/hdutil',
        new_ramdisk_name,
        'add',
        'asr.patched',
        'usr/sbin/asr'
    )

    runCommand(' '.join(add_patched_asr), True)

    fix_asr_permissions = (
        'bin/hdutil',
        new_ramdisk_name,
        'chmod',
        '755',
        'usr/sbin/asr'
    )

    runCommand(' '.join(fix_asr_permissions), True)

    repack_ramdisk = (
        'bin/xpwntool',
        new_ramdisk_name,
        f'{new_ramdisk_name}.packed',
        f'-t {new_ramdisk_name.split(".")[0]}.dmg'
    )

    runCommand(' '.join(repack_ramdisk), True)


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

    runCommand(' '.join(pack), True)


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

        if thing.name.startswith('kernelcache'):
            try:
                thing.unlink()
            except Exception:
                pass

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

    args = parser.parse_args()

    if args.ipsw:
        clean()
        extractFiles(args.ipsw[0])
        codename = getCodename()
        data = readRestorePlist('.tmp/Restore.plist')
        writeJSON(data, 'Restore.json')
        bundle_name, info = getRestoreInfo('Restore.json')
        createBundleFolder(bundle_name)
        getBootchainReady(info.get('ramdisk'))
        getKeys(codename, info.get('buildid'), info.get('device'))
        decrypt('Keys.json')
        # patchRamdisk(bundle_name)
        patchiBoot(bundle_name)
        patchKernel(bundle_name, info.get('version'))
        initInfoPlist(bundle_name, args.ipsw[0], info.get('board'))
        # replaceAsr(f'bundles/{bundle_name}')
        # makeIpsw(f'bundles/{bundle_name}')
        clean()
    elif args.clean:
        clean()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
