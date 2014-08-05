"""
Notebook management module.
"""

import os
import markdown
from copy import deepcopy
from PyQt4.QtCore import Qt, QDir, QFile, QSettings, QSize
from PyQt4.QtGui import (QAbstractItemDelegate, QAbstractItemView, QColor, QDialog, QDialogButtonBox, 
                         QFileDialog, QFont, QGridLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                         QPen, QPushButton, QStyle, QVBoxLayout, QTabWidget, QWidget, QBrush, QTreeWidget,
                         QTreeWidgetItem, QSpinBox)

import mikidown
from .utils import allMDExtensions
from .config import Setting, readListFromSettings, writeListToSettings, writeDictToSettings


class ListDelegate(QAbstractItemDelegate):
    """ Customize view and behavior of notebook list """

    def __init__(self, parent=None):
        super(ListDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        r = option.rect

        if option.state & QStyle.State_Selected:
            painter.fillRect(r, self.parent().palette().highlight())
            fontPen = QPen(self.parent().palette().highlightedText(), 1, Qt.SolidLine)
        else:
            painter.fillRect(r, self.parent().palette().base())
            fontPen = QPen(self.parent().palette().text(), 1, Qt.SolidLine)

        painter.setPen(fontPen)

        name = index.data(Qt.DisplayRole)
        path = index.data(Qt.UserRole)

        imageSpace = 10
        # notebook name
        r = option.rect.adjusted(imageSpace, 0, -10, -20)
        name_font = QFont(self.parent().font())
        name_font.setPointSize(10)
        name_font.setBold(True)
        painter.setFont(name_font)
        painter.drawText(r.left(), r.top(), r.width(), r.height(), 
                         Qt.AlignBottom|Qt.AlignLeft, name)
        # notebook path
        path_font = QFont(self.parent().font())
        path_font.setPointSize(8)
        r = option.rect.adjusted(imageSpace, 20, -10, 0)
        painter.setFont(path_font)
        painter.drawText(r.left(), r.top(), r.width(), r.height(), 
                         Qt.AlignLeft, path)

    def sizeHint(self, option, index):
        return QSize(200, 40)

class NotebookExtSettingsDialog(QDialog):
    def __init__(self, parent=None, cfg_list=[]):
        super(NotebookExtSettingsDialog, self).__init__(parent)
        self.extCfgEdit = QTreeWidget()
        self.extCfgEdit.setHeaderLabels(['Property', 'Value'])
        self.addRow = QPushButton('+')
        self.removeRow = QPushButton('-')
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok |
                                          QDialogButtonBox.Cancel)

        layout = QGridLayout(self)
        layout.addWidget(self.extCfgEdit,0,0,1,2)
        layout.addWidget(self.addRow,1,0,1,1)
        layout.addWidget(self.removeRow,1,1,1,1)
        layout.addWidget(self.buttonBox,2,0,1,2)
        self.initCfgPanel(cfg_list)

        self.addRow.clicked.connect(self.actionAdd)
        self.removeRow.clicked.connect(self.actionRemove)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def initCfgPanel(self, cfg_list):
        for item in cfg_list:
            self.actionAdd(prop_name=item[0], prop_val=item[1])

    def actionRemove(self):
        item = self.extCfgEdit.currentItem()
        row = self.extCfgEdit.indexOfTopLevelItem(item)
        self.extCfgEdit.takeTopLevelItem(row)

    def actionAdd(self, checked=False, prop_name='', prop_val=''):
        item = QTreeWidgetItem(self.extCfgEdit, [prop_name, prop_val])
        item.setFlags(item.flags()|Qt.ItemIsEditable)
        #self.extCfgEdit.addTopLevelItem(item)

    def configToList(self):
        items = []
        for i in range(self.extCfgEdit.topLevelItemCount()):
            witem = self.extCfgEdit.topLevelItem(i)
            items.append((witem.text(0), witem.text(1)))
        return items

