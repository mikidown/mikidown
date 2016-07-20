import os
import re

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets

#from PyQt4.QtCore import QDir, QFile, QSettings, Qt
#from PyQt4.QtGui  import QStandardItem, QStandardItemModel, QFileSystemModel
from whoosh import fields
import markdown

from .utils import TitleType, TTPL_COL_DATA, TTPL_COL_EXTRA_DATA

NOT_EXT = re.compile(r"Failed to initiate extension '([^']+)': 'module' object has no attribute 'makeExtension'")

__appname__ = 'mikidown'
__version__ = '0.3.11' # we should really change this to a tuple

class Setting():
    def __init__(self, notebooks):
        # Index directory of whoosh, located in notebookPath.
        self.schema = fields.Schema(
            path = fields.TEXT(stored=True),
            title = fields.TEXT(stored=True),
            content = fields.TEXT(stored=True),
            tags = fields.KEYWORD(commas=True))

        self.notebookName = notebooks[0][0]
        self.notebookPath = notebooks[0][1]
        self.templatesPath = os.path.join(self.notebookPath, "templates").replace(os.sep, '/')
        self.notePath = os.path.join(self.notebookPath, "notes").replace(os.sep, '/')
        self.htmlPath = os.path.join(self.notebookPath, "html", "notes").replace(os.sep, '/')
        self.indexdir = os.path.join(self.notePath, ".indexdir").replace(os.sep, '/')
        self.attachmentPath = os.path.join(self.notebookPath, "attachments").replace(os.sep, '/')
        self.configfile = os.path.join(self.notebookPath, "notebook.conf").replace(os.sep, '/')
        self.templatesConfigfile = os.path.join(self.templatesPath,
            "template_settings.conf").replace(os.sep, '/')
        cssPath = os.path.join(self.notebookPath, "css").replace(os.sep, '/')
        self.cssfile = os.path.join(cssPath, "notebook.css").replace(os.sep, '/')
        self.searchcssfile = os.path.join(cssPath, "search-window.css").replace(os.sep, '/')
        self.qsettings = QtCore.QSettings(self.configfile, QtCore.QSettings.IniFormat)
        self.tplqsettings = QtCore.QSettings(self.templatesConfigfile, QtCore.QSettings.IniFormat)

        if os.path.exists(self.configfile):
            self.extensions = readListFromSettings(self.qsettings,
                                                   "extensions")
            self.fileExt = self.qsettings.value("fileExt")
            self.attachmentImage = self.qsettings.value("attachmentImage")
            self.attachmentDocument = self.qsettings.value("attachmentDocument")
            self.version = self.qsettings.value("version")
            self.geometry = self.qsettings.value("geometry")
            self.windowstate = self.qsettings.value("windowstate")
            self.mathjax = self.qsettings.value('mathJax')
            if 'extensionsConfig' not in set(self.qsettings.childGroups()):
                self.extcfg = self.qsettings.value('extensionsConfig',  defaultValue={})
                writeDictToSettings(self.qsettings, 'extensionsConfig', self.extcfg)
            else:
                self.extcfg = readDictFromSettings(self.qsettings, 'extensionsConfig')
        else:
            self.extensions = []
            self.fileExt = ""
            self.attachmentImage = []
            self.attachmentDocument = []
            self.version = None
            self.geometry = None
            self.windowstate = None
            self.mathjax = ''
            self.extcfg = {}

        if os.path.exists(self.templatesPath):
            self.titleTemplates = readNestedListFromSettings(self.tplqsettings, 'titleTemplates',
                {
                    'friendlyName':Qt.DisplayRole,
                    'content':TTPL_COL_DATA,
                    'type':TTPL_COL_EXTRA_DATA,
                    'id':TTPL_COL_EXTRA_DATA+1,
                },
                transforms={
                    'type': lambda x: TitleType(int(x)),
                })
            self.bodyTitlePairs = readNestedListFromSettings(self.tplqsettings, 'bodyTitlePairs',
                {
                    'friendlyName':Qt.DisplayRole,
                    'bodyTpl':TTPL_COL_DATA,
                    'titleID':TTPL_COL_EXTRA_DATA,
                })
        else:
            os.makedirs(self.templatesPath)
            self.titleTemplates = QtGui.QStandardItemModel()
            self.bodyTitlePairs = QtGui.QStandardItemModel()
        self.bodyTemplates = QtWidgets.QFileSystemModel()
        self.bodyTemplates.setRootPath(self.templatesPath)
        self.bodyTemplates.rowCount()
        self.bodyTemplates.setFilter(QtCore.QDir.Files)
        self.bodyTemplates.setNameFilters(['*{}'.format(self.fileExt)])
        self.bodyTemplates.setNameFilterDisables(False)

        self.faulty_exts=[]

        # Default enabled python-markdown extensions.
        # http://pythonhosted.org/Markdown/extensions/index.html
        if not self.extensions:
            self.extensions = [
                   'nl2br',          # newline to break
                   'strkundr',       # bold-italics-underline-delete style
                   'codehilite',     # code syntax highlight
                   'fenced_code',    # code block
                   'headerid',       # add id to headers
                   'headerlink',     # add anchor to headers
                   'footnotes',
                   'asciimathml',
                 ]
            writeListToSettings(self.qsettings, "extensions", self.extensions)

        while True:
             print(self.extensions)
             try:
                 markdown.markdown("",extensions=self.extensions)
             except AttributeError as e:
                 remove_this = NOT_EXT.findall(e.args[0])[0]
                 if remove_this in self.extensions:
                     print("Found invalid markdown extension",remove_this,". Please consider removing it.")
                     print('If you want to permanently disable this, just hit OK in the Notebook Settings dialog')
                     self.extensions.remove(remove_this)
                     self.faulty_exts.append(remove_this)
             except ImportError as e:
                 if e.name.startswith('mdx_') and e.name[4:] in self.extensions:
                     print('Found missing markdown extension', e.name[4:], ', temporarily disabling.')
                     print('If you want to permanently disable this, just hit OK in the Notebook Settings dialog')
                     self.extensions.remove(e.name[4:])
                     self.faulty_exts.append(e.name[4:])
                 elif e.name in self.extensions:
                     print('Found missing markdown extension', e.name, ', temporarily disabling.')
                     print('If you want to permanently disable this, just hit OK in the Notebook Settings dialog')
                     self.extensions.remove(e.name)
                     self.faulty_exts.append(e.name)
             else:
                 self.md = markdown.Markdown(self.extensions, extension_configs=self.extcfg)
                 break

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
            notebookDir = QtCore.QDir(self.notebookPath)

            # move all markdown files to notes/
            dirList = notebookDir.entryList(QtCore.QDir.Dirs | QtCore.QDir.NoDotAndDotDot)
            if 'css' in dirList:
                dirList.remove('css')
            fileList = notebookDir.entryList(['*.md', '*.mkd', '*.markdown'])
            notebookDir.mkdir('notes')
            for d in dirList + fileList:
                notebookDir.rename(d, os.path.join('notes', d).replace(os.sep, '/'))

            # remove .indexdir folder
            oldIndexDir = QtCore.QDir(os.path.join(self.notebookPath, '.indexdir'.replace(os.sep, '/')))
            indexFileList = oldIndexDir.entryList()
            for f in indexFileList:
                oldIndexDir.remove(f)
            notebookDir.rmdir('.indexdir')

            # rename notes.css to css/notebook.css
            oldCssFile = os.path.join(self.notebookPath, 'notes.css').replace(os.sep, '/')
            QtCore.QDir().mkpath(cssPath)
            if os.path.exists(oldCssFile):
                QtCore.QFile.rename(oldCssFile, self.cssfile)

            self.version = '0'

        if not self.mathjax:
            self.mathjax = 'http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML'
            self.qsettings.setValue('mathJax', self.mathjax)

    def saveGeometry(self, geometry):
        self.qsettings.setValue("geometry", geometry)

    def saveWindowState(self, state):
        self.qsettings.setValue("windowstate", state)

    def recentViewedNotes(self):
        return readListFromSettings(self.qsettings, "recentViewedNoteList")

    def updateRecentViewedNotes(self, notesList):
        writeListToSettings(self.qsettings, "recentViewedNoteList", notesList)

    def updateTitleTemplates(self):
        writeNestedListToSettings(self.tplqsettings, 'titleTemplates',
            self.titleTemplates,
                {
                    Qt.DisplayRole:'friendlyName',
                    TTPL_COL_DATA:'content',
                    TTPL_COL_EXTRA_DATA:'type',
                    TTPL_COL_EXTRA_DATA + 1:'id',
                },
                transforms={
                    TTPL_COL_EXTRA_DATA: lambda x: x.value,
                })

    def updateBodyTitlePairs(self):
        writeNestedListToSettings(self.tplqsettings, 'bodyTitlePairs',
            self.bodyTitlePairs,
                {
                    Qt.DisplayRole:'friendlyName',
                    TTPL_COL_DATA:'bodyTpl',
                    TTPL_COL_EXTRA_DATA:'titleID',
                })

