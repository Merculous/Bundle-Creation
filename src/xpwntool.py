
from .command import runXpwntool
from .keys import readKeys
from .utils import listDir


def decrypt():
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

    cmds = []

    for name, kv in info.items():
        iv, k = kv
        if len(iv) == 32 and len(k) == 64:
            cmd = (
                name,
                f'{name}.decrypted',
                f'-iv {iv}',
                f'-k {k}'
            )
            cmds.append(cmd)
        else:
            cmd = (
                name,
                f'{name}.decrypted'
            )
            cmds.append(cmd)

    for cmd in cmds:
        # FIXME
        # Weird, this only works if ran inside a shell
        runXpwntool(cmd)


def packFile(path, template, pwn_llb=False):
    cmd = [
        path,
        f'{path}.packed',
        '-t',
        template
    ]

    if pwn_llb:
        cmd.append('-xn8824k')

    return runXpwntool(cmd)