class NotebookSettingsDialog(QDialog):
    """GUI for adjusting notebook settings"""
    def __init__(self, parent=None):
        super(NotebookSettingsDialog, self).__init__(parent)
        #widgets for tab 1
        self.mdExts = QListWidget()
        self.mjEdit = QLineEdit()
        self.moveUp = QPushButton('<<')
        self.moveDown = QPushButton('>>')
        self.configureExtension = QPushButton('Edit Settings for this extension')
        self.tmpdict = deepcopy(self.parent().settings.extcfg)
        
        #widgets for tab 2
        self.fExtEdit = QLineEdit()
        self.attImgEdit = QLineEdit()
        self.attDocEdit = QLineEdit()
        # mandatory button box
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok |
                                          QDialogButtonBox.Cancel)
        
        #tab panels
        tabs = QTabWidget()
        markupTab = QWidget()
        fileExtsTab = QWidget()
        tabs.addTab(markupTab, "Markdown")
        tabs.addTab(fileExtsTab, "File extensions")
        
        #initialization functions
        self.initExtList()
        self.mdExts.setDragDropMode(QAbstractItemView.InternalMove)
        self.mjEdit.setText(self.parent().settings.mathjax)
        self.attImgEdit.setText(', '.join(self.parent().settings.attachmentImage))
        self.attDocEdit.setText(', '.join(self.parent().settings.attachmentDocument))
        self.fExtEdit.setText(self.parent().settings.fileExt)
        
        #set up tab 1
        layout=QGridLayout(markupTab)
        layout.addWidget(QLabel("Markdown extensions"),0,0,1,4)
        layout.addWidget(self.mdExts,1,0,1,4)
        layout.addWidget(self.moveUp,2,0,1,1)
        layout.addWidget(self.moveDown,2,1,1,1)
        layout.addWidget(self.configureExtension,2,2,1,2)
        layout.addWidget(QLabel("MathJax Location"),3,0,1,1)
        layout.addWidget(self.mjEdit,3,1,1,3)
        
        #set up tab 2
        layout=QGridLayout(fileExtsTab)
        layout.addWidget(QLabel("Note file extension"),0,0,1,1)
        layout.addWidget(QLabel("Image file extension"),1,0,1,1)
        layout.addWidget(QLabel("Document file extension"),2,0,1,1)
        layout.addWidget(self.fExtEdit,0,1,1,1)
        layout.addWidget(self.attImgEdit,1,1,1,1)
        layout.addWidget(self.attDocEdit,2,1,1,1)
        
        #put it together
        vlayout = QVBoxLayout(self)
        vlayout.addWidget(tabs)
        vlayout.addWidget(self.buttonBox)

        #setup signal handlers
        self.moveUp.clicked.connect(self.moveItemUp)
        self.configureExtension.clicked.connect(self.configExt)
        self.moveDown.clicked.connect(self.moveItemDown)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def configExt(self, checked=False, ext=None):
        if ext is None:
            ext = self.mdExts.currentItem().text()
        cfg = self.tmpdict.get(ext,[])
        dialog = NotebookExtSettingsDialog(cfg_list=cfg)
        done = dialog.exec()
        if done:
            self.tmpdict[ext] = dialog.configToList()

    def initExtList(self):
        extset=set(self.parent().settings.extensions)
        #for easier performance in checking
        for ext in self.parent().settings.extensions:
            item = QListWidgetItem(ext, self.mdExts)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)

        for ext in self.parent().settings.faulty_exts:
            item = QListWidgetItem(ext, self.mdExts)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setBackground(QBrush(QColor('red')))
            item.setForeground(QBrush(QColor('black')))
            item.setCheckState(Qt.Checked)

        for ext in allMDExtensions():
            if ext in extset: continue
            item = QListWidgetItem(ext, self.mdExts)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            #self.mdExts.addItem(item)

    def moveItemUp(self):
        item = self.mdExts.currentItem()
        row = self.mdExts.currentRow()
        if row != 0:
            # self.mdExts.removeItemWidget(item)
            self.mdExts.takeItem(row)
            self.mdExts.insertItem(row-1, item)
            self.mdExts.setCurrentRow(row-1)

    def moveItemDown(self):
        item = self.mdExts.currentItem()
        row = self.mdExts.currentRow()
        count = self.mdExts.count()
        if row != count-1:
            self.mdExts.takeItem(row)
            self.mdExts.insertItem(row+1, item)
            self.mdExts.setCurrentRow(row+1)


    def accept(self):
        #write to settings first
        msettings = self.parent().settings
        nbsettings = msettings.qsettings
        
        nbsettings.setValue('mathJax', self.mjEdit.text())
        extlist = []
        for i in range(self.mdExts.count()):
            item = self.mdExts.item(i)
            if item.checkState() == Qt.Checked:
                extlist.append(item.text())
        writeListToSettings(nbsettings, 'extensions', extlist)
        writeListToSettings(nbsettings, 'attachmentImage', self.attImgEdit.text().split(", "))
        writeListToSettings(nbsettings, 'attachmentDocument', self.attDocEdit.text().split(", "))
        writeDictToSettings(nbsettings, 'extensionsConfig', self.tmpdict)
        
        #then to memory
        msettings.extensions = extlist
        msettings.mathjax = self.mjEdit.text()
        msettings.attachmentDocument = readListFromSettings(nbsettings, 'attachmentDocument')
        msettings.attachmentImage = readListFromSettings(nbsettings, 'attachmentImage')
        msettings.extcfg.update(self.tmpdict)
        msettings.md = markdown.Markdown(msettings.extensions, extension_configs=msettings.extcfg)
        
        #then make mikidown use these settings NOW
        curitem=self.parent().notesTree.currentItem()
        self.parent().currentItemChangedWrapper(curitem, curitem)
        QDialog.accept(self)

