
from zipfile import ZipFile

from .command import runShellCommand
from .file import moveFileToPath, removeFile
from .plist import readPlist
from .utils import makeDirs, listDir


def extractFiles(archive):
    makeDirs('.tmp')

    with ZipFile(archive) as f:
        f.extractall('.tmp')


def makeIpsw(bundle):
    data = readPlist(f'{bundle}/Info.plist')

    packed = listDir('*.packed')

    bootchain = data.get('FirmwarePatches')

    for thing in bootchain:
        path = bootchain.get(thing)['File']

        for filename in packed:
            prefix = filename.name.split('.')[0]
            if prefix in path:
                path = f'.tmp/{path}'
                moveFileToPath(filename, path)

    # For iTunes users (gets rid of meaningless popup)
    removeFile('.tmp/BuildManifest.plist')

    pack = (
        'cd',
        '.tmp',
        '&&',
        '7z',
        'a',
        '-tzip',
        '../custom.ipsw',
        '*'
    )

    runShellCommand(pack)
