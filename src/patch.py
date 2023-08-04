
import bsdiff4


def patchFileWithBSDiff(orig, new, patch_path):
    bsdiff4.file_patch(orig, new, patch_path)