class NotebookListDialog(QDialog):
    """ Functions to display, create, remove, modify notebookList """

    def __init__(self, parent=None):
        super(NotebookListDialog, self).__init__(parent)

        self.notebookList = QListWidget()
        self.moveUp = QPushButton('<<')
        self.moveDown = QPushButton('>>')
        self.add = QPushButton('Add')
        self.remove = QPushButton('Remove')
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok |
                                          QDialogButtonBox.Cancel)
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        layout = QGridLayout()
        layout.addWidget(self.notebookList, 0, 0, 4, 6)
        layout.addWidget(self.moveUp, 1, 6)
        layout.addWidget(self.moveDown, 2, 6)
        layout.addWidget(self.add, 4, 0)
        layout.addWidget(self.remove, 4, 1)
        layout.addWidget(self.buttonBox, 4, 5, 1, 2)
        self.setLayout(layout)

        self.notebookList.setItemDelegate(ListDelegate(self.notebookList))

        self.notebookList.currentRowChanged.connect(self.updateUi)
        self.add.clicked.connect(self.actionAdd)
        self.remove.clicked.connect(self.actionRemove)
        self.moveUp.clicked.connect(self.moveItemUp)
        self.moveDown.clicked.connect(self.moveItemDown)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.initList()

    def initList(self):
        self.notebookList.clear()
        notebooks = Mikibook.read()
        for nb in notebooks:
            item = QListWidgetItem()
            item.setData(Qt.DisplayRole, nb[0])
            item.setData(Qt.UserRole, nb[1])
            self.notebookList.addItem(item)

        self.updateUi(len(notebooks) != 0)
        self.notebookList.setCurrentRow(0)
            # QListWidgetItem(nb, self.notebookList)

    def updateUi(self, row):
        flag = (row != -1)
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(flag)
        self.remove.setEnabled(flag)
        self.moveUp.setEnabled(flag)
        self.moveDown.setEnabled(flag)

    def actionAdd(self):
        Mikibook.create()
        self.initList()
        count = self.notebookList.count()
        self.notebookList.setCurrentRow(count-1)

    def actionRemove(self):
        item = self.notebookList.currentItem()
        row = self.notebookList.currentRow()
        name = item.data(Qt.DisplayRole)
        path = item.data(Qt.UserRole)
        self.notebookList.takeItem(row)

        Mikibook.remove(name, path)

    def moveItemUp(self):
        item = self.notebookList.currentItem()
        row = self.notebookList.currentRow()
        if row != 0:
            # self.notebookList.removeItemWidget(item)
            self.notebookList.takeItem(row)
            self.notebookList.insertItem(row-1, item)
            self.notebookList.setCurrentRow(row-1)

    def moveItemDown(self):
        item = self.notebookList.currentItem()
        row = self.notebookList.currentRow()
        count = self.notebookList.count()
        if row != count-1:
            self.notebookList.takeItem(row)
            self.notebookList.insertItem(row+1, item)
            self.notebookList.setCurrentRow(row+1)

    def accept(self):
        notebookPath = self.notebookList.currentItem().data(Qt.UserRole)
        notebookName = self.notebookList.currentItem().data(Qt.DisplayRole)
        settings = Setting([[notebookName, notebookPath]])
        window = mikidown.MikiWindow(settings)
        window.show()
        count = self.notebookList.count()
        notebooks = []
        for i in range(count):
            name = self.notebookList.item(i).data(Qt.DisplayRole)
            path = self.notebookList.item(i).data(Qt.UserRole)
            notebooks.append([name, path])
            Mikibook.write(notebooks)

        QDialog.accept(self)


