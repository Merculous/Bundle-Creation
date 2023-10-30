
from .command import run7zip, runDmg, runHdutil
from .file import getFileSize


def decryptDmg(src, dst, key):
    cmd = (
        'extract',
        src,
        dst,
        f'-k {key}'
    )

    return runDmg(cmd)


def buildRootFS(src, dst):
    cmd = (
        'build',
        src,
        dst
    )

    return runDmg(cmd)


def getRootFSInfo(files):
    decrypted = files['RootFS']['decrypted']

    size = getFileSize(decrypted) // (1024*1024)

    output = run7zip(('l', str(decrypted)))[0].splitlines()

    for line in output:
        if '/Applications' in line:
            break

    mount_name = line.split()[-1].split('/')[0]

    files['RootFS']['size'] = size
    files['RootFS']['mount_name'] = mount_name

    return files


def hdutilList(dmg, path):
    cmd = (
        dmg,
        'ls',
        path
    )
    return runHdutil(cmd)


def hdutilExtract(dmg, src, dst):
    cmd = (
        dmg,
        'extract',
        src,
        dst
    )
    return runHdutil(cmd)

# asr usr/sbin/asr


def hdutilRemovePath(dmg, path):
    cmd = (
        dmg,
        'rm',
        path
    )
    return runHdutil(cmd)


def hdutilGrow(dmg, size):
    cmd = (
        dmg,
        'grow',
        str(size)
    )
    return runHdutil(cmd)


def hdutilAdd(dmg, src, dst):
    cmd = (
        dmg,
        'add',
        src,
        dst
    )
    return runHdutil(cmd)


def hdutilChmod(dmg, mode, path):
    cmd = (
        dmg,
        'chmod',
        str(mode),
        path
    )
    return runHdutil(cmd)
