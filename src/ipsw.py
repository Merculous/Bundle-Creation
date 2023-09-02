
from zipfile import ZipFile

from .command import run7zip
from .file import moveFileToPath, removeFile
from .plist import readPlist
from .temp import makeTempDir
from .utils import listDir


def extractFiles(archive):
    zip_dir = makeTempDir()

    with ZipFile(archive) as f:
        f.extractall(zip_dir)

    return zip_dir


def makeIpsw(bundle, cwd, zip_dir, working_dir):
    data = readPlist(f'{bundle}/Info.plist')

    packed = listDir('*.packed', working_dir)

    bootchain = data.get('FirmwarePatches')

    # TODO
    # I think I can clean up the loop below

    for thing in bootchain:
        path = bootchain.get(thing)['File']

        for filename in packed:
            prefix = filename.name.split('.')[0]

            if prefix in path:
                zip_path = f'{zip_dir}/{path}'
                moveFileToPath(filename, zip_path)

    # For iTunes users (gets rid of meaningless popup)
    removeFile(f'{zip_dir}/BuildManifest.plist')

    pack_ipsw = (
        'a',
        '-tzip',
        f'{cwd}/custom.ipsw',
        f'{zip_dir}/*'
    )

    run7zip(pack_ipsw)
