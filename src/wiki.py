
from .json import writeJSON
from .keys import readKeys
from .remote import readFromURL


def parseKeyTemplate(template):
    template = template.splitlines()

    data = [x.strip() for x in template]

    info = {
        'start': data[0],
        'end': data[-1],
        'spaces': [],
        'data': {}
    }

    for i, line in enumerate(data):
        if line == '':
            info['spaces'].append(i)
        else:
            line = line[2:].split('=')
            if len(line) == 2:
                k = line[0].strip()
                v = line[1].strip()
                info['data'].update({k: v})

    writeJSON(info, 'Keys.json')


def getKeys(codename, buildid, device):
    wiki_url = 'https://www.theiphonewiki.com/w/index.php'
    url = f'{wiki_url}?title={codename}_{buildid}_({device})&action=raw'

    template = readFromURL(url, 's', False)
    parseKeyTemplate(template)

    data = readKeys()

    data = data.get('data')

    needed_keys = {
        'ramdisk': [
            data.get('RestoreRamdisk'),
            data.get('RestoreRamdiskIV'),
            data.get('RestoreRamdiskKey')
        ],
        'iBSS': [
            data.get('iBSS'),
            data.get('iBSSIV'),
            data.get('iBSSKey')
        ],
        'iBEC': [
            data.get('iBEC'),
            data.get('iBECIV'),
            data.get('iBECKey')
        ],
        'LLB': [
            data.get('LLB'),
            data.get('LLBIV'),
            data.get('LLBKey')
        ],
        'iBoot': [
            data.get('iBoot'),
            data.get('iBootIV'),
            data.get('iBootKey')
        ],
        'RootFS': [
            data.get('RootFS'),
            data.get('RootFSKey')
        ],
        'kernelcache': [
            data.get('Kernelcache'),
            data.get('KernelcacheIV'),
            data.get('KernelcacheKey')
        ]
    }

    writeJSON(needed_keys, 'Keys.json')
