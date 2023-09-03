
from zipfile import ZipFile

from .utils import cd, listDir


class Archive(ZipFile):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _extractPath(self, src, dst):
        self.extract(src, dst)

    def _extractAll(self, dst):
        self.extractall(dst)

    def _listPaths(self):
        return self.infolist()

    def _addPaths(self, src):
        cd(src)

        contents = listDir('*', recursive=True)

        for path in contents:
            self.write(path)

    def _readPath(self, src):
        return self.read(src)
