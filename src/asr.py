
from pathlib import Path

from .command import runAsrPatch, runHdutil
from .file import copyFileToPath, getFileSize
from .keys import readKeys
from .patch import patchFileWithBSDiff
from .utils import listDir
from .xpwntool import packFile

# FIXME
# Current asr patches make asr get killed.
# Most likely bad patching. Use different patcher.


def replaceAsr(bundle):
    keys = readKeys()

    ramdisk = Path(f'{keys.get("ramdisk")[0]}.dmg.decrypted')
    ramdisk_size = getFileSize(ramdisk)
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
    copyFileToPath(ramdisk.name, new_ramdisk_name)

    grow = (
        new_ramdisk_name,
        'grow',
        new_size
    )

    runHdutil(grow)

    remove_asr = (
        new_ramdisk_name,
        'rm',
        'usr/sbin/asr'
    )

    runHdutil(remove_asr)

    asr_patch_path = f'{bundle}/asr.patch'

    patchFileWithBSDiff('asr', 'asr.patched', asr_patch_path)

    add_patched_asr = (
        new_ramdisk_name,
        'add',
        'asr.patched',
        'usr/sbin/asr'
    )

    runHdutil(add_patched_asr)

    fix_asr_permissions = (
        new_ramdisk_name,
        'chmod',
        '755',
        'usr/sbin/asr'
    )

    runHdutil(fix_asr_permissions)

    packFile(new_ramdisk_name, f'{new_ramdisk_name.split(".")[0]}.dmg')


def patchRamdisk(bundle):
    ramdisk = None

    for thing in listDir('*.decrypted'):
        if '.dmg' in thing.name:
            ramdisk = thing.name
            break

    extract_asr = (
        ramdisk,
        'cat',
        'usr/sbin/asr',
        '>',
        'asr'
    )

    runHdutil(extract_asr)

    create_patch = (
        'asr',
        f'bundles/{bundle}/asr.patch'
    )

    runAsrPatch(create_patch)
