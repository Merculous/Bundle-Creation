
from .diff import createBSDiffPatchFile
from .patch import patchFileWithFuzzyPatcher
from .utils import listDir
from .xpwntool import packFile


# FIXME
# Apparently all kernel patching is messed up.
# Figure out what's going wrong.

def patchKernel(bundle, version):
    name = None
    for path in listDir('*.decrypted'):
        if path.name.startswith('kernelcache'):
            name = path.name
            break

    patch_path = f'kernel\\ patches/{version}/{version}.json'

    patchFileWithFuzzyPatcher(name, f'{name}.patched', patch_path)

    packed = f'{name}.patched.packed'

    packFile(f'{name}.patched', name.replace('.decrypted', ''))

    original = name.replace('.decrypted', '')

    createBSDiffPatchFile(name, packed, f'bundles/{bundle}/{original}.patch')
