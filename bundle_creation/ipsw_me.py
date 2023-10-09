
from .file import getFileHash
from .remote import downloadFile, readJSONFromURL
from .utils import selectFromList

api = 'https://api.ipsw.me/v4'
restore_types = ('ipsw', 'ota')


def getDeviceInfo(device, restore_type='ipsw'):
    if restore_type not in restore_types:
        raise Exception(f'Unknown restore type: {restore_type}')

    url = f'{api}/device/{device}?type={restore_type}'
    return readJSONFromURL(url)


def getFirmwaresForDevice(device):
    data = getDeviceInfo(device)
    return data['firmwares']


def getVersionInfo(device, version):
    firmwares = getFirmwaresForDevice(device)
    matches = [v for v in firmwares if v['version'] == version]
    return matches


def getBuildidForVersion(device, version):
    matches = getVersionInfo(device, version)

    if len(matches) == 1:
        return matches[0]['buildid']
    else:
        choices = [b['buildid'] for b in matches]
        choice = selectFromList(choices)
        return choice


def getURLForArchive(device, version, buildid):
    version_info = getVersionInfo(device, version)

    for version in version_info:
        if version['buildid'] == buildid:
            return version['url']


def getSHA1ForArchive(device, version, buildid):
    version_info = getVersionInfo(device, version)

    for version in version_info:
        if version['buildid'] == buildid:
            return version['sha1sum']


def downloadArchive(device, version, buildid):
    url = getURLForArchive(device, version, buildid)
    ipsw_name = url.split('/')[-1]
    sha1_server = getSHA1ForArchive(device, version, buildid)
    downloadFile(url, ipsw_name)
    sha1_local = getFileHash(ipsw_name)

    if sha1_server != sha1_local:
        print('SHA1 hash from ipsw.me differs from local ipsw!')
        print(f'ipsw.me SHA1: {sha1_server}')
        print(f'local SHA1: {sha1_local}')
