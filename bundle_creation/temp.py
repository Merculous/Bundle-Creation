
import tempfile
from pathlib import Path


def makeTempDir():
    return Path(tempfile.mkdtemp())
