import re

def preProcess(source):
    ''' Scripts to control behavior of TOC in notesView
        May be removed when TOC in sidepanel function well.
    '''
    script = '\n<script type="text/javascript" src="/usr/share/mikidown/js/jquery.min.js"></script><script type="text/javascript" src="/usr/share/mikidown/js/toc.js"></script>'
    outText = "[TOC]\n" + source + script
    return outText

def parseHeaders(source):
    ''' Quite basic header parser
        Headers are used to construct Table Of Contents

        return: [(headerText, headerPosition)]
    '''
    #RE = re.compile(r'(^|\n)(?P<level>#{1,6})(?P<header>.*?)#*(\n|$)')
    hdrs = []
    RE = re.compile(r'^#.*', re.MULTILINE)
    for m in RE.finditer(source):
        #print(m.start())
        #print(m.string[m.start():m.end()])
        pos = m.start()
        hdr = m.string[m.start():m.end()]
        hdrs.append((hdr, pos))
    #print(hdrs)
    return hdrs
