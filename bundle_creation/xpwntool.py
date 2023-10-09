
from .command import runXpwntool


def decryptXpwn(src, dst, iv, key, unpack=True):
    cmd = [
        src,
        dst
    ]

    if iv == 'Not Encrypted':
        iv, key = '', ''

    else:
        if iv and key:
            cmd.extend((f'-iv {iv}', f'-k {key}'))
        else:
            raise Exception(f'iv: {iv}\nkey:{key}')

    if not unpack:
        cmd.append('-decrypt')

    return runXpwntool(cmd)


def pack(src, dst, template, iv, key, platform=None, pwn_llb=False):
    # [-x24k|-xn8824k]

    # iPod 8720 3GS 8920

    cmd = [
        src,
        dst,
        '-t',
        template
    ]

    if iv == 'Not Encrypted':
        iv, key = '', ''

    else:
        if iv and key:
            cmd.extend((f'-iv {iv}', f'-k {key}'))
        else:
            raise Exception(f'iv: {iv}\nkey:{key}')

    if platform and pwn_llb:
        if platform == '0x8720':
            cmd.append('-x24k')
        elif platform == '0x8920':
            cmd.append('-xn8824k')

    return runXpwntool(cmd)
