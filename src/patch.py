
from pathlib import Path

import bsdiff4

from .command import runLdid
from .dmg import (hdutilAdd, hdutilChmod, hdutilExtract, hdutilGrow,
                  hdutilRemovePath)
from .file import copyFileToPath, getFileSize, moveFileToPath, removeFile
from .iboot import useiBoot32Patcher
from .kernel import applyRestorePatches
from .utils import listDir


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


def patchRamdisk(patches, working_dir):
    asr = Path('usr/sbin/asr')
    working_asr = f'{working_dir}/asr'

    rde = Path('usr/local/bin/restored_external')
    working_rde = f'{working_dir}/{rde.name}'

    ramdisk = patches['ramdisk']

    working_dmg = f'{working_dir}/{ramdisk}.decrypted'

    # Remove ".dmg" from ramdisk cause it matters, seriously

    dmg_renamed = f'{working_dir}/ramdisk'

    copyFileToPath(working_dmg, dmg_renamed)

    if patches['asr']:
        hdutilExtract(dmg_renamed, str(asr), working_asr)
        patchFile(working_asr, patches['asr'])
        # runLdid(('-S', working_asr))
        hdutilRemovePath(dmg_renamed, str(asr))

    if patches['restored_external']:
        hdutilExtract(dmg_renamed, str(rde), working_rde)
        patchFile(working_rde, patches['restored_external'])
        # runLdid(('-S', working_rde))
        hdutilRemovePath(dmg_renamed, str(rde))

    grow_size = getFileSize(dmg_renamed) + 6_000_00

    hdutilGrow(dmg_renamed, grow_size)

    for path in listDir('*', working_dir):
        if path.name == 'asr':
            hdutilAdd(dmg_renamed, str(path), str(asr))
            hdutilChmod(dmg_renamed, 100755, str(asr))
            removeFile(path)

        if path.name == 'restored_external':
            hdutilAdd(dmg_renamed, str(path), str(rde))
            hdutilChmod(dmg_renamed, 100755, str(rde))
            removeFile(path)

    patched = f'{working_dmg}.patched'

    moveFileToPath(dmg_renamed, patched)

    return patched
