import re
from markdown.extensions.headerid import slugify, unique

def parseHeaders(source):
    ''' Quite basic header parser
        Headers are used to construct Table Of Contents

        return: [(headerText, headerPosition, headerAnchor)]
    '''
    #RE = re.compile(r'(^|\n)(?P<level>#{1,6})(?P<header>.*?)#*(\n|$)')
    hdrs = []
    used_ids = []           # In case there are headers with the same name.
    RE = re.compile(r'^#.*', re.MULTILINE)
    for m in RE.finditer(source):
        hdr = m.string[m.start():m.end()]
        pos = m.start()
        anchor = unique(slugify(hdr, '-'), used_ids)
        hdrs.append((hdr, pos, anchor))
    #print(hdrs)
    return hdrs

