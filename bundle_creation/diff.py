
import bsdiff4

from .file import writeBinaryFile


def createDiffFromData(old_data, new_data, patch_path):
    # bsdiff4 apparently doesn't like bytearray's :/

    if isinstance(old_data, bytearray):
        old_data = bytes(old_data)

    if isinstance(new_data, bytearray):
        new_data = bytes(new_data)

    data = bsdiff4.diff(old_data, new_data)

    writeBinaryFile(data, patch_path)


def makePatchFiles(old_data, new_data, name, bundle):
    patch_path = f'{bundle}/{name}.patch'

    print(f'Making patch file for: {name}')

    createDiffFromData(old_data, new_data, patch_path)
