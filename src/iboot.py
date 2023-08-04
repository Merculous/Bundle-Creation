
from .command import runiBoot32Patcher
from .diff import createBSDiffPatchFile
from .file import copyFileToPath
from .utils import listDir
from .xpwntool import packFile


def patchiBoot(bundle):
    bootchain = []
    iBoot = ('iBSS', 'iBEC', 'LLB', 'iBoot')

    for thing in listDir('*'):
        for name in iBoot:
            if thing.name.startswith(name) and thing.name.endswith('.decrypted'):
                bootchain.append(thing.name)

    cmds = []

    for name in bootchain:
        cmd = [
            name,
            f'{name}.patched',
            '--rsa'
        ]

        # TODO
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
    tmp_contents = listDir('*', '.tmp', True)

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
        copyFileToPath(path, '.')
