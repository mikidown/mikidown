import os

from PyQt4.QtCore import QSettings
from whoosh import fields


__appname__ = 'mikidown'
__version__ = '0.2.4'

class Setting():

    def __init__(self, notebooks):

        # Index directory of whoosh, located in notebookPath.
        self.schema = fields.Schema(
            path = fields.TEXT(stored=True), 
            title = fields.TEXT(stored=True),
            content = fields.TEXT(stored=True))
        self.indexdir = ".indexdir"

        self.notebookName = notebooks[0][0]
        self.notebookPath = notebooks[0][1]
        self.configfile = os.path.join(self.notebookPath, "notebook.conf")
        self.qsettings = QSettings(self.configfile, QSettings.NativeFormat)

        if os.path.exists(self.configfile):
            self.extensions = readListFromSettings(self.qsettings,
                                                   "extensions")
            self.fileExt = self.qsettings.value("fileExt")
            self.geometry = self.qsettings.value("geometry")
            self.windowstate = self.qsettings.value("windowstate")
            self.autoSaveHtml = self.qsettings.value("autoSaveHtml") in ["1", "true", "yes", "True", "Yes"]
        else:
            self.autoSaveHtml = False
            self.qsettings.setValue("autoSaveHtml", False)
            self.extensions = []
            self.fileExt = ""
            self.geometry = None
            self.windowstate = None

        # Default enabled python-markdown extensions.
        # http://pythonhosted.org/Markdown/extensions/index.html
        if not self.extensions:
            self.extensions = [
                   'nl2br'           # newline to break
                 , 'strkundr'        # bold-italics-underline-delete style
                 , 'codehilite'      # code syntax highlight
                 , 'fenced_code'     # code block
                 , 'headerid'        # add id to headers
                 , 'headerlink'      # add anchor to headers
                 , 'footnotes'
                 ]
            writeListToSettings(self.qsettings, "extensions", self.extensions)

        # Default file extension name
        if not self.fileExt:
            self.fileExt = ".md"
            self.qsettings.setValue("fileExt", self.fileExt)

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
