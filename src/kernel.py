
from pathlib import Path

from kernelpatch.patch import Patch

from .diff import createBSDiffPatchFile
from .file import moveFileToPath, readBinaryFile, writeBinaryFile
from .utils import listDir
from .xpwntool import decryptFile, packFile


def patchAndCompressKernel(keys, bundle, working_dir):
    path, iv, key = keys['kernelcache']

    name = [n for n in listDir('kernelcache*.decrypted', working_dir)][0]

    patched = f'{name}.patched'

    decrypted_data = readBinaryFile(name)

    patched_data = Patch(decrypted_data).patchKernel()

    writeBinaryFile(patched_data, patched)

    ########################################################################

    # The kernel must be compressed in order to boot.
    # This awful code does that. I'm not sure how to compress with xpwntool,
    # so only way I know for now is just to encrypt again, which will compress
    # the kernel. All we have to do is decrypt again, and make use of the
    # -decrypt argument so we don't strip any img3 or lzss headers.

    encrypted_compressed = f'{patched}.encrypted.compressed'

    path = f'{working_dir}/{path}'

    packFile(patched, encrypted_compressed, path, iv, key)

    decrypted_compressed = f'{patched}.decrypted.compressed'

    decryptFile(encrypted_compressed, decrypted_compressed, iv, key, False)

    packed = f'{decrypted_compressed}.packed'

    moveFileToPath(decrypted_compressed, packed)

    ########################################################################

    bspatch_path = f'bundles/{bundle}/{Path(path).name}.patch'

    createBSDiffPatchFile(path, packed, bspatch_path)
