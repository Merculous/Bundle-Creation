
from .command import runShellCommand
from .utils import listDir

# FFS xpwntool won't work correctly unless I'm using shell :/


def decryptFile(in_path, out_path, iv=None, key=None, unpack=True):
    cmd = [
        'bin/xpwntool',
        in_path,
        out_path
    ]

    if iv:
        cmd.append(f'-iv {iv}')

    if key:
        cmd.append(f'-k {key}')

    if not unpack:
        cmd.append('-decrypt')

    return runShellCommand(' '.join(cmd))


def decryptAll(keys, working_dir):
    things = ('dmg', 'dfu', 'img3', 'kernelcache')

    paths = []

    for thing in things:
        matches = listDir(f'*{thing}*', working_dir)

        if matches:
            paths.extend(matches)

    info = {}

    for path in paths:
        iv, k = None, None

        if path.name.endswith('.dmg'):
            filename, iv, k = keys.get('ramdisk')
            info.update({path.name: [iv, k, str(path)]})

        for name in keys:
            if name in path.name:
                filename, iv, k = keys.get(name)
                info.update({path.name: [iv, k, str(path)]})

    for name, kv in info.items():
        iv, k, path = kv

        decrypted = f'{path}.decrypted'

        if len(iv) == 32 and len(k) == 64:
            decryptFile(path, decrypted, iv, k)

        else:
            decryptFile(path, decrypted)


def packFile(in_path, out_path, template, iv=None, key=None, pwn_llb=False):
    cmd = [
        'bin/xpwntool',
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

    return runShellCommand(' '.join(cmd))
