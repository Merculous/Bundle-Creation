
from .command import runFuzzyPatcher
from .diff import createBSDiffPatchFile
from .utils import listDir
from .xpwntool import packFile


def patchKernel(bundle, version):
    name = None
    for path in listDir('*.decrypted'):
        if path.name.startswith('kernelcache'):
            name = path.name
            break

    patch_kernel = (
        '--patch',
        f'--delta kernel\\ patches/{version}/{version}.json',
        f'--orig {name}',
        f'--patched {name}.patched'
    )

    runFuzzyPatcher(patch_kernel)

    packed = f'{name}.patched.packed'

    packFile(f'{name}.patched', name.replace('.decrypted', ''))

    original = name.replace('.decrypted', '')

    createBSDiffPatchFile(name, packed, f'bundles/{bundle}/{original}.patch')
