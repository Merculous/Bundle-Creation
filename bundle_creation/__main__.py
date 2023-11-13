
from argparse import ArgumentParser

from .ipsw import makeIpsw
from .ipsw_me import downloadArchive, getBuildidForVersion
from .utils import binCheck


def main():
    parser = ArgumentParser()

    parser.add_argument('--device', nargs=1)
    parser.add_argument('--version', nargs=1)
    parser.add_argument('--ipsw', nargs=1)
    parser.add_argument('--applelogo', nargs=1)
    parser.add_argument('--recovery', nargs=1)
    parser.add_argument('--jailbreak', action='store_true')
    parser.add_argument('--download', action='store_true')

    args = parser.parse_args()

    if args.ipsw:
        binCheck()

        ipsw = args.ipsw[0]
        applelogo = None
        recovery = None
        jailbreak = args.jailbreak

        if args.applelogo:
            applelogo = args.applelogo[0]

        if args.recovery:
            recovery = args.recovery[0]

        makeIpsw(ipsw, applelogo, recovery, jailbreak)

    elif args.device and args.version and args.download:
        buildid = getBuildidForVersion(args.device[0], args.version[0])
        downloadArchive(args.device[0], args.version[0], buildid)

    else:
        parser.print_help()


main()
