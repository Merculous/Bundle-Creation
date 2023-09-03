
from pathlib import Path

from .archive import Archive
from .decrypt import decryptFiles
from .diff import makePatchFiles
from .dmg import getRootFSInfo
from .encrypt import packFiles
from .file import getFileHash
from .patch import patchFile, patchiBoot, patchKernel
from .plist import getBuildManifestInfo, initInfoPlist, readPlistFile
from .temp import makeTempDir
from .utils import listDir, makeDirs, removeDirectory
from .wiki import getKeys


def getIpswInfo(zip_fd):
    manifest = zip_fd._readPath('BuildManifest.plist')
    manifest_info = getBuildManifestInfo(manifest)
    return manifest_info


def getWorkingDirReady(zip_fd):
    info = getIpswInfo(zip_fd)

    supported = ('5.0', '5.0.1', '5.1', '5.1.1')

    if info['version'] not in supported:
        raise Exception(f'{info["version"]} is not supported yet!')

    files = info['files']

    needed = (
        files['KernelCache'],
        files['LLB'],
        files['OS'],
        files['RestoreRamDisk'],
        files['iBEC'],
        files['iBSS'],
        files['iBoot']
    )

    paths = zip_fd._listPaths()

    working_dir = makeTempDir()

    for path in paths:
        file = Path(path.filename)

        for required in needed:
            if file == required:
                zip_fd._extractPath(path, working_dir)

    return working_dir


def makeBundle(ipsw):
    with Archive(ipsw) as zip_r:
        info = getIpswInfo(zip_r)
        working_dir = getWorkingDirReady(zip_r)

    codename = info['codename']
    buildid = info['buildid']
    device = info['device']
    version = info['version']
    board = info['board']
    platform = info['platform']

    keys = getKeys(codename, buildid, device)

    shared_info = decryptFiles(keys, working_dir)

    shared_info = patchiBoot(shared_info, version)

    shared_info = patchKernel(shared_info)

    shared_info = packFiles(shared_info, platform)

    shared_info = getRootFSInfo(shared_info)

    bundle = f'bundles/{device}_{board}_{version}_{buildid}.bundle'
    makeDirs(bundle)

    shared_info = makePatchFiles(shared_info, bundle)

    initInfoPlist(shared_info, working_dir, ipsw, bundle)

    removeDirectory(working_dir)


def makeIpsw(ipsw):
    with Archive(ipsw) as t:
        info = getIpswInfo(t)

    buildid = info['buildid']
    device = info['device']
    version = info['version']
    board = info['board']

    bundle = f'{device}_{board}_{version}_{buildid}.bundle'

    match = None

    matches1 = [b for b in listDir('*.bundle', 'bundles') if b.name == bundle]

    if not matches1:
        makeBundle(ipsw)

        matches2 = [b for b in listDir('*.bundle', 'bundles') if b.name == bundle]

        if not matches2:
            raise Exception('We tried to make a bundle but it does not exist!')

        match = matches2[0]

    else:
        match = matches1[0]

    info_plist = readPlistFile(f'{match}/Info.plist')

    ipsw_hash = getFileHash(ipsw)
    plist_hash = info_plist['SHA1']

    if ipsw_hash != plist_hash:
        raise Exception(f'Expected SHA1 {plist_hash}\nGot {ipsw_hash}')

    working_dir = makeTempDir()

    with Archive(ipsw) as r:
        r._extractAll(working_dir)

    patches = info_plist['FirmwarePatches']

    for name in patches:
        if 'Patch' in patches[name]:
            patch = patches[name]['Patch']

            if patch:
                path = patches[name]['File']
                file_path = f'{working_dir}/{path}'

                patch_path = f'{match}/{patch}'

                patchFile(file_path, patch_path)

    new_ipsw = ipsw.replace('Restore', 'Custom')

    with Archive(new_ipsw, 'w') as c:
        c._addPaths(working_dir)
