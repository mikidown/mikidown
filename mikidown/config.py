from PyQt4.QtCore import QSettings
from whoosh.fields import Schema, ID, TEXT


class Default():
    """ Several default settings """

    ''' ~/.config/mikidown/mikidown.conf
        Apply to all notebooks created by one user.
    '''
    __appname__ = 'mikidown'
    __version__ = '0.1.6'
    global_settings = QSettings('mikidown', 'mikidown')

    # Default enabled python-markdown extensions.
    # http://pythonhosted.org/Markdown/extensions/index.html
    extensionList = ['nl2br'           # newline to break
                     , 'strkundr'        # bold-italics-underline-delete style
                     , 'codehilite'      # code syntax highlight
                     , 'fenced_code'     # code block
                     , 'headerid'        # add id to headers
                     , 'headerlink'      # add anchor to headers
                     , 'footnotes'
                     ]
    # Index directory of whoosh, located in notebookPath.
    schema = Schema(path = ID(stored=True, unique=True, spelling=True), 
                    #title = KEYWORD(stored=True, scorable=True,spelling=True, sortable=True),
                    content = TEXT)
    indexdir = ".indexdir"


def readListFromSettings(settings, key):
    if not settings.contains(key):
        return []
    value = settings.value(key)
    if isinstance(value, str):
        return [value]
    else:
        return value


def writeListToSettings(settings, key, value):
    if len(value) >= 1:
        settings.setValue(key, value)
    else:
        settings.remove(key)
