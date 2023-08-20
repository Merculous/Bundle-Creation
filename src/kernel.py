
from .diff import createBSDiffPatchFile
from .file import moveFileToPath
from .keys import readKeys
from .utils import listDir
from .xpwntool import decryptFile, packFile

from kernelpatch.patch import patchKernel


def patchAndCompressKernel(bundle):
    keys = readKeys()

    path, iv, key = keys['kernelcache']

    name = [n.name for n in listDir('kernelcache*.decrypted')][0]

    patched = f'{name}.patched'

    patchKernel(name, patched)

    ########################################################################

    # The kernel must be compressed in order to boot.
    # This awful code does that. I'm not sure how to compress with xpwntool,
    # so only way I know for now is just to encrypt again, which will compress
    # the kernel. All we have to do is decrypt again, and make use of the
    # -decrypt argument so we don't strip any img3 or lzss headers.

    encrypted_compressed = f'{patched}.encrypted.compressed'

    packFile(patched, encrypted_compressed, path, iv, key)

    decrypted_compressed = f'{patched}.decrypted.compressed'

    decryptFile(encrypted_compressed, decrypted_compressed, iv, key, False)

    packed = f'{decrypted_compressed}.packed'

    moveFileToPath(decrypted_compressed, packed)

    ########################################################################

    bspatch_path = f'bundles/{bundle}/{path}.patch'

    createBSDiffPatchFile(path, packed, bspatch_path)
