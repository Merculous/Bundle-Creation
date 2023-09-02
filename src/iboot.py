
from pathlib import Path

from .command import runiBoot32Patcher
from .diff import createBSDiffPatchFile
from .file import copyFileToPath
from .temp import makeTempDir
from .utils import listDir
from .xpwntool import packFile

# TODO
# iBSS can load boot-args and such. Basically skipping over iBEC
# completely. So custom args are I suspect, ignored. Also, apparently,
# manually loading iBSS then iBEC fixes iOS 4 boot/restore? Test this.
# If that's the case, I need to either make the whole restore process
# "manually" or to just boot iBSS and then iBEC first before starting
# a restore on any device.

# TODO
# Check if the other device that has 24kpwn vuln is being used.
# Need to apply other payload besides 2,1.


def patchiBoot(keys, bundle, version, working_dir):
    bootchain = []
    iBoot = ('iBSS', 'iBEC', 'LLB', 'iBoot')

    for name in iBoot:
        match = listDir(f'{name}*.decrypted', working_dir)

        if match:
            bootchain.extend([str(n) for n in match])

    for name in bootchain:
        cmd = [
            name,
            f'{name}.patched',
            '--rsa'
        ]

        part1 = ('--debug', '-b')

        part2 = [
            'rd=md0',
            '-v',
            'debug=0x14e',
            'serial=3',
            'cs_enforcement_disable=1'
        ]

        part3 = [
            *part1,
            '"' +
            ' '.join(part2) +
            '"'
        ]

        supported_versions = list(range(3, 11))

        base_version = int(version.split('.')[0])

        if base_version in supported_versions:
            if base_version == 3 or base_version == 4:
                if 'iBSS' in name:
                    cmd.extend(part3)

            if 'iBEC' in name:
                cmd.extend(part3)

            if 'iBoot' in name:
                part3[2] = part3[2].replace('rd=md0 ', '')
                cmd.extend(part3)

        else:
            raise Exception(f'Unsupported iOS: {version}')

        # OK, for some reason boot-args aren't being passed again
        # Adding double quotes somehow make this work???

        # FIXME
        # Similar issue in decrypt()
        # I think since everything I have in 'bin' are symlinks
        # that it doesn't work correctly when not passing values
        # to the 'binary', thus needing to run cmd as a shell command
        # if I don't run the command as a shell command, the '-b -v'
        # arg was never passed, thus only the '--rsa' is passed
        runiBoot32Patcher(cmd)

        orig = name.split('.decrypted')[0]
        new = cmd[1]

        patch_name = orig.split('.')
        patch_name[-1] = 'patch'
        patch_name = '.'.join(patch_name)

        new_packed = f'{new}.packed'

        if 'LLB' in new:
            # 24Kpwn LLB needs to be encrypted in order to work
            # Deals with KBAG and some other stuff

            llb_name, iv, key = keys['LLB']
            packFile(new, new_packed, orig, iv, key, True)

        else:
            packFile(new, new_packed, orig)

        patch_path = f'bundles/{bundle}/{Path(patch_name).name}'

        createBSDiffPatchFile(orig, new_packed, patch_path)


def getBootchainReady(ramdisk, zip_dir):
    needed = (
        'iBSS',
        'iBEC',
        'LLB',
        'iBoot',
        ramdisk,
        'kernelcache'
    )

    needed_paths = []

    for filename in needed:
        match = listDir(f'{filename}*', zip_dir, True)

        if match:
            needed_paths.extend(match)

    working_dir = makeTempDir()

    for path in needed_paths:
        copyFileToPath(path, working_dir)

    return working_dir
