
import shutil
from hashlib import sha1
from pathlib import Path


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
    return sha1(data).hexdigest()


def removeFile(path):
    try:
        Path(path).unlink()
    except FileNotFoundError:
        pass


def copyFileToPath(in_path, out_path):
    shutil.copy(in_path, out_path)


def moveFileToPath(in_path, out_path):
    shutil.move(in_path, out_path)
