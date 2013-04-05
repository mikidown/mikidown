def preProcess(inText):
    script = '\n<script type="text/javascript" src="/usr/share/mikidown/js/jquery.min.js"></script><script type="text/javascript" src="/usr/share/mikidown/js/toc.js"></script>'
    outText = "[TOC]\n" + inText + script
    return outText
