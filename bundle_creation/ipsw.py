
from pathlib import Path

from .archive import Archive
from .decrypt import decryptFiles
from .diff import makePatchFiles
from .dmg import getRootFSInfo, decryptDmg, buildRootFS
from .encrypt import packFiles
from .file import getFileHash, moveFileToPath, removeFile
from .patch import patchFile, patchiBoot, patchKernel, patchRamdisk
from .plist import getBuildManifestInfo, initInfoPlist, readPlistFile
from .temp import makeTempDir
from .utils import listDir, makeDirs, removeDirectory
from .wiki import getKeys
from .xpwntool import decryptXpwn, pack


def getIpswInfo(zip_fd):
    manifest = zip_fd._readPath('BuildManifest.plist')
    manifest_info = getBuildManifestInfo(manifest)
    return manifest_info


def getWorkingDirReady(zip_fd):
    info = getIpswInfo(zip_fd)

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


def makeBundle(ipsw, applelogo=None, recovery=None):
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

    ramdisk = patches['Restore Ramdisk']
    iv = ramdisk['IV']
    key = ramdisk['Key']

    working_ramdisk = f'{working_dir}/{ramdisk["File"]}'

    decrypted = f'{working_ramdisk}.decrypted'

    decryptXpwn(working_ramdisk, decrypted, iv, key)

    patched = patchRamdisk(version, board, decrypted, working_dir)

    packed = f'{patched}.packed'

    pack(patched, packed, working_ramdisk, iv, key)

    moveFileToPath(packed, working_ramdisk)

    removeFile(decrypted)
    removeFile(patched)

    # Gotta do the FS stuff below otherwise idevicerestore won't work.
    # Also idevicerestore must be on a version where it extracts the
    # filesystem, or is in a path where the filesytem and the rest
    # of the ipsw contents are located. I found this out the very
    # hard way. Literally took around 2 months just to figure this out...

    fs = info_plist['RootFilesystem']
    fs_key = info_plist['RootFilesystemKey']

    working_fs = Path(f'{working_dir}/{fs}')

    decrypted_fs = Path(f'{working_dir}/rootfs.dmg')

    decryptDmg(str(working_fs), str(decrypted_fs), fs_key)

    fs_built = Path(f'{working_dir}/built_fs.dmg')

    buildRootFS(str(decrypted_fs), str(fs_built))

    removeFile(working_fs)
    removeFile(decrypted_fs)

    moveFileToPath(fs_built, working_fs)

    new_ipsw = ipsw.replace('Restore', 'Custom')

    with Archive(new_ipsw, 'w') as c:
        c._addPaths(working_dir)
