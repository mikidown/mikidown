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
    '''
    #RE = re.compile(r'(^|\n)(?P<level>#{1,6})(?P<header>.*?)#*(\n|$)')
    RE = re.compile(r'^#.*', re.MULTILINE)
    m = RE.findall(source)
    return m
