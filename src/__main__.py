
from argparse import ArgumentParser
from pathlib import Path

from .iboot import getBootchainReady, patchiBoot
from .ipsw import extractFiles, makeIpsw
from .ipsw_me import downloadArchive, getBuildidForVersion
from .kernel import patchAndCompressKernel
from .plist import getBuildManifestInfo, initInfoPlist
from .utils import binCheck, clean, createBundleFolder
from .wiki import getKeys
from .xpwntool import decryptAll


def go(ipsw):
    supported = ('5.0', '5.0.1', '5.1', '5.1.1')

    binCheck()

    zip_dir = extractFiles(ipsw)

    manifest = getBuildManifestInfo(f'{zip_dir}/BuildManifest.plist')

    device = manifest['device']
    board = manifest['board']
    version = manifest['version']
    buildid = manifest['buildid']
    codename = manifest['codename']

    bundle_name = f'{device}_{board}_{version}_{buildid}.bundle'

    if version in supported:
        createBundleFolder(bundle_name)

        restore_ramdisk = manifest['files']['RestoreRamDisk']['Info']['Path']

        working_dir = getBootchainReady(restore_ramdisk, zip_dir)

        keys = getKeys(codename, buildid, device)
        decryptAll(keys, working_dir)

        # patchRamdisk(bundle_name)
        patchiBoot(keys, bundle_name, version, working_dir)
        patchAndCompressKernel(keys, bundle_name, working_dir)

        initInfoPlist(keys, bundle_name, ipsw, board, zip_dir, working_dir)

        # replaceAsr(keys, f'bundles/{bundle_name}')

        cwd = Path().cwd()

        makeIpsw(f'bundles/{bundle_name}', cwd, zip_dir, working_dir)

        clean((zip_dir, working_dir))

    else:
        print(f'{version} is not fully supported yet!')


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
