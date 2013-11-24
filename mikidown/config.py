import os

from PyQt4.QtCore import QDir, QFile, QSettings
from whoosh import fields


__appname__ = 'mikidown'
__version__ = '0.3.1'

class Setting():

    def __init__(self, notebooks):

        # Index directory of whoosh, located in notebookPath.
        self.schema = fields.Schema(
            path = fields.TEXT(stored=True),
            title = fields.TEXT(stored=True),
            content = fields.TEXT(stored=True))

        self.notebookName = notebooks[0][0]
        self.notebookPath = notebooks[0][1]
        self.notePath = os.path.join(self.notebookPath, "notes")
        self.htmlPath = os.path.join(self.notebookPath, "html", "notes")
        self.indexdir = os.path.join(self.notePath, ".indexdir")
        self.attachmentPath = os.path.join(self.notebookPath, "attachments")
        self.configfile = os.path.join(self.notebookPath, "notebook.conf")
        cssPath = os.path.join(self.notebookPath, "css")
        self.cssfile = os.path.join(cssPath, "notebook.css")
        self.qsettings = QSettings(self.configfile, QSettings.NativeFormat)

        if os.path.exists(self.configfile):
            self.extensions = readListFromSettings(self.qsettings,
                                                   "extensions")
            self.fileExt = self.qsettings.value("fileExt")
            self.attachmentImage = self.qsettings.value("attachmentImage")
            self.attachmentDocument = self.qsettings.value("attachmentDocument")
            self.version = self.qsettings.value("version")
            self.geometry = self.qsettings.value("geometry")
            self.windowstate = self.qsettings.value("windowstate")
        else:
            self.extensions = []
            self.fileExt = ""
            self.attachmentImage = []
            self.attachmentDocument = []
            self.version = None
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

        # Image file types that will be copied to attachmentDir
        # Inserted as image link
        if not self.attachmentImage:
            self.attachmentImage = [".jpg", ".jpeg", ".png", ".gif", ".svg"]
            self.qsettings.setValue("attachmentImage", self.attachmentImage)

        # Document file types that will be copied to attachmentDir
        # Inserted as link
        if not self.attachmentDocument:
            self.attachmentDocument = [".pdf", ".doc", ".odt"]
            self.qsettings.setValue("attachmentDocument", self.attachmentDocument)

        # Migrate notebookPath to v0.3.0 folder structure
        if not self.version:
            notebookDir = QDir(self.notebookPath)

            # move all markdown files to notes/
            dirList = notebookDir.entryList(QDir.Dirs | QDir.NoDotAndDotDot)
            if 'css' in dirList:
                dirList.remove('css')
            fileList = notebookDir.entryList(['*.md', '*.mkd', '*.markdown'])
            notebookDir.mkdir('notes')
            for d in dirList + fileList:
                notebookDir.rename(d, os.path.join('notes', d))

            # remove .indexdir folder
            oldIndexDir = QDir(os.path.join(self.notebookPath, '.indexdir'))
            indexFileList = oldIndexDir.entryList()
            for f in indexFileList:
                oldIndexDir.remove(f)
            notebookDir.rmdir('.indexdir')

            # rename notes.css to css/notebook.css
            oldCssFile = os.path.join(self.notebookPath, 'notes.css')
            QDir().mkpath(cssPath)
            if os.path.exists(oldCssFile):
                QFile.rename(oldCssFile, self.cssfile)

            self.version = '0'

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
