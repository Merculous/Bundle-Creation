
from argparse import ArgumentParser

from .iboot import getBootchainReady, patchiBoot
from .ipsw import extractFiles, makeIpsw
from .json import writeJSON
from .kernel import patchKernel
from .plist import getCodename, getRestoreInfo, initInfoPlist, readPlist
from .utils import clean, createBundleFolder
from .wiki import getKeys
from .xpwntool import decrypt


def main():
    parser = ArgumentParser()

    parser.add_argument('--clean', action='store_true')
    parser.add_argument('--ipsw', nargs=1)

    args = parser.parse_args()

    if args.ipsw:
        clean()
        extractFiles(args.ipsw[0])
        codename = getCodename()
        data = readPlist('.tmp/Restore.plist')
        writeJSON(data, 'Restore.json')
        bundle_name, info = getRestoreInfo('Restore.json')
        createBundleFolder(bundle_name)
        getBootchainReady(info.get('ramdisk'))
        getKeys(codename, info.get('buildid'), info.get('device'))
        decrypt()
        # patchRamdisk(bundle_name)
        patchiBoot(bundle_name)
        patchKernel(bundle_name, info.get('version'))
        initInfoPlist(bundle_name, args.ipsw[0], info.get('board'))
        # replaceAsr(f'bundles/{bundle_name}')
        makeIpsw(f'bundles/{bundle_name}')
        clean()
    elif args.clean:
        clean()
    else:
        parser.print_help()


main()
