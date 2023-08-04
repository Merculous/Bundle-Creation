
import bsdiff4


def createBSDiffPatchFile(orig, new, patch_path):
    bsdiff4.file_diff(orig, new, patch_path)
