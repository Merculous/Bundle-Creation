
from pathlib import Path

from img3lib.img3 import IMG3

from .archive import Archive
from .bundle import Bundle
from .diff import makePatchFiles
from .dmg import DMG
from .file import getFileSize, moveFileToPath, readBinaryFile, removeFile, writeBinaryFile
from .patch import Patch
from .plist import getBuildManifestInfo, initInfoPlist, readPlistFile, writePlistFile
from .temp import makeTempDir
from .utils import getSHA1, listDir, makeDirs, removeDirectory
from .wiki import getKeys


class IPSW(Archive):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.ipsw_info = self.getIpswInfo()

        self.device = self.ipsw_info['device']
        self.board = self.ipsw_info['board']
        self.version = self.ipsw_info['version']
        self.buildid = self.ipsw_info['buildid']
        self.codename = self.ipsw_info['codename']
        self.platform = self.ipsw_info['platform']

        self.ipsw_name = Path(self.filename).name

        self.keys = getKeys(self.codename, self.buildid, self.device)

    def getIpswInfo(self) -> dict:
        manifest = self._readPath('BuildManifest.plist')
        manifest_info = getBuildManifestInfo(manifest)
        return manifest_info

    def getRequiredFiles(self):
        files = self.ipsw_info['files']

        required = {
            'AppleLogo': None,
            'KernelCache': None,
            'LLB': None,
            'OS': None,
            'RecoveryMode': None,
            'RestoreRamDisk': None,
            'iBEC': None,
            'iBSS': None,
            'iBoot': None
        }

        for file in files:
            for name in required:
                if file == name:
                    required[name] = str(files[name])

        return required

    def extractRequired(self, temp_dir):
        files = self.getRequiredFiles()

        extracted = {}

        for file in files:
            in_path = files[file]
            out_path = f'{temp_dir}/{in_path}'

            self._extractPath(in_path, temp_dir)

            extracted[file] = {
                'path': out_path
            }

            # TODO
            # Remove AppleLogo and RecoveryMode from skip

            skip = ('AppleLogo', 'OS', 'RecoveryMode', 'RestoreRamDisk')

            if file not in skip:
                extracted[file]['data'] = readBinaryFile(out_path)

        return extracted

    def decryptFiles(self, files):
        # Start decryption

        info = {}

        for file in files:
            if file == 'OS':
                # RootFS

                path = files[file]['path']
                decrypted = f'{Path(path).parent}/rootfs'

                filename, iv, key = self.keys[file]

                dmgfile = DMG(path, key)
                dmgfile.decryptFS(decrypted)

                dmgfile.dmg = decrypted

                root = dmgfile.getRootName()

                info[file] = {
                    'path': {
                        'orig': path,
                        'decrypted': decrypted
                    },
                    'key': key,
                    'root': root
                }

                continue

            for name in self.keys:
                filename, iv, key = self.keys[name]

                if '-' in filename and '.dmg' not in filename:
                    filename = f'{filename}.dmg'

                path = files[file]['path']

                if Path(path).name == filename:
                    data = readBinaryFile(path)

                    decrypted = f'{path}.decrypted'

                    img3file = IMG3(data, iv, key)

                    decrypted_data = img3file.decrypt()

                    writeBinaryFile(decrypted_data, decrypted)

                    info[name] = {
                        'path': {
                            'orig': path,
                            'decrypted': decrypted
                        },
                        'data': {
                            'old': data
                        },
                        'iv': iv,
                        'key': key
                    }

        return info

    def applyPatches(self, files):
        for file in files:
            # TODO Applelogo and Recovery

            if file == 'OS':
                # TODO
                # I'm skipping this, as this is the FS.
                # However, I may use this if I'm adding
                # Cydia or other stuff.
                continue

            in_path = files[file]['path']['decrypted']

            out_path = f'{in_path}.patched'

            patch = Patch(in_path, out_path, self.version)

            if file in ('iBSS', 'iBEC', 'LLB', 'iBoot'):
                patched_iBoot = patch.applyiBootPatch(file)

                files[file]['path']['patched'] = patched_iBoot
                files[file]['data']['new'] = readBinaryFile(patched_iBoot)

            elif file == 'KernelCache':
                # FIXME
                # Seems 6.0 kernel patching is missing a bunch
                # of patches, like NOR and others.

                patched_kernel = patch.applyKernelPatch(file)

                files[file]['path']['patched'] = patched_kernel
                files[file]['data']['new'] = readBinaryFile(patched_kernel)

            elif file in ('AppleLogo', 'RecoveryMode'):
                pass

            elif file == 'RestoreRamDisk':
                patched_ramdisk = patch.applyRamdiskPatch(file)

                files[file]['path']['patched'] = patched_ramdisk[0]

                files[file].update(patched_ramdisk[1])

            else:
                raise Exception(f'Extra file included for patching: {file}')

        return files

    def packFiles(self, files):
        for file in files:
            # TODO
            # FS

            if file == 'OS':
                continue

            for name in self.keys:
                if name == file:
                    filename, iv, key = self.keys[name]

                    old_data = bytes(files[file]['data']['old'])

                    files[file]['data']['old'] = old_data

                    new_data = files[file]['data'].get('new', None)

                    if new_data is not None:
                        new_data = bytes(new_data)

                    img3file = IMG3(old_data, iv, key)

                    if name in ('AppleLogo', 'RecoveryMode'):
                        continue

                    elif name == 'LLB':
                        img3file.do3GSLLBHax()

                    elif name == 'RestoreRamDisk':
                        continue

                    else:
                        img3file.replaceData(new_data)

                    new_data = img3file.data

                    files[file]['data']['new'] = new_data

                    writeBinaryFile(new_data, files[file]['path']['patched'])

        return files

    def makeBundle(self, path):
        makeDirs(path)

        # Extract ipsw

        temp_dir = makeTempDir()

        # Instead of using try for ctrl+c handling...
        # I could make a decorator while handles that
        # for any functions I use where we can have
        # leftover files if something gets raised,
        # which will also handling ctrl+c if possible.

        extracted = self.extractRequired(temp_dir)

        decrypted = self.decryptFiles(extracted)

        patches = self.applyPatches(decrypted)

        packed = self.packFiles(patches)

        # Make patch files

        for file in packed:
            if file == 'OS':
                continue

            file_info = packed[file]

            old_data = file_info['data']['old']
            new_data = file_info['data'].get('new', None)

            if file == 'RestoreRamDisk':
                extra = ('asr', 'options', 'restored_external')

                for name in packed[file]:
                    if name not in extra:
                        continue

                    extra_info = packed[file][name]

                    old_data = extra_info['data']['old']
                    new_data = extra_info['data']['new']

                    filename = Path(extra_info['path']['working']).name

                    makePatchFiles(old_data, new_data, filename, path)

                continue

            elif new_data is None:
                continue

            filename = Path(file_info['path']['orig']).name

            makePatchFiles(old_data, new_data, filename, path)

        # Add stuff to Info.plist

        # Give the function some needed data to work with

        stuff = {
            'patched': packed,
            'ipsw_dir': temp_dir,
            'keys': self.keys,
            'ipsw_path': self.filename,
            'ipsw_name': self.ipsw_name
        }

        info_plist = initInfoPlist(stuff)

        plist_path = f'{path}/Info.plist'

        writePlistFile(info_plist, plist_path)

        removeDirectory(temp_dir)

    def makeIpsw(self):
        bundle = Bundle(self.device, self.board, self.version, self.buildid)

        bundle_exists = bundle.findBundle()

        bundle_path = bundle.name

        if not bundle_exists:  # Missing bundle
            self.makeBundle(bundle_path)

        info_plist = readPlistFile(f'{bundle_path}/Info.plist')

        temp_dir = makeTempDir()

        # Extract stuff to modify

        self._extractAll(temp_dir)

        # FS

        print('RootFS setup...')

        fs_name = info_plist['RootFilesystem']
        fs_key = info_plist['RootFilesystemKey']

        fs_working = f'{temp_dir}/{fs_name}'
        fs_decrypted = f'{fs_working}.decrypted'

        dmgfile = DMG(fs_working, fs_key)
        dmgfile.decryptFS(fs_decrypted)

        fs_built = f'{fs_decrypted}.built'

        dmgfile.dmg = fs_decrypted
        dmgfile.buildFS(fs_built)

        removeFile(fs_decrypted)

        moveFileToPath(fs_built, fs_working)

        print('RootFS setup done.')

        patches = info_plist['FirmwarePatches']

        # Ramdisk

        print('Applying ramdisk patches...')

        ramdisk_info = patches['Restore Ramdisk']

        ramdisk_name = ramdisk_info['File']
        ramdisk_iv = ramdisk_info['IV']
        ramdisk_key = ramdisk_info['Key']

        working_ramdisk = f'{temp_dir}/{ramdisk_name}'
        working_ramdisk_data = readBinaryFile(working_ramdisk)

        ramdisk_decrypted = f'{temp_dir}/ramdisk'

        img3file = IMG3(working_ramdisk_data, ramdisk_iv, ramdisk_key)
        ramdisk_decrypted_data = img3file.decrypt()

        writeBinaryFile(ramdisk_decrypted_data, ramdisk_decrypted)

        ramdisk_grow = getFileSize(ramdisk_decrypted) + 6_000_000

        dmgfile.dmg = ramdisk_decrypted
        dmgfile.grow(ramdisk_grow)

        # Options

        options_path = info_plist['RamdiskOptionsPath']

        options_patch = bundle.getPatch('options')

        working_options = f'{temp_dir}/{Path(options_path).name}'

        dmgfile.extractFile(options_path, working_options)

        patcher = Patch(working_options, working_options, None)
        patcher.applyBSPatchToFile(options_patch)

        dmgfile.addPath(working_options, options_path)

        removeFile(working_options)

        # ASR / restored_external

        ramdisk_patches = info_plist['RamdiskPatches']

        for file in ramdisk_patches:
            dmg_path = ramdisk_patches[file]['File']
            patchFile = ramdisk_patches[file]['Patch']

            bundlePatch = bundle.getPatch(patchFile)

            if bundlePatch:
                working_file = f'{temp_dir}/{file}'

                dmgfile.extractFile(dmg_path, working_file)

                patcher.in_path = working_file
                patcher.out_path = working_file
                patcher.applyBSPatchToFile(bundlePatch)

                if file == 'asr':
                    ldid_args = (
                        'bin/ldid',
                        '-S',
                        working_file
                    )

                    dmgfile.runCommand(ldid_args)

                # Hmmm, seems like we HAVE to remove these first

                dmgfile.rm(dmg_path)
                dmgfile.addPath(working_file, dmg_path)
                dmgfile.chmod(100755, dmg_path)

                removeFile(working_file)

        # Replace DATA

        ramdisk_patched = f'{ramdisk_decrypted}.patched'

        ramdisk_patched_data = readBinaryFile(ramdisk_decrypted)

        img3file.replaceData(ramdisk_patched_data)

        writeBinaryFile(img3file.data, ramdisk_patched)

        removeFile(ramdisk_decrypted)

        moveFileToPath(ramdisk_patched, working_ramdisk)

        print('Ramdisk patches done...')

        # Other

        for file in patches:
            if file == 'Restore Ramdisk':
                # Already patched above
                continue

            if file in ('AppleLogo', 'RecoveryMode'):
                # TODO
                continue

            print(f'Patching {file}...')

            file_info = patches[file]

            filename = file_info['File']
            patchfile = file_info['Patch']

            working_file = f'{temp_dir}/{filename}'

            patched = f'{working_file}.patched'

            patcher.in_path = working_file
            patcher.out_path = patched

            patch_path = bundle.getPatch(patchfile)

            patcher.applyBSPatchToFile(patch_path)

            moveFileToPath(patched, working_file)

            print(f'{file} patching done.')

        # Start making the ipsw

        print('Putting everything together...')

        custom_ipsw = self.filename.replace('Restore', 'Custom')

        with Archive(custom_ipsw, 'w') as f:
            f._addPaths(temp_dir)

        removeDirectory(temp_dir)

        print('Done patching ipsw! Have fun :P -Merc')