def readListFromSettings(settings, key):
    if not settings.contains(key):
        return []
    value = settings.value(key)
    if isinstance(value, str):
        return [value]
    else:
        return value

def writeListToSettings(settings, key, value):
    if value:
        settings.setValue(key, value)
    else:
        settings.remove(key)

def readNestedListFromSettings(settings, key, props, transforms=None):
    """
    Reads a nested list from settings
    
    :param settings QSettings: Settings object to read from
    :param key str: The section the array resides in
    :param props dict: A dict containing mappings from array item
        property names to Qt Item roles.
    :param transforms dict: A dict containing mappings from property names
        to callables that transform it into the right type.
    :return: QStandardItemModel with QStandardItems in the specified roles

    .. tip::
        Example props parameter.

        .. code-block:: python

            {
                'testProp' :Qt.DisplayRole,
                'testProp2':Qt.UserRole,
                'testProp3':Qt.UserRole+1,
            }
    """

    if transforms is None:
        transforms = {}

    size = settings.beginReadArray(key)
    model = QtGui.QStandardItemModel()
    for i in range(size):
        settings.setArrayIndex(i)
        item = QtGui.QStandardItem()
        for prop in props:
            value = settings.value(prop, '')
            if prop in transforms:
                value = transforms[prop](value)
            item.setData(value, props[prop])
        model.appendRow(item)
    settings.endArray()
    return model

