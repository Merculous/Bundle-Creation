
from argparse import ArgumentParser

from .iboot import getBootchainReady, patchiBoot
from .ipsw import extractFiles, makeIpsw
from .ipsw_me import getBuildidForVersion, downloadArchive
from .json import writeJSON
from .kernel import patchKernel
from .plist import getCodename, getRestoreInfo, initInfoPlist, readPlist
from .utils import clean, createBundleFolder
from .wiki import getKeys
from .xpwntool import decrypt


def go(ipsw):
    clean()
    extractFiles(ipsw)
    codename = getCodename()
    data = readPlist('.tmp/Restore.plist')
    writeJSON(data, 'Restore.json')
    bundle_name, info = getRestoreInfo('Restore.json')
    createBundleFolder(bundle_name)
    getBootchainReady(info.get('ramdisk'))
    getKeys(codename, info.get('buildid'), info.get('device'))
    decrypt()
    # patchRamdisk(bundle_name)
    patchiBoot(bundle_name, info.get('version'))
    patchKernel(bundle_name, info.get('version'))
    initInfoPlist(bundle_name, ipsw, info.get('board'))
    # replaceAsr(f'bundles/{bundle_name}')
    makeIpsw(f'bundles/{bundle_name}')
    clean()


def main():
    parser = ArgumentParser()

    parser.add_argument('--device', nargs=1)
    parser.add_argument('--version', nargs=1)
    parser.add_argument('--ipsw', nargs=1)
    parser.add_argument('--clean', action='store_true')
    parser.add_argument('--download', action='store_true')

    args = parser.parse_args()

    if args.ipsw:
        go(args.ipsw[0])
    elif args.device and args.version and args.download:
        buildid = getBuildidForVersion(args.device[0], args.version[0])
        downloadArchive(args.device[0], args.version[0], buildid)
    elif args.clean:
        clean()
    else:
        parser.print_help()


main()
