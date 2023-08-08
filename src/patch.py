
import bsdiff4

from .command import runFuzzyPatcher


def patchFileWithBSDiff(orig, new, patch_path):
    bsdiff4.file_patch(orig, new, patch_path)


def patchFileWithFuzzyPatcher(orig, new, patch_path):
    # Fuzzy patcher allows deterministic patching.
    # I may add support to make use of it, but for now,
    # I'm going to skip over it.

    cmd = (
        '--patch',
        '--delta',
        patch_path,
        '--orig',
        orig,
        '--patched',
        new
    )
    runFuzzyPatcher(cmd)
