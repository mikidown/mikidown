import re
from markdown.extensions.headerid import slugify, unique


def parseHeaders(source):
    """ Parse headers to construct Table Of Contents
        return: [(level, text, position, anchor)]
        position/anchor is the header position in notesEdit/notesView
    """

    hdrs = []
    headers = []
    used_ids = set()           # In case there are headers with the same name.

    # hash headers
    RE = re.compile(r'^(#+)(.+)', re.MULTILINE)
    for m in RE.finditer(source):
        level = len(m.group(1))
        hdr = m.group(2)
        pos = m.start()
        hdrs.append((pos, level, hdr))
    
    # setext headers
    RE = re.compile(r'(.+)\n([=-]+[ ]*)(\n|$)', re.MULTILINE)
    for m in RE.finditer(source):
        if m.group(2).startswith('='):
            level = 1
        else:
            level = 2
        hdr = m.group(1)
        pos = m.start()
        hdrs.append((pos, level, hdr))

    hdrs.sort()
    for (p, l, h) in hdrs:
        anchor = unique(slugify(h, '-'), used_ids)
        headers.append((l, h, p, anchor))
    return headers

def parseTitle(source, fallback):
    """ Quite basic title parser, the first header1 is taken as title """
    title_re = re.compile(r'^#([^#].+)')
    title = title_re.search(source)
    if title:
        return title.group(1).strip()
    else:
        return fallback
