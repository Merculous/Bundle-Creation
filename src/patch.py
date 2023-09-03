
from pathlib import Path

import bsdiff4

from .iboot import useiBoot32Patcher
from .kernel import applyRestorePatches


def patchFile(src, patch):
    bsdiff4.file_patch_inplace(src, patch)


def patchiBoot(files, version):
    base_version = int(version.split('.')[0])

    iBoot = ('iBSS', 'iBEC', 'LLB', 'iBoot')

    for name in files:
        if name in iBoot:
            decrypted = str(files[name]['decrypted'])
            patched = f'{decrypted}.patched'

            boot_args = [
                'nand-enable-reformat=1',
                'rd=md0',
                '-v',
                'debug=0x14e',
                'serial=3',
                'cs_enforcement_disable=1'
            ]

            if name == iBoot[0]:  # iBSS
                # Pre iOS 5 iBSS actually has boot-args

                if base_version == 3 or base_version == 4:
                    useiBoot32Patcher(decrypted, patched, boot_args)
                else:
                    useiBoot32Patcher(decrypted, patched)

            elif name == iBoot[1]:  # iBEC
                useiBoot32Patcher(decrypted, patched, boot_args)

            elif name == iBoot[3]:  # iBoot
                useiBoot32Patcher(decrypted, patched, boot_args[2:])

            else:  # LLB
                useiBoot32Patcher(decrypted, patched)

            files[name]['patched'] = Path(patched)

    return files


def patchKernel(files):
    decrypted = str(files['KernelCache']['decrypted'])
    patched = f'{decrypted}.patched'

    applyRestorePatches(decrypted, patched)

    files['KernelCache']['patched'] = Path(patched)

    return files
