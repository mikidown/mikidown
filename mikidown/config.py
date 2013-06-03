import os

from PyQt4.QtCore import QSettings
from whoosh.fields import Schema, ID, TEXT


class Setting():

    def __init__(self, notebookPath, notebookName):
        self.__appname__ = 'mikidown'
        self.__version__ = '0.1.6'

        # Index directory of whoosh, located in notebookPath.
        self.schema = Schema(
            path = ID(stored=True, unique=True, spelling=True), 
            # title = KEYWORD(stored=True, scorable=True,spelling=True, sortable=True),
            content = TEXT)
        
        self.notebookPath = notebookPath
        self.notebookName = notebookName
        self.indexdir = ".indexdir"
        self.configfile = os.path.join(notebookPath, "notebook.conf")
        
        self.qsettings = QSettings(self.configfile, QSettings.NativeFormat)
        self.geometry = self.qsettings.value("geometry")
        self.windowstate = self.qsettings.value("windowstate")

        if os.path.exists(self.configfile):
            self.extensions = readListFromSettings(self.qsettings,
                                                      "extensions")
        else:
            # Default enabled python-markdown extensions.
            # http://pythonhosted.org/Markdown/extensions/index.html
            self.extensions = [
                   'nl2br'           # newline to break
                 , 'strkundr'        # bold-italics-underline-delete style
                 , 'codehilite'      # code syntax highlight
                 , 'fenced_code'     # code block
                 , 'headerid'        # add id to headers
                 , 'headerlink'      # add anchor to headers
                 , 'footnotes'
                 ]
    def saveGeometry(self, geometry):
        self.qsettings.setValue("geometry", geometry)

    def saveWindowState(self, state):
        self.qsettings.setValue("windowstate", state)

    def recentViewedNotes(self):
        return readListFromSettings(self.qsettings, "recentViewedNoteList")

    def updateRecentViewedNotes(self, notesList):
        writeListToSettings(self.qsettings, "recentViewedNoteList", notesList)

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
