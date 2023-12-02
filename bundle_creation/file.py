
import shutil
from pathlib import Path

from .utils import getSHA1


def writeBinaryFile(data, path):
    with open(path, 'wb') as f:
        f.write(data)


def getFileSize(path):
    return Path(path).stat().st_size


def readBinaryFile(path):
    with open(path, 'rb') as f:
        return bytearray(f.read())


def getFileHash(path):
    data = readBinaryFile(path)
    hash = getSHA1(data)
    return hash


def removeFile(path):
    try:
        Path(path).unlink()
    except FileNotFoundError:
        pass


def copyFileToPath(in_path, out_path):
    shutil.copy(in_path, out_path)


def moveFileToPath(in_path, out_path):
    shutil.move(in_path, out_path)


def readTextFile(path):
    with open(path) as f:
        return f.readlines()


def writeTextFile(path, data):
    with open(path, 'w') as f:
        f.writelines(data)