def writeNestedListToSettings(settings, key, values, props, transforms=None):
    """
    Writes a nested list to settings
    
    :param settings QSettings: Settings object to write from
    :param key str: The section the array will reside in
    :param values QStandardItemModel: The array to write
    :param props dict: A dict containing mappings from Qt Item roles
        to array property names.
    :param transforms dict: A dict containing mappings from Qt Item roles
        to callables that transform it into the right type.

    .. tip::
        Example props parameter.

        .. code-block:: python

            {
                Qt.DisplayRole:'testProp',
                Qt.UserRole   :'testProp2',
                Qt.UserRole+1 :'testProp3',
            }
    """

    if transforms is None:
        transforms = {}

    settings.beginWriteArray(key)
    size = values.rowCount()
    for i in range(size):
        settings.setArrayIndex(i)
        val = values.item(i)
        for prop in props:
            value = val.data(prop)
            if prop in transforms:
                value = transforms[prop](value)
            settings.setValue(props[prop], value)
    settings.endArray()

def readDictFromSettings(settings, key):
    data={}
    settings.beginGroup(key)
    for k in settings.childGroups():
        settings.beginGroup(k)
        key_data = []
        for k2 in settings.childKeys():
            key_data.append((k2, settings.value(k2)))
        settings.endGroup()
        data[k]=key_data
    settings.endGroup()
    return data

def writeDictToSettings(settings, key, value):
    settings.beginGroup(key)
    for k in value.keys():
        settings.beginGroup(k)
        for v in value[k]:
            settings.setValue(v[0], v[1])
        settings.endGroup()
    settings.endGroup()
