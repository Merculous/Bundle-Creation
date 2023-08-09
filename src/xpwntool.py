
from .command import runXpwntool
from .keys import readKeys
from .utils import listDir


def decryptFile(in_path, out_path, iv=None, key=None, unpack=True):
    cmd = [
        in_path,
        out_path
    ]

    if iv:
        cmd.append(f'-iv {iv}')

    if key:
        cmd.append(f'-k {key}')

    if not unpack:
        cmd.append('-decrypt')

    return runXpwntool(cmd)


def decryptAll():
    keys = readKeys()

    things = ('dmg', 'dfu', 'img3', 'kernelcache')

    paths = []

    for thing in things:
        matches = listDir(f'*{thing}*')

        if matches:
            paths.extend(matches)

    info = {}

    for path in paths:
        iv, k = None, None

        if path.name.endswith('.dmg'):
            filename, iv, k = keys.get('ramdisk')
            info.update({path.name: [iv, k]})

        for name in keys:
            if name in path.name:
                filename, iv, k = keys.get(name)
                info.update({path.name: [iv, k]})

    for name, kv in info.items():
        iv, k = kv

        decrypted = f'{name}.decrypted'

        if len(iv) == 32 and len(k) == 64:
            decryptFile(name, decrypted, iv, k)

        else:
            decryptFile(name, decrypted)


def packFile(in_path, out_path, template, iv=None, key=None, pwn_llb=False):
    cmd = [
        in_path,
        out_path,
        '-t',
        template
    ]

    if iv:
        cmd.append(f'-iv {iv}')

    if key:
        cmd.append(f'-k {key}')

    if pwn_llb:
        cmd.append('-xn8824k')

    return runXpwntool(cmd)
