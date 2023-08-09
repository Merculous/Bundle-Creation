
from .command import runiBoot32Patcher
from .diff import createBSDiffPatchFile
from .file import copyFileToPath
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


def patchiBoot(bundle, version):
    bootchain = []
    iBoot = ('iBSS', 'iBEC', 'LLB', 'iBoot')

    for name in iBoot:
        match = listDir(f'{name}*.decrypted')

        if match:
            bootchain.extend([n.name for n in match])

    for name in bootchain:
        cmd = [
            name,
            f'{name}.patched',
            '--rsa'
        ]

        restore_args = (
            '--debug',
            '-b',
            '"rd=md0 -v debug=0x14e serial=3 cs_enforcement_disable=1"'
        )

        boot_args = (
            '--debug',
            '-b',
            '"-v debug=0x14e serial=3 cs_enforcement_disable=1"'
        )

        supported_versions = list(range(3, 11))

        base_version = int(version.split('.')[0])

        if base_version in supported_versions:
            if base_version == 3 or base_version == 4:
                if 'iBSS' in name:
                    cmd.extend(restore_args)

            if 'iBEC' in name:
                cmd.extend(restore_args)

            elif 'iBoot' in name:
                cmd.extend(boot_args)

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

        pwn_llb = False

        if 'LLB' in new:
            pwn_llb = True

        packFile(new, orig, pwn_llb)

        patch_path = f'bundles/{bundle}/{patch_name}'

        createBSDiffPatchFile(orig, new_packed, patch_path)


def getBootchainReady(ramdisk):
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
        match = listDir(f'{filename}*', '.tmp', True)

        if match:
            needed_paths.extend(match)

    for path in needed_paths:
        copyFileToPath(path, '.')
