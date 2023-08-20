
from argparse import ArgumentParser

from .iboot import getBootchainReady, patchiBoot
from .ipsw import extractFiles, makeIpsw
from .ipsw_me import downloadArchive, getBuildidForVersion
from .json import writeJSON
from .kernel import patchAndCompressKernel
from .plist import getCodename, getRestoreInfo, initInfoPlist, readPlist
from .utils import binCheck, clean, createBundleFolder
from .wiki import getKeys
from .xpwntool import decryptAll


def go(ipsw):
    supported = ('5.0', '5.0.1', '5.1', '5.1.1')

    clean()
    binCheck()
    extractFiles(ipsw)
    codename = getCodename()
    data = readPlist('.tmp/Restore.plist')
    writeJSON(data, 'Restore.json')
    bundle_name, info = getRestoreInfo('Restore.json')

    if info.get('version') in supported:
        createBundleFolder(bundle_name)
        getBootchainReady(info.get('ramdisk'))
        getKeys(codename, info.get('buildid'), info.get('device'))
        decryptAll()
        # patchRamdisk(bundle_name)
        patchiBoot(bundle_name, info.get('version'))
        patchAndCompressKernel(bundle_name)
        initInfoPlist(bundle_name, ipsw, info.get('board'))
        # replaceAsr(f'bundles/{bundle_name}')
        makeIpsw(f'bundles/{bundle_name}')

    else:
        print(f'{info.get("version")} is not fully supported yet!')

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
