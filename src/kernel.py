
from .diff import createBSDiffPatchFile
from .patch import patchFileWithFuzzyPatcher
from .utils import listDir
from .xpwntool import packFile


# FIXME
# Apparently all kernel patching is messed up.
# Figure out what's going wrong.

def patchKernel(bundle, version):
    name = [n.name for n in listDir('kernelcache*.decrypted')][0]

    patch_path = f'kernel\\ patches/{version}/{version}.json'

    patched = f'{name}.patched'

    patchFileWithFuzzyPatcher(name, patched, patch_path)

    packed = f'{patched}.packed'

    packFile(patched, name.replace('.decrypted', ''))

    original = name.replace('.decrypted', '')

    createBSDiffPatchFile(name, packed, f'bundles/{bundle}/{original}.patch')
