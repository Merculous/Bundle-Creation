
from .command import runCommand, runDmg
from .file import getFileSize
from .keys import readKeys


def getRootFSInfo():
    keys = readKeys()

    root_fs = f'.tmp/{keys.get("RootFS")[0]}.dmg'
    root_fs_key = keys.get('RootFS')[1]

    cmd = (
        'extract',
        root_fs,
        'rootfs.dmg',
        f'-k {root_fs_key}'
    )

    runDmg(cmd)

    root_fs_size = round(getFileSize('rootfs.dmg') / (1024 * 1024))

    p7z_cmd = runCommand(('7z', 'l', 'rootfs.dmg'))
    p7z_out = p7z_cmd[0].splitlines()

    for line in p7z_out:
        if 'usr/' in line:
            mount_name = line.split()[-1].split('/')[0]
            break

    return (root_fs.split('/')[1], mount_name, root_fs_size, root_fs_key)