class NewNotebookDlg(QDialog):
    def __init__(self, parent=None):
        super(NewNotebookDlg, self).__init__(parent)
        self.setWindowTitle('Add Notebook - mikidown')
        tipLabel = QLabel('Choose a name and folder for your notebook.' +
                          '\nThe folder can be an existing notebook folder.')
        self.nameEditor = QLineEdit()
        self.nameEditor.setText('Notes')
        nameLabel = QLabel('Name:')
        nameLabel.setBuddy(self.nameEditor)
        self.pathEditor = QLineEdit()
        # self.pathEditor.setText('~/mikidown')
        self.pathEditor.setText(os.path.expanduser('~').replace(os.sep,'/')+'/mikinotes')
        pathLabel = QLabel('Path:')
        pathLabel.setBuddy(self.pathEditor)
        browse = QPushButton('Browse')
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok |
                                     QDialogButtonBox.Cancel)

        grid = QGridLayout()
        grid.setRowMinimumHeight(1, 10)
        grid.setRowMinimumHeight(4, 10)
        grid.addWidget(tipLabel, 0, 0, 1, 4)
        grid.addWidget(nameLabel, 2, 0)
        grid.addWidget(self.nameEditor, 2, 1, 1, 4)
        grid.addWidget(pathLabel, 3, 0)
        grid.addWidget(self.pathEditor, 3, 1, 1, 4)
        grid.addWidget(browse, 3, 5)
        grid.addWidget(buttonBox, 5, 4, 1, 2)
        self.setLayout(grid)

        browse.clicked.connect(self.browse)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def browse(self):
        default = os.path.expanduser('~')
        path = QFileDialog.getExistingDirectory(self,
                                                "Select Folder",
                                                default,
                                                QFileDialog.ShowDirsOnly)
        self.pathEditor.setText(path)

    def closeEvent(self, event):
        event.accept()

class MikidownHighlightCfgWidget(QWidget):
    def __init__(self, parent=None):
        super(MikidownHighlightCfgWidget, self).__init__(parent)

class MikidownCfgDialog(QDialog):
    def __init__(self, parent=None):
        super(MikidownCfgDialog, self).__init__(parent)
        #tab = QWidget()
        #tab2 = QWidget()
        self.recentNotesCount = QSpinBox()
        recent_notes_n = Mikibook.settings.value('recentNotesNumber',type=int, defaultValue=20)
        self.recentNotesCount.setValue(recent_notes_n)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok |
                                          QDialogButtonBox.Cancel)

        layout = QGridLayout(self)
        layout.addWidget(QLabel("# of recently viewed notes to keep"),0,0,1,1)
        layout.addWidget(self.recentNotesCount,0,1,1,1)
        layout.addWidget(self.buttonBox,1,0,1,2)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def accept(self):
        Mikibook.settings.setValue('recentNotesNumber', self.recentNotesCount.value())
        QDialog.accept(self)

