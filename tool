#!/usr/bin/env python3

import json
import plistlib
from argparse import ArgumentParser
from pathlib import Path
from zipfile import ZipFile

import bsdiff4


def main() -> None:
    parser = ArgumentParser()

    parser.add_argument('--ipsw', nargs=1)

    args = parser.parse_args()

    if args.ipsw:
        print(args.ipsw[0])
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
