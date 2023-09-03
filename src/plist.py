
import plistlib
from pathlib import Path

from .file import getFileHash


def readPlistFile(path):
    with open(path, 'rb') as f:
        return plistlib.load(f)


def writePlistFile(data, path):
    with open(path, 'wb') as f:
        plistlib.dump(data, f)


def serializePlist(data):
    return plistlib.dumps(data)


def deserializePlist(data):
    return plistlib.loads(data)


def getBuildManifestInfo(data):
    data = deserializePlist(data)

    info = {}

    info['buildid'] = data['ProductBuildVersion']
    info['version'] = data['ProductVersion']
    info['device'] = data['SupportedProductTypes'][0]

    build_identities = data['BuildIdentities'][0]

    info['platform'] = build_identities['ApChipID']
    info['codename'] = build_identities['Info']['BuildTrain']
    info['board'] = build_identities['Info']['DeviceClass']

    info['files'] = {}

    files = build_identities['Manifest']

    for filename in files:
        info['files'][filename] = Path(files[filename]['Info']['Path'])

    return info


def initInfoPlist(files, working_dir, ipsw, bundle):
    info_plist = readPlistFile('Info.plist')

    bootchain = info_plist['FirmwarePatches']

    for name in bootchain:
        for file in files:
            if file == name:
                orig = files[name]['orig']
                parent = str(working_dir) + '/'
                path = str(orig).replace(parent, '')

                bootchain[name]['File'] = path
                bootchain[name]['IV'] = files[file]['iv']
                bootchain[name]['Key'] = files[file]['key']

                if 'patch' in files[file]:
                    bootchain[name]['Patch'] = files[file]['patch']
                else:
                    bootchain[name]['Patch'] = ''

    rootfs = files['RootFS']

    info_plist['RootFilesystem'] = str(rootfs['orig'].name)
    info_plist['RootFilesystemSize'] = rootfs['size']
    info_plist['RootFilesystemKey'] = rootfs['key']
    info_plist['RootFilesystemMountVolume'] = rootfs['mount_name']

    info_plist['SHA1'] = getFileHash(ipsw)

    info_plist['Filename'] = ipsw

    tmp = ipsw.split('_')
    del tmp[-1]

    info_plist['Name'] = '_'.join(tmp)

    writePlistFile(info_plist, f'{bundle}/Info.plist')
