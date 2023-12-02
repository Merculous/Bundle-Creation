
import plistlib
from pathlib import Path

from bundle_creation.utils import listDir

from .file import getFileHash, getFileSize


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


def initInfoPlist(stuff):
    info_plist = readPlistFile('Info.plist')

    patches = info_plist['FirmwarePatches']

    # Add stuff to Filesystem Jailbreak section
    # It includes fstab

    ipsw_dir_contents = listDir('*', stuff['ipsw_dir'], True)

    for patch in patches:
        if patch in ('AppleLogo', 'RecoveryMode'):
            # TODO
            continue

        if patch == 'Restore Ramdisk':
            # This is done later
            continue

        for name in stuff['keys']:
            if name == patch:
                filename, iv, key = stuff['keys'][name]

                for file in ipsw_dir_contents:
                    sep = f'{str(stuff["ipsw_dir"])}/'

                    full_path = Path(str(file).split(sep)[1])

                    if '.decrypted' in full_path.name:
                        continue

                    if filename == full_path.name:
                        patch_info = patches[patch]

                        patch_info['File'] = str(full_path)
                        patch_info['IV'] = iv
                        patch_info['Key'] = key
                        patch_info['Patch'] = f'{full_path.name}.patch'

    # Do ramdisk

    ramdisk_info = patches['Restore Ramdisk']

    ramdisk_name, ramdisk_iv, ramdisk_key = stuff['keys']['RestoreRamDisk']

    if not ramdisk_name.endswith('.dmg'):
        ramdisk_name = f'{ramdisk_name}.dmg'

    ramdisk_info['File'] = ramdisk_name
    ramdisk_info['IV'] = ramdisk_iv
    ramdisk_info['Key'] = ramdisk_key

    options = stuff['patched']['RestoreRamDisk']['options']['path']['dmg']

    info_plist['RamdiskOptionsPath'] = options

    # ipsw

    info_plist['SHA1'] = getFileHash(stuff['ipsw_path'])
    info_plist['Filename'] = stuff['ipsw_name']
    info_plist['Name'] = stuff['ipsw_name'].replace('_Restore.ipsw', '')

    # FS

    fs_info = stuff['patched']['OS']

    info_plist['RootFilesystem'] = Path(fs_info['path']['orig']).name

    fs_size = getFileSize(fs_info['path']['decrypted'])

    # Convert to MB

    fs_size = fs_size // (1 << 20)

    info_plist['RootFilesystemSize'] = fs_size

    info_plist['RootFilesystemKey'] = fs_info['key']

    info_plist['RootFilesystemMountVolume'] = fs_info['root']

    return info_plist
