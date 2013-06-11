import re
from markdown.extensions.headerid import slugify, unique


def parseHeaders(source):
    ''' Quite basic header parser
        Headers are used to construct Table Of Contents

        return: [(hdrLevel, hdrText, hdrPosition, hdrAnchor)]
    '''
    # RE = re.compile(r'(^|\n)(?P<level>#{1,6})(?P<header>.*?)#*(\n|$)')
    hdrs = []
    used_ids = set()           # In case there are headers with the same name.
    RE = re.compile(r'^(#+)(.+)', re.MULTILINE)
    for m in RE.finditer(source):
        hdrLevel = m.group(1)
        hdr = m.group(2)
        pos = m.start()
        anchor = unique(slugify(hdr, '-'), used_ids)
        hdrs.append((hdrLevel, hdr, pos, anchor))
    return hdrs

def parseTitle(source, fallback):
    """ Quite basic title parser, the first header1 is taken as title """
    title_re = re.compile(r'^#([^#].+)')
    title = title_re.search(source)
    if title:
        return title.group(1).strip()
    else:
        return fallback
