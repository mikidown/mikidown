import re
from markdown.extensions.headerid import slugify, unique

def parseHeaders(source):
    ''' Quite basic header parser
        Headers are used to construct Table Of Contents

        return: [(hdrLevel, hdrText, hdrPosition, hdrAnchor)]
    '''
    #RE = re.compile(r'(^|\n)(?P<level>#{1,6})(?P<header>.*?)#*(\n|$)')
    hdrs = []
    used_ids = []           # In case there are headers with the same name.
    RE = re.compile(r'^(#+)(.+)', re.MULTILINE)
    for m in RE.finditer(source):
        hdrLevel = m.group(1)
        hdr = m.group(2)
        #hdr = m.string[m.start():m.end()]
        pos = m.start()
        anchor = unique(slugify(hdr, '-'), used_ids)
        hdrs.append((hdrLevel, hdr, pos, anchor))
    #print(hdrs)
    return hdrs

