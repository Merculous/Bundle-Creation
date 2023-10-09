
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

    return info


def getKeys(codename, buildid, device):
    wiki_url = 'https://theapplewiki.com/index.php'
    url = f'{wiki_url}?title=Keys:{codename}_{buildid}_({device})&action=raw'

    template = readFromURL(url, 's', False)
    key_data = parseKeyTemplate(template)

    data = key_data['data']

    needed_keys = {
        'Restore Ramdisk': [
            data['RestoreRamdisk'],
            data.get('RestoreRamdiskIV', ''),  # Can be unencrypted
            data.get('RestoreRamdiskKey', '')
        ],
        'iBSS': [
            data['iBSS'],
            data['iBSSIV'],
            data['iBSSKey']
        ],
        'iBEC': [
            data['iBEC'],
            data['iBECIV'],
            data['iBECKey']
        ],
        'LLB': [
            data['LLB'],
            data['LLBIV'],
            data['LLBKey']
        ],
        'iBoot': [
            data['iBoot'],
            data['iBootIV'],
            data['iBootKey']
        ],
        'RootFS': [
            data['RootFS'],
            data['RootFSKey']
        ],
        'KernelCache': [
            data['Kernelcache'],
            data['KernelcacheIV'],
            data['KernelcacheKey']
        ]
    }

    return needed_keys
