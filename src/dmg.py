
from .command import runDmg, run7zip
from .file import getFileSize


def decryptDmg(src, dst, key):
    cmd = (
        'extract',
        src,
        dst,
        f'-k {key}'
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
