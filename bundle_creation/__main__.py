
from argparse import ArgumentParser

from .ipsw import makeBundle, makeIpsw
from .ipsw_me import downloadArchive, getBuildidForVersion


def main():
    parser = ArgumentParser()

    parser.add_argument('--device', nargs=1)
    parser.add_argument('--version', nargs=1)
    parser.add_argument('--ipsw', nargs=1)
    parser.add_argument('--bootlogo', nargs=1)
    parser.add_argument('--recovery', nargs=1)
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--make', action='store_true')

    args = parser.parse_args()

    if args.ipsw:
        if args.make:
            makeIpsw(args.ipsw[0])
        else:
            makeBundle(args.ipsw[0])

    elif args.device and args.version and args.download:
        buildid = getBuildidForVersion(args.device[0], args.version[0])
        downloadArchive(args.device[0], args.version[0], buildid)

    else:
        parser.print_help()


main()
