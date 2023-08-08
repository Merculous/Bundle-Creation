
import bsdiff4

from .command import runFuzzyPatcher


def createBSDiffPatchFile(orig, new, patch_path):
    bsdiff4.file_diff(orig, new, patch_path)


def createDiffWithFuzzyPatcher(orig, new, diff_path):
    cmd = (
        '--diff',
        '--delta',
        diff_path,
        '--orig',
        orig,
        '--patched',
        new
    )
    runFuzzyPatcher(cmd)
