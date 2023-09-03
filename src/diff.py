
import bsdiff4


def createBSDiffPatchFile(orig, new, patch_path):
    bsdiff4.file_diff(orig, new, patch_path)


def makePatchFiles(files, bundle):
    for file in files:
        if 'packed' in files[file]:
            orig = files[file]['orig']
            packed = files[file]['packed']

            tmp = orig.name.split('.')
            tmp[-1] = 'patch'

            patch = '.'.join(tmp)
            bundle_patch = f'{bundle}/' + patch

            createBSDiffPatchFile(orig, packed, bundle_patch)

            files[file]['patch'] = patch

    return files
