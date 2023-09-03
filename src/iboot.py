
from .command import runiBoot32Patcher


def useiBoot32Patcher(src, dst, boot_args=None):
    cmd = [
        src,
        dst,
        '--rsa'
    ]

    if boot_args:
        add = (
            '--debug',
            '-b',
            '"' + ' '.join(boot_args) + '"'
        )

        cmd.extend(add)

    return runiBoot32Patcher(cmd)
