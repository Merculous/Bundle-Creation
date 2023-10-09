
from kernelpatch.config import CS_ARCH_ARM, CS_MODE_THUMB
from kernelpatch.patch import Patch

from .file import writeBinaryFile


def applyRestorePatches(src, dst):
    patched_data = Patch(CS_ARCH_ARM, CS_MODE_THUMB, src).patch()
    writeBinaryFile(patched_data, dst)
