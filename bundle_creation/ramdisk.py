
import plistlib

from .file import readBinaryFile

from binpatch.find import find
from binpatch.patch import patchBufferAtIndex


def patchTicketUpdate(data):
    # FIXME
    # This doesn't work on 6.0

    pattern = b'\x06\xf0\x30\xf8\xb0\xb9'

    patch = b'\x00\x00\x00\x00\x16\xe0'

    print('[#] ticket update')

    offset = find(pattern, data)

    patchBufferAtIndex(data, offset, pattern, patch)

    return data


def patchWriteImage3Data(data):
    pattern = b'\x61\x40\x08\x43\x0a\xd1'

    patch = b'\x61\x40\x08\x43\x0a\xe0'

    print('[#] write_image3_data')

    offset = find(pattern, data)

    patchBufferAtIndex(data, offset, pattern, patch)

    return data


def patchRestoredExternal(path):
    data = readBinaryFile(path)

    patchTicketUpdate(data)

    patchWriteImage3Data(data)

    return data


def patchImageVerification(data):
    pattern = b'\x4d\xf6\x6a\x30'

    patch = b'\xf4\xe7\x6a\x30'

    print('[#] image verification')

    offset = find(pattern, data)

    patchBufferAtIndex(data, offset, pattern, patch)

    return data


def patchASR(path):
    data = readBinaryFile(path)

    patchImageVerification(data)

    return data


def updateOptions(optionsPath):
    with open(optionsPath, 'rb+') as f:
        data = plistlib.load(f)

        data['UpdateBaseband'] = False

        # data['CreateFilesystemPartitions'] = True

        # data['SystemPartitionSize'] += 50

        plistlib.dump(data, f)
