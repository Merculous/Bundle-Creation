
from .file import readBinaryFile
from .plist import readPlistFile, writePlistFile

from binpatch.find import find
from binpatch.patch import patchBufferAtIndex


def patchTicketUpdate(data):
    pattern = b'\x06\xf0\x30\xf8\xb0\xb9'

    patch = b'\x00\x00\x00\x00\x16\xe0'

    name = '_ramrod_ticket_update'

    print(f'[#] {name}')

    offset = find(pattern, data)

    if offset is None:
        print(f'Failed to find {name}. Using new pattern...')

        pattern = pattern.replace(b'\x30', b'\x1e')

        offset = find(pattern, data)

        if offset is None:
            raise Exception(f'Still cannot find {name}! Exiting!')

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

    name = 'image verification'

    print(f'[#] {name}')

    offset = find(pattern, data)

    if offset is None:
        print(f'Failed to find {name}. Using new pattern...')

        pattern = b'\x2e\x48\x0e\xf0'

        patch = b'\xfd\xe7\x0e\xf0'

        offset = find(pattern, data)

        if offset is None:
            print(f'Failed to find {name}. Using new pattern...')

            pattern = b'\xdf\xf8\xe0\x00'

            patch = b'\xfd\xe7\xe0\x00'

            offset = find(pattern, data)

            if offset is None:
                print(f'Failed to find {name}. Using new pattern...')

                pattern = b'\x2f\x48\x0c\xf0'

                patch = b'\xfd\xe7\x0c\xf0'

                offset = find(pattern, data)

            if offset is None:
                raise Exception(f'Still cannot find {name}! Exiting!')

    patchBufferAtIndex(data, offset, pattern, patch)

    return data


def patchASR(path):
    data = readBinaryFile(path)

    patchImageVerification(data)

    return data


def updateOptions(optionsPath):
    options = readPlistFile(optionsPath)

    options['UpdateBaseband'] = False

    options['SystemPartitionSize'] += 30

    writePlistFile(options, optionsPath)
