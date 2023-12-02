
from pathlib import Path

from .utils import listDir


class Bundle:
    bundle_parent = 'FirmwareBundles'

    def __init__(self, device, board, version, buildid) -> None:
        self.device = device
        self.board = board
        self.version = version
        self.buildid = buildid

        self.name = self.formBundlePath()

    def findBundle(self):
        # We can first check the "FirmwareBundles" even exists!

        bundle_contents = self.getBundleContents()

        if len(bundle_contents) == 0:
            return None

        if self.name not in bundle_contents:
            return False

        return True

    def formBundlePath(self):
        name = f'{self.device}_{self.board}_{self.version}_{self.buildid}'
        return Path(f'{self.bundle_parent}/{name}.bundle')

    def getBundleContents(self):
        return listDir('*', self.bundle_parent, True)

    def getPatch(self, pattern):
        for path in self.getBundleContents():
            if pattern in path.name:
                return path