class Mikibook():
    # ~/.config/mikidown/mikidown.conf
    settings = QSettings(QSettings.IniFormat, QSettings.UserScope, 'mikidown', 'mikidown')
    lockpath = os.path.join(os.path.dirname(settings.fileName()),'lock').replace(os.sep,'/')

    @staticmethod
    def highlighterColors():
        items = []
        defaults = [ '#A40000',
                    "#4E9A06",
                    "#4E9A06",
                    "#4E9A06",
                    "#4E9A06",
                    "#A40000",
                    "#ff0037", #italic, not used
                    "#888A85",
                    "#888A85",
                    "#F57900",
                    "#F57900",
                    "#204A87", #underline color, not used atm
                    "#204A87",
                    "#F57900",
                    "#F57900",
                    "#F5006E"]
        size = Mikibook.settings.beginReadArray('highlighting')
        if size == 0:
            Mikibook.settings.endArray()
            Mikibook.setHighlighterColors(defaults)
            size = Mikibook.settings.beginReadArray('highlighting')
        for i in range(16):
            Mikibook.settings.setArrayIndex(i)
            items.append(Mikibook.settings.value('color', defaultValue=defaults[i], type=str))
        Mikibook.settings.endArray()
        return items

    @staticmethod
    def setHighlighterColors(items):
        Mikibook.settings.beginWriteArray('highlighting')
        for i,val in enumerate(items):
            Mikibook.settings.setArrayIndex(i)
            Mikibook.settings.setValue('color', val)
        Mikibook.settings.endArray()

    @staticmethod
    def read():
        """ Read notebook list from config file """
        version = Mikibook.settings.value("version", defaultValue=None)
        if not version: #before 0.3.4, since we're migrating the notebooklist to be plaintext
            Mikibook.nbListMigration()
        items = []
        size = Mikibook.settings.beginReadArray("notebookList")
        for i in range(size):
            Mikibook.settings.setArrayIndex(i)
            items.append((Mikibook.settings.value('name', type=str),
                        Mikibook.settings.value('path', type=str)))
        Mikibook.settings.endArray()
        return items

    @staticmethod
    def nbListMigration():
        books = readListFromSettings(Mikibook.settings, 'notebookList')
        Mikibook.write(books)

    @staticmethod
    def write(notebooks):
        """ Write notebook list to config file """
        Mikibook.settings.beginWriteArray("notebookList")
        for i, val in enumerate(notebooks):
            Mikibook.settings.setArrayIndex(i)
            Mikibook.settings.setValue('name', val[0])
            Mikibook.settings.setValue('path', val[1])
        Mikibook.settings.endArray()

    @staticmethod
    def create():
        """ Display a dialog to set notebookName and notebookPath """
        newNotebook = NewNotebookDlg()
        if newNotebook.exec_():
            notebookName = newNotebook.nameEditor.text()
            notebookPath = newNotebook.pathEditor.text()
            Mikibook.initialise(notebookName, notebookPath)

            notebooks = Mikibook.read()
            notebooks.append([notebookName, notebookPath])
            Mikibook.write(notebooks)

    @staticmethod
    def initialise(notebookName, notebookPath):
        """ Called by create()
        A notebook directory will be initialised to:
            css/  notebook.conf  notes/
        """

        # QDir().mkpath will create all necessary parent directories
        QDir().mkpath(os.path.join(notebookPath, "notes").replace(os.sep,'/'))
        QDir().mkpath(os.path.join(notebookPath, "css").replace(os.sep,'/'))
        cssFile = os.path.join(notebookPath, "css", "notebook.css").replace(os.sep,'/')
        searchCssFile = os.path.join(notebookPath, "css", "search-window.css").replace(os.sep,'/')
        cssTemplate = "/usr/share/mikidown/notebook.css"
        searchCssTemplate = "/usr/share/mikidown/search-window.css"
        if not os.path.exists(cssTemplate):
            cssTemplate = os.path.join(
                os.path.dirname(__file__), "css", "sphinx.css").replace(os.sep,'/')
        if not os.path.exists(searchCssTemplate):
            searchCssTemplate = os.path.join(
                os.path.dirname(__file__), "css" , "search-window.css").replace(os.sep,'/')
        # If //cssFile// already exists, copy() returns false!
        print(cssTemplate)
        print(searchCssTemplate)
        QFile.copy(cssTemplate, cssFile)
        QFile.copy(searchCssTemplate, searchCssFile)

    @staticmethod
    def remove(name, path):
        notebooks = Mikibook.read()
        notebooks.remove([name, path])
        Mikibook.write(notebooks)
