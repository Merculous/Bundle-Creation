
from kernelpatch.patch import Patch

from .file import readBinaryFile, writeBinaryFile


def applyRestorePatches(src, dst):
    data = readBinaryFile(src)
    patched_data = Patch(data).patchKernel()
    writeBinaryFile(patched_data, dst)
