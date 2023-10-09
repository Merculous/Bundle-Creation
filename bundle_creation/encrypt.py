
from pathlib import Path

from .xpwntool import pack


def packFiles(files, platform):
    for name in files:
        if 'patched' in files[name]:
            orig = str(files[name]['orig'])
            patched = str(files[name]['patched'])
            packed = f'{patched}.packed'
            iv = files[name]['iv']
            key = files[name]['key']

            if name == 'LLB':
                pack(
                    patched,
                    packed,
                    orig,
                    iv,
                    key,
                    platform,
                    True
                )
            else:
                pack(
                    patched,
                    packed,
                    orig,
                    iv,
                    key
                )

            files[name]['packed'] = Path(packed)

    return files
