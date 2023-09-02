
import plistlib
from pathlib import Path

from .dmg import getRootFSInfo
from .file import getFileHash


def readPlist(path):
    with open(path, 'rb') as f:
        return plistlib.load(f)


def writePlist(data, path):
    with open(path, 'wb') as f:
        plistlib.dump(data, f)


def getCodename(path):
    data = readPlist(f'{path}/BuildManifest.plist')

    stuff = data.get('BuildIdentities')[0]
    info = stuff.get('Info')
    codename = info.get('BuildTrain')

    return codename


def getRestoreInfo(path):
    data = readPlist(path)

    platform = data.get('DeviceMap')[0]['Platform']

    info = {
        'device': data.get('ProductType'),
        'board': data.get('DeviceMap')[0]['BoardConfig'],
        'version': data.get('ProductVersion'),
        'buildid': data.get('ProductBuildVersion'),
        'platform': platform,
        'ramdisk': data.get('RamDisksByPlatform')[platform]['User']
    }

    things = (
        info.get('device'),
        info.get('board'),
        info.get('version'),
        info.get('buildid')
    )

    bundle_name = f'{things[0]}_{things[1]}_{things[2]}_{things[3]}.bundle'

    return (bundle_name, info)

# FIXME
# This function below is garbage and needs to be updated


def initInfoPlist(keys, bundle, ipsw, board, zip_dir, working_dir):
    plist_data = readPlist('Info.plist')

    dfu_path = 'Firmware/dfu'
    other_path = f'Firmware/all_flash/all_flash.{board}.production'

    bootchain_paths = {
        'iBSS': f'{dfu_path}/iBSS.{board}.RELEASE.dfu',
        'iBEC': f'{dfu_path}/iBEC.{board}.RELEASE.dfu',
        'LLB': f'{other_path}/LLB.{board}.RELEASE.img3',
        'iBoot': f'{other_path}/iBoot.{board}.RELEASE.img3'
    }

    plist_data['Filename'] = ipsw
    plist_data['Name'] = ipsw.split('_Restore.ipsw')[0]

    bootchain = plist_data.get('FirmwarePatches')

    kernel = bootchain.get('KernelCache')
    kernel['File'] = keys.get('kernelcache')[0]
    kernel['IV'] = keys.get('kernelcache')[1]
    kernel['Key'] = keys.get('kernelcache')[2]
    kernel['Patch'] = f'{keys.get("kernelcache")[0]}.patch'

    ramdisk = bootchain.get('Restore Ramdisk')
    ramdisk['File'] = f'{keys.get("ramdisk")[0]}.dmg'
    ramdisk['IV'] = keys.get('ramdisk')[1]
    ramdisk['Key'] = keys.get('ramdisk')[2]

    ibss = bootchain.get('iBSS')
    ibss['File'] = bootchain_paths.get('iBSS')
    ibss['IV'] = keys.get('iBSS')[1]
    ibss['Key'] = keys.get('iBSS')[2]
    ibss['Patch'] = Path(ibss.get("File")).name.replace(".dfu", ".patch")

    ibec = bootchain.get('iBEC')
    ibec['File'] = bootchain_paths.get('iBEC')
    ibec['IV'] = keys.get('iBEC')[1]
    ibec['Key'] = keys.get('iBEC')[2]
    ibec['Patch'] = Path(ibec.get("File")).name.replace(".dfu", ".patch")

    llb = bootchain.get('LLB')
    llb['File'] = bootchain_paths.get('LLB')
    llb['IV'] = keys.get('LLB')[1]
    llb['Key'] = keys.get('LLB')[2]
    llb['Patch'] = Path(llb.get("File")).name.replace(".img3", ".patch")

    iboot = bootchain.get('iBoot')
    iboot['File'] = bootchain_paths.get('iBoot')
    iboot['IV'] = keys.get('iBoot')[1]
    iboot['Key'] = keys.get('iBoot')[2]
    iboot['Patch'] = Path(iboot.get("File")).name.replace(".img3", ".patch")

    # Check if there are files that aren't encrypted
    # If so, then if there's a "Not Encrypted" string
    # we change it to None, or json's equivalent: null

    for name in bootchain:
        iv = bootchain.get(name)['IV']
        k = bootchain.get(name)['Key']

        thingy = 'Not Encrypted'

        if iv == thingy or k == thingy:
            bootchain[name]['IV'] = ''
            bootchain[name]['Key'] = ''

    plist_data['FirmwarePatches'] = bootchain

    ipsw_sha1 = getFileHash(ipsw)

    plist_data['SHA1'] = ipsw_sha1

    info_path = f'bundles/{bundle}/Info.plist'

    fs_info = getRootFSInfo(keys, zip_dir, working_dir)

    plist_data['RootFilesystem'] = fs_info[0]
    plist_data['RootFilesystemMountVolume'] = fs_info[1]
    plist_data['RootFilesystemSize'] = fs_info[2]
    plist_data['RootFilesystemKey'] = fs_info[3]

    writePlist(plist_data, info_path)
