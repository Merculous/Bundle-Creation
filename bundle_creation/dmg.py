
from pathlib import Path

from .command import Command


class DMG(Command):
    def __init__(self, dmg, key=None) -> None:
        super().__init__()

        self.dmg = dmg
        self.key = key

    def decryptFS(self, dst):
        if self.key is None:
            raise Exception('Please set key!')

        cmd_args = (
            'bin/dmg',
            'extract',
            self.dmg,
            dst,
            '-k',
            self.key
        )

        cmd = self.runCommand(cmd_args)

        if cmd[1] != 0:
            raise Exception('dmg decryption seems to have failed!')

        return cmd

    def getRootName(self):
        cmd_args = (
            'bin/7z',
            'l',
            self.dmg
        )

        cmd = self.runCommand(cmd_args)

        cmd_stdout = cmd[2].splitlines()

        for line in cmd_stdout:
            line = line.split()

            if line and '/Applications' in line[-1]:
                path = str(Path(line[-1]).parent)
                return path

    def buildFS(self, dst):
        cmd_args = (
            'bin/dmg',
            'build',
            self.dmg,
            dst
        )

        cmd = self.runCommand(cmd_args)

        if cmd[1] != 0:
            raise Exception('dmg failed to build fs!')

        return cmd

    def extractFile(self, src, dst):
        cmd_args = (
            'bin/hdutil',
            self.dmg,
            'extract',
            src,
            dst
        )

        cmd = self.runCommand(cmd_args)

        return cmd

    def grow(self, size):
        cmd_args = (
            'bin/hdutil',
            self.dmg,
            'grow',
            str(size)
        )

        cmd = self.runCommand(cmd_args)

        return cmd

    def ls(self, path):
        cmd_args = (
            'bin/hdutil',
            self.dmg,
            'ls',
            path
        )

        cmd = self.runCommand(cmd_args)

        return cmd

    def rm(self, path):
        cmd_args = (
            'bin/hdutil',
            self.dmg,
            'rm',
            path
        )

        cmd = self.runCommand(cmd_args)

        return cmd

    def addPath(self, src, dst):
        cmd_args = (
            'bin/hdutil',
            self.dmg,
            'add',
            src,
            dst
        )

        cmd = self.runCommand(cmd_args)

        return cmd

    def chmod(self, mode, path):
        cmd_args = (
            'bin/hdutil',
            self.dmg,
            'chmod',
            str(mode),
            path
        )

        cmd = self.runCommand(cmd_args)

        return cmd
