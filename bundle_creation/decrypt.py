from pathlib import Path

from .dmg import decryptDmg
from .utils import listDir
from .xpwntool import decryptXpwn


def decryptFiles(keys, working_dir):
    dir_contents = listDir('*', working_dir, True)

    info = {}

    for path in dir_contents:
        for name, v in keys.items():
            if len(v) == 3:
                filename, iv, key = v

                if filename[0] == '0':
                    filename = f'{filename}.dmg'

                if filename == path.name:
                    decrypted_path = Path(f'{path}.decrypted')

                    decryptXpwn(str(path), str(decrypted_path), iv, key)

                    info[name] = {
                        'orig': path,
                        'decrypted': decrypted_path,
                        'iv': iv,
                        'key': key
                    }

            elif len(v) == 2:
                # Make sure this is RootFS
                if name == 'RootFS':
                    filename, key = v

                    filename = f'{filename}.dmg'

                    if filename == path.name:
                        decrypted_path = Path(f'{path}.decrypted')

                        decryptDmg(str(path), str(decrypted_path), key)

                        info[name] = {
                            'orig': path,
                            'decrypted': decrypted_path,
                            'key': key
                        }

            else:
                raise Exception(v)

    return info
