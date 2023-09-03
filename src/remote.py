
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .file import writeBinaryFile
from .json import readJSONStr


def readFromURL(url, mode, use_json):
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        r = urlopen(req)
    except HTTPError as e:
        print(f'Got error from url: {url}')
        print(f'Status: {e.code}')
        print(f'Reason: {e.reason}')
    else:
        data = r.read()

        if mode == 's':
            data = data.decode('utf-8')

            if use_json:
                return readJSONStr(data)
            else:
                return data

        elif mode == 'b':
            return data

        else:
            raise Exception(f'Got mode: {mode}')


def downloadFile(url, path):
    data = readFromURL(url, 'b', False)
    writeBinaryFile(data, path)


def readJSONFromURL(url):
    data = readFromURL(url, 's', True)
    return data
