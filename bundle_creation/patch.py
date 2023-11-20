
from pathlib import Path

import bsdiff4

from .command import runLdid, runImagetool
from .dmg import (hdutilAdd, hdutilChmod, hdutilExtract, hdutilGrow,
                  hdutilRemovePath)
from .file import copyFileToPath, getFileSize, moveFileToPath, removeFile, writeBinaryFile, readTextFile, writeTextFile
from .iboot import useiBoot32Patcher
from .kernel import applyRestorePatches
from .ramdisk import patchASR, patchRestoredExternal, updateOptions
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
                'debug=0x2014e',
                'serial=3',
                'cs_enforcement_disable=1'
            ]

            if name == iBoot[0]:  # iBSS
                # Pre iOS 5 iBSS actually has boot-args

                if base_version == 3 or base_version == 4:
                    useiBoot32Patcher(decrypted, patched, boot_args)
                else:
                    useiBoot32Patcher(decrypted, patched)

            if name == iBoot[1]:  # iBEC
                if base_version == 3 or base_version == 4:
                    useiBoot32Patcher(decrypted, patched, boot_args[2:])
                else:
                    useiBoot32Patcher(decrypted, patched, boot_args)

            if name == iBoot[2]:  # LLB
                useiBoot32Patcher(decrypted, patched)

            if name == iBoot[3]:  # iBoot
                useiBoot32Patcher(decrypted, patched, boot_args[2:])

            files[name]['patched'] = Path(patched)

    return files


def patchKernel(files):
    decrypted = str(files['KernelCache']['decrypted'])
    patched = f'{decrypted}.patched'

    applyRestorePatches(decrypted, patched)

    files['KernelCache']['patched'] = Path(patched)

    return files


def patchRamdisk(version, board, ramdisk, working_dir):
    asr = Path('usr/sbin/asr')
    working_asr = f'{working_dir}/asr'

    rde = Path('usr/local/bin/restored_external')
    working_rde = f'{working_dir}/{rde.name}'

    # Remove ".dmg" from ramdisk cause it matters, seriously

    dmg_renamed = f'{working_dir}/ramdisk'

    copyFileToPath(ramdisk, dmg_renamed)

    grow_size = getFileSize(dmg_renamed) + 6_000_00

    hdutilGrow(dmg_renamed, grow_size)

    # /usr/local/share/restore/options.(n88).plist

    optionsPath = Path('/usr/local/share/restore/options.plist')
    working_options = f'{working_dir}/{optionsPath.name}'

    print(f'Trying to read from {optionsPath}. This may fail!')

    hdutilExtract(dmg_renamed, str(optionsPath), working_options)

    # Some options.plist include the board in the name

    optionsPathExists = True if getFileSize(working_options) != 0 else False

    if optionsPathExists is False:
        removeFile(working_options)

        optionsPath = Path(str(optionsPath).replace(
            'options', f'options.{board[:-2]}'))
        working_options = f'{working_dir}/{optionsPath.name}'

        print(f'Plain options.plist does not exist! Trying {optionsPath}...')

        hdutilExtract(dmg_renamed, str(optionsPath), working_options)

    try:
        updateOptions(working_options)
    except FileNotFoundError:
        print('Weird. A options.plist does not exist. Continue anyway...')
    else:
        hdutilAdd(dmg_renamed, str(working_options), str(optionsPath))
        removeFile(working_options)

    # asr

    hdutilExtract(dmg_renamed, str(asr), working_asr)

    asr_patched_data = patchASR(working_asr)

    writeBinaryFile(asr_patched_data, working_asr)

    runLdid(('-S', working_asr))
    hdutilRemovePath(dmg_renamed, str(asr))

    # restored_external

    if version.startswith('6'):
        hdutilExtract(dmg_renamed, str(rde), working_rde)

        rde_patched_data = patchRestoredExternal(working_rde)

        writeBinaryFile(rde_patched_data, working_rde)

        # runLdid(('-S', working_rde))
        hdutilRemovePath(dmg_renamed, str(rde))

    for path in listDir('*', working_dir):
        if path.name == 'asr':
            hdutilAdd(dmg_renamed, str(path), str(asr))
            hdutilChmod(dmg_renamed, 100755, str(asr))
            removeFile(path)

        if path.name == 'restored_external':
            hdutilAdd(dmg_renamed, str(path), str(rde))
            hdutilChmod(dmg_renamed, 100755, str(rde))
            removeFile(path)

    patched = f'{ramdisk}.patched'

    moveFileToPath(dmg_renamed, patched)

    return patched


def patchAppleLogo(files, applelogo):
    info = files['AppleLogo']

    orig = str(info['orig'])
    patched = f'{orig}.packed'

    cmd = (
        'inject',
        applelogo,
        patched,
        orig,
        info['iv'],
        info['key']
    )

    runImagetool(cmd)

    info['packed'] = Path(patched)

    return files


def patchRecovery(files, recovery):
    info = files['RecoveryMode']

    orig = str(info['orig'])
    patched = f'{orig}.packed'

    cmd = (
        'inject',
        recovery,
        patched,
        orig,
        info['iv'],
        info['key']
    )

    runImagetool(cmd)

    info['packed'] = Path(patched)

    return files


def patchFStab(path):
    '''
    /dev/disk0s1 / hfs ro 0 1
    /dev/disk0s2 /private/var hfs rw,nosuid,nodev 0 2
    '''

    '''
    /dev/disk0s1s1 / hfs rw 0 1
    /dev/disk0s1s2 /private/var hfs rw 0 2
    '''

    # line 1: ro -> rw
    # line 2: rw,nosuid,nodev -> rw

    data = readTextFile(path)
    data[0] = data[0].replace('ro', 'rw')
    data[1] = data[1].replace(',nosuid,nodev', '')

    writeTextFile(path, data)
