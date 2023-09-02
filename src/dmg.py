
from .command import runCommandWithOutput, runShellCommand
from .file import getFileSize


def getRootFSInfo(keys, zip_dir, working_dir):
    root_fs = f'{zip_dir}/{keys.get("RootFS")[0]}.dmg'
    root_fs_key = keys.get('RootFS')[1]

    decrypted_path = f'{working_dir}/rootfs.dmg'

    cmd = (
        'bin/dmg',
        'extract',
        root_fs,
        decrypted_path,
        f'-k {root_fs_key}'
    )

    runShellCommand(' '.join(cmd))

    root_fs_size = round(getFileSize(decrypted_path) / (1024 * 1024))

    p7z_cmd = runCommandWithOutput(('bin/7z', 'l', decrypted_path))
    p7z_out = p7z_cmd[0].splitlines()

    for line in p7z_out:
        if 'usr/' in line:
            mount_name = line.split()[-1].split('/')[0]
            break

    return (root_fs.split('/')[1], mount_name, root_fs_size, root_fs_key)
