
from pathlib import Path

from binpatch.find import find
from binpatch.patch import patchBufferAtIndex
from bsdiff4 import file_patch
from kernelpatch.config import CS_ARCH_ARM, CS_MODE_THUMB
from kernelpatch.patch import Patch as KernelPatch

from bundle_creation.plist import readPlistFile, serializePlist, writePlistFile

from .command import Command
from .dmg import DMG
from .file import copyFileToPath, getFileSize, readBinaryFile, writeBinaryFile


class Patch(Command):
    def __init__(self, in_path, out_path, version) -> None:
        self.in_path = in_path
        self.out_path = out_path
        self.version = version

        if version:
            self.version_prefix = int(self.version.split('.')[0])

        self.working_dir = Path(self.in_path).parent

    def applyBSPatchToFile(self, patchFile):
        file_patch(self.in_path, self.out_path, patchFile)

    def applyiBootPatch(self, name):
        stage1canUseBootArgs = False

        if self.version_prefix <= 4:
            stage1canUseBootArgs = True

        # TODO Custom boot-args

        cmd_args = [
            'bin/iBoot32Patcher',
            self.in_path,
            self.out_path,
            '--rsa'
        ]

        bootArgs = [
            '-v',
            'serial=3',
            'debug=0x2014e',
            'cs_enforcement_disable=1'
        ]

        # iBoot32Patcher LITERALLY requires everything after "-b"
        # as a string literal. So here, I cannot use boot-args that
        # are a list of strings, and instead boot-args as literally
        # just a string with all of them put together...

        bootArgs = ' '.join(bootArgs)

        if name == 'iBSS':
            newCmdArgs = (
                '--debug',
                '-b',
                f'nand-enable-reformat=1 rd=md0 {bootArgs}'
            )

            cmd_args.extend(newCmdArgs)

        if name == 'iBEC':
            if stage1canUseBootArgs is False:
                # We are iOS >= 5

                newCmdArgs = (
                    '--debug',
                    '-b',
                    f'nand-enable-reformat=1 rd=md0 {bootArgs}'
                )

                cmd_args.extend(newCmdArgs)

        if name == 'iBoot':
            newCmdArgs = (
                '--debug',
                '-b',
                bootArgs
            )

            cmd_args.extend(newCmdArgs)

        cmd = self.runCommand(cmd_args)

        if cmd[1] != 1:
            raise Exception('iBoot32Patcher seems to have failed!')

        return self.out_path

    def applyKernelPatch(self, name):
        patched_data = KernelPatch(
            CS_ARCH_ARM, CS_MODE_THUMB, self.in_path).patch()

        writeBinaryFile(patched_data, self.out_path)

        return self.out_path

    def findAndPatch(self, name, data, old, new):
        print(f'[*] {name}')

        offset = find(old, data)

        if offset is None:
            raise Exception(f'Failed to patch at offset: {offset}')

        print(f'[#] {name}')
        print(f'Patching data at offset: {offset}')

        patchBufferAtIndex(data, offset, old, new)

    def patchWriteImage3Data(self, data):
        # SCAB / APTicket

        name = 'write_image3_data'

        old = None
        new = None

        if self.version in ('6.0'):
            old = b'\x61\x40\x08\x43\x0a\xd1'
            new = b'\x61\x40\x08\x43\x0a\xe0'

        else:
            pass

        self.findAndPatch(name, data, old, new)

    def patchRamrodTicketUpdate(self, data):
        name = 'ramrod_ticket_update'

        old = None
        new = None

        if self.version in ('6.0'):
            old = b'\x06\xf0\x1e\xf8\xb0\xb9'
            new = b'\x00\x00\x00\x00\x16\xe0'

        else:
            pass

        self.findAndPatch(name, data, old, new)

    def patchRestoredExternal(self):
        file = 'restored_external'

        path = f'/usr/local/bin/{file}'

        working_path = f'{self.working_dir}/{file}'

        self.dmg.extractFile(path, working_path)

        data = readBinaryFile(working_path)

        info = {
            file: {
                'path': {
                    'working': working_path,
                    'dmg': path
                },
                'data': {
                    'old': data,
                    'new': data[:]  # Copy data for patching
                }
            }
        }

        newData = info[file]['data']['new']

        self.patchRamrodTicketUpdate(newData)
        self.patchWriteImage3Data(newData)

        writeBinaryFile(newData, working_path)

        return info

    def patchImageSignatureVerification(self, data):
        name = 'image signature verification'

        old = None
        new = None

        if self.version in ('3.0'):
            old = b'\x2f\x48\x06\xf0\x06\xe8'
            new = b'\xfd\xe7\x06\xf0\x06\xe8'

        elif self.version in ('3.1.3'):
            old = b'\x2f\x48\x0c\xf0\xe8\xed'
            new = b'\xfd\xe7\x0c\xf0\xe8\xed'

        elif self.version in ('6.0'):
            old = b'\x4d\xf6\x6a\x30'
            new = b'\xfa\xe7\x6a\x30'

        else:
            pass

        self.findAndPatch(name, data, old, new)

    def patchASR(self):
        file = 'asr'

        path = f'/usr/sbin/{file}'

        working_path = f'{self.working_dir}/{file}'

        self.dmg.extractFile(path, working_path)

        data = readBinaryFile(working_path)

        info = {
            file: {
                'path': {
                    'working': working_path,
                    'dmg': path
                },
                'data': {
                    'old': data,
                    'new': data[:]  # Copy data for patching
                }
            }
        }

        newData = info[file]['data']['new']

        self.patchImageSignatureVerification(newData)

        writeBinaryFile(newData, working_path)

        return info

    def patchOptions(self, jailbreak=False):
        # We search for the plist since it can either
        # be "options.plist" or "options.(board).plist"

        path = '/usr/local/share/restore'

        path_contents = self.dmg.ls(path)[2].splitlines()

        plist_name = None

        for line in path_contents:
            file = line.split()[-1]

            if file.startswith('options') and file.endswith('.plist'):
                plist_name = file
                break

        if plist_name is None:
            raise FileNotFoundError('Could not find options plist!')

        plist_path = f'{path}/{plist_name}'

        working_path = f'{self.working_dir}/{plist_name}'

        self.dmg.extractFile(plist_path, working_path)

        plist_data = readPlistFile(working_path)

        info = {
            'options': {
                'path': {
                    'working': working_path,
                    'dmg': plist_path
                },
                'data': {
                    'old': plist_data,
                    'new': plist_data.copy()  # Copy data for patching
                }
            }
        }

        oldData = info['options']['data']['old']
        newData = info['options']['data']['new']

        newData['UpdateBaseband'] = False

        writePlistFile(newData, working_path)

        # Convert dict -> bytes for .patch file making

        oldData = serializePlist(oldData)
        newData = serializePlist(newData)

        info['options']['data']['old'] = oldData
        info['options']['data']['new'] = newData

        if jailbreak:
            pass

        return info

    def patchFStab(self):
        pass

    def applyRamdiskPatch(self, name, jailbreak=False):
        # hdutil refuses to work on files with
        # ".dmg" in them, we need to remove that.

        newPath = f'{self.working_dir}/ramdisk'

        copyFileToPath(self.in_path, newPath)

        self.dmg = DMG(newPath)

        ramdisk_size = getFileSize(newPath)

        grow_size = ramdisk_size + 6_000_000

        self.dmg.grow(grow_size)

        info = {}

        if self.version_prefix >= 6:
            rde_info = self.patchRestoredExternal()

            rde_paths = rde_info['restored_external']['path']

            working_rde = rde_paths['working']
            rde_path = rde_paths['dmg']

            self.dmg.rm(rde_path)
            self.dmg.addPath(working_rde, rde_path)
            self.dmg.chmod(100755, rde_path)

            info.update(rde_info)

        asr_info = self.patchASR()

        asr_paths = asr_info['asr']['path']

        working_asr = asr_paths['working']
        asr_path = asr_paths['dmg']

        # Sign asr

        ldid_args = (
            'bin/ldid',
            '-S',
            working_asr
        )

        self.runCommand(ldid_args)

        self.dmg.rm(asr_path)
        self.dmg.addPath(working_asr, asr_path)
        self.dmg.chmod(100755, asr_path)

        info.update(asr_info)

        options_info = self.patchOptions()

        options_paths = options_info['options']['path']

        working_options = options_paths['working']
        options_path = options_paths['dmg']

        self.dmg.rm(options_path)
        self.dmg.addPath(working_options, options_path)

        info.update(options_info)

        if jailbreak:
            pass

        # Rename ramdisk back

        copyFileToPath(newPath, self.out_path)

        return (self.out_path, info)

    def applyImageToImg3(self, name):
        pass


'''def patchAppleLogo(files, applelogo):
    info = files['AppleLogo']

    orig = str(info['orig'])
    patched = f'{orig}.packed'

    cmd = (
        'inject',
        applelogo,
        patched,
        orig,
        info['iv'],
        info['key']
    )

    runImagetool(cmd)

    info['packed'] = Path(patched)

    return files


def patchRecovery(files, recovery):
    info = files['RecoveryMode']

    orig = str(info['orig'])
    patched = f'{orig}.packed'

    cmd = (
        'inject',
        recovery,
        patched,
        orig,
        info['iv'],
        info['key']
    )

    runImagetool(cmd)

    info['packed'] = Path(patched)

    return files'''


'''def patchFStab(path):
    data = readTextFile(path)
    data[0] = data[0].replace('ro', 'rw')
    data[1] = data[1].replace(',nosuid,nodev', '')

    writeTextFile(path, data)'''
