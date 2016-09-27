"""
Notebook management module.
"""

import os
import markdown
from copy import deepcopy

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets
"""
from PyQt4.QtCore import Qt, QDir, QFile, QSettings, QSize
from PyQt4.QtGui import (QAbstractItemDelegate, QAbstractItemView, QColor, QDialog, QDialogButtonBox, 
                         QFileDialog, QFont, QGridLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                         QPen, QPushButton, QStyle, QVBoxLayout, QTabWidget, QWidget, QBrush, QTreeWidget,
                         QTreeWidgetItem, QSpinBox, QScrollArea, QCheckBox, QIcon, QPalette, QFont)
"""
import mikidown

## TODO look at using QColorDialog ?
try:
    import slickpicker
    BETTER_COLOR_PICKER = True
except ImportError as e:
    print("Can't find slickpicker, falling back to QLineEdit for editing mikidown colors")
    BETTER_COLOR_PICKER = False
from .utils import allMDExtensions
from .config import Setting, readListFromSettings, writeListToSettings, writeDictToSettings
from .fontbutton import QFontButton

class ListDelegate(QtWidgets.QAbstractItemDelegate):
    """Customize view and behavior of notebook list"""

    def __init__(self, parent=None):
        super(ListDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        r = option.rect

        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillRect(r, self.parent().palette().highlight())
            fontPen = QtGui.QPen(self.parent().palette().highlightedText(), 1, Qt.SolidLine)
        else:
            painter.fillRect(r, self.parent().palette().base())
            fontPen = QtGui.QPen(self.parent().palette().text(), 1, Qt.SolidLine)

        painter.setPen(fontPen)

        name = index.data(Qt.DisplayRole)
        path = index.data(Qt.UserRole)

        imageSpace = 10
        # notebook name
        r = option.rect.adjusted(imageSpace, 0, -10, -20)
        name_font = QtGui.QFont(self.parent().font())
        name_font.setPointSize(10)
        name_font.setBold(True)
        if index.flags() == Qt.NoItemFlags:
            name_font.setStrikeOut(True)
        painter.setFont(name_font)
        painter.drawText(r.left(), r.top(), r.width(), r.height(), 
                         Qt.AlignBottom|Qt.AlignLeft, name)
        # notebook path
        path_font = QtGui.QFont(self.parent().font())
        path_font.setPointSize(8)
        if index.flags() == Qt.NoItemFlags:
            path_font.setStrikeOut(True)
        r = option.rect.adjusted(imageSpace, 20, -10, 0)
        painter.setFont(path_font)
        painter.drawText(r.left(), r.top(), r.width(), r.height(), 
                         Qt.AlignLeft, path)

    def sizeHint(self, option, index):
        return QtCore.QSize(200, 40)

class NotebookExtSettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, cfg_list=[]):
        super(NotebookExtSettingsDialog, self).__init__(parent)
        self.extCfgEdit = QtWidgets.QTreeWidget()
        self.extCfgEdit.setHeaderLabels(['Property', 'Value'])
        self.addRow = QtWidgets.QPushButton('+')
        self.removeRow = QtWidgets.QPushButton('-')
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                                                    QtWidgets.QDialogButtonBox.Cancel)

        layout = QtWidgets.QGridLayout(self)
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
        item = QtWidgets.QTreeWidgetItem(self.extCfgEdit, [prop_name, prop_val])
        item.setFlags(item.flags()|Qt.ItemIsEditable)
        #self.extCfgEdit.addTopLevelItem(item)

    def configToList(self):
        items = []
        for i in range(self.extCfgEdit.topLevelItemCount()):
            witem = self.extCfgEdit.topLevelItem(i)
            items.append((witem.text(0), witem.text(1)))
        return items

class NotebookSettingsDialog(QtWidgets.QDialog):
    """Dialog for adjusting notebook settings"""
    
    def __init__(self, parent=None):
        super(NotebookSettingsDialog, self).__init__(parent)
        self.setWindowTitle(self.tr("Notebook settings - mikidown"))
        
        # widgets for tab 1
        self.mdExts = QtWidgets.QListWidget()
        self.mjEdit = QtWidgets.QLineEdit()
        self.moveUp = QtWidgets.QPushButton('<<')
        self.moveDown = QtWidgets.QPushButton('>>')
        self.configureExtension = QtWidgets.QPushButton(self.tr('Edit Settings for this extension'))
        self.tmpdict = deepcopy(self.parent().settings.extcfg)
        
        # widgets for tab 2
        self.fExtEdit = QtWidgets.QLineEdit()
        self.attImgEdit = QtWidgets.QLineEdit()
        self.attDocEdit = QtWidgets.QLineEdit()
        
        # mandatory button box
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                                                    QtWidgets.QDialogButtonBox.Cancel)
        
        # tab panels
        tabs = QtWidgets.QTabWidget()
        markupTab = QtWidgets.QWidget()
        fileExtsTab = QtWidgets.QWidget()
        tabs.addTab(markupTab, "Markdown")
        tabs.addTab(fileExtsTab, self.tr("File extensions"))
        
        # initialization functions
        self.initExtList()
        self.mdExts.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.mjEdit.setText(self.parent().settings.mathjax)
        self.attImgEdit.setText(', '.join(self.parent().settings.attachmentImage))
        self.attDocEdit.setText(', '.join(self.parent().settings.attachmentDocument))
        self.fExtEdit.setText(self.parent().settings.fileExt)
        
        # set up tab 1
        layout = QtWidgets.QGridLayout(markupTab)
        layout.addWidget(QtWidgets.QLabel(self.tr("Markdown extensions")),0,0,1,4)
        layout.addWidget(self.mdExts,1,0,1,4)
        layout.addWidget(self.moveUp,2,0,1,1)
        layout.addWidget(self.moveDown,2,1,1,1)
        layout.addWidget(self.configureExtension,2,2,1,2)
        layout.addWidget(QtWidgets.QLabel(self.tr("MathJax Location")),3,0,1,1)
        layout.addWidget(self.mjEdit,3,1,1,3)
        
        # set up tab 2
        layout = QtWidgets.QGridLayout(fileExtsTab)
        layout.addWidget(QtWidgets.QLabel(self.tr("Note file extension")),0,0,1,1)
        layout.addWidget(QtWidgets.QLabel(self.tr("Image file extension")),1,0,1,1)
        layout.addWidget(QtWidgets.QLabel(self.tr("Document file extension")),2,0,1,1)
        layout.addWidget(self.fExtEdit,0,1,1,1)
        layout.addWidget(self.attImgEdit,1,1,1,1)
        layout.addWidget(self.attDocEdit,2,1,1,1)
        
        # put it together
        vlayout = QtWidgets.QVBoxLayout(self)
        vlayout.addWidget(tabs)
        vlayout.addWidget(self.buttonBox)

        # setup signal handlers
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
        extset = set(self.parent().settings.extensions)
        #for easier performance in checking
        for ext in self.parent().settings.extensions:
            item = QtWidgets.QListWidgetItem(ext, self.mdExts)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)

        for ext in self.parent().settings.faulty_exts:
            item = QtWidgets.QListWidgetItem(ext, self.mdExts)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setBackground(QtGui.QBrush(QtGui.QColor('red')))
            item.setForeground(QtGui.QBrush(QtGui.QColor('black')))
            item.setCheckState(Qt.Checked)

        for ext in allMDExtensions():
            if ext in extset: continue
            item = QtWidgets.QListWidgetItem(ext, self.mdExts)
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
        # write to settings first
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
        
        # then to memory
        msettings.extensions = extlist
        msettings.mathjax = self.mjEdit.text()
        msettings.attachmentDocument = readListFromSettings(nbsettings, 'attachmentDocument')
        msettings.attachmentImage = readListFromSettings(nbsettings, 'attachmentImage')
        msettings.extcfg.update(self.tmpdict)
        msettings.md = markdown.Markdown(msettings.extensions, extension_configs=msettings.extcfg)
        
        # then make mikidown use these settings NOW
        curitem=self.parent().notesTree.currentItem()
        self.parent().currentItemChangedWrapper(curitem, curitem)
        QtGui.QDialog.accept(self)

class NotebookListDialog(QtWidgets.QDialog):
    """Display, create, remove, modify notebookList """

    def __init__(self, parent=None):
        super(NotebookListDialog, self).__init__(parent)

        self.notebookList = QtWidgets.QListWidget()
        self.moveUp = QtWidgets.QPushButton('<<')
        self.moveDown = QtWidgets.QPushButton('>>')
        self.add = QtWidgets.QPushButton(self.tr('Add'))
        self.remove = QtWidgets.QPushButton(self.tr('Remove'))
        
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                                                    QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        
        layout = QtWidgets.QGridLayout()
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
            item = QtWidgets.QListWidgetItem()
            item.setData(Qt.DisplayRole, nb[0])
            item.setData(Qt.UserRole, nb[1])
            lockPath = os.path.join(nb[1], '.mikidown_lock')
            if os.path.exists(lockPath):
                item.setFlags(Qt.NoItemFlags)
            self.notebookList.addItem(item)

        self.updateUi(len(notebooks) != 0)
        self.notebookList.setCurrentRow(0)
        # QListWidgetItem(nb, self.notebookList) ???

    def updateUi(self, row):
        flag = (row != -1)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(flag)
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

        QtWidgets.QDialog.accept(self)

class NewNotebookDlg(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(NewNotebookDlg, self).__init__(parent)
        self.setWindowTitle(self.tr('Add Notebook - mikidown'))
        tipLabel = QtWidgets.QLabel(self.tr('Choose a name and folder for your notebook.') +
                          self.tr('\nThe folder can be an existing notebook folder.'))
        
        self.nameEditor = QtWidgets.QLineEdit()
        self.nameEditor.setText(self.tr('Notes'))
        nameLabel = QtWidgets.QLabel(self.tr('Name:'))
        nameLabel.setBuddy(self.nameEditor)
        
        self.pathEditor = QtWidgets.QLineEdit()
        # self.pathEditor.setText('~/mikidown')
        self.pathEditor.setText(os.path.expanduser('~').replace(os.sep,'/')+'/mikinotes')
        pathLabel = QtWidgets.QLabel(self.tr('Path:'))
        pathLabel.setBuddy(self.pathEditor)
        
        browse = QtWidgets.QPushButton(self.tr('Browse'))
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                                                QtWidgets.QDialogButtonBox.Cancel)

        grid = QtWidgets.QGridLayout()
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
        path = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                self.tr("Select Folder"),
                                                default,
                                                QtWidgets.QFileDialog.ShowDirsOnly)
        self.pathEditor.setText(path)

    def closeEvent(self, event):
        event.accept()

class MikidownHighlightCfgWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MikidownHighlightCfgWidget, self).__init__(parent)
        layout = QtWidgets.QGridLayout(self)
        colors = Mikibook.highlighterColors()
        for i in range(16):
            layout.addWidget(QtWidgets.QLabel(Mikibook.highlighter_labels[i]),i,0,1,1)
            if BETTER_COLOR_PICKER:
                layout.addWidget(slickpicker.QColorEdit(colors[i]),i,1,1,1)
            else:
                layout.addWidget(QtWidgets.QLineEdit(colors[i]),i,1,1,1)

    def configToList(self):
        items=[]
        for i in range(16):
            if BETTER_COLOR_PICKER:
                items.append(self.layout().itemAtPosition(i,1).widget().lineEdit.text())
            else:
                items.append(self.layout().itemAtPosition(i,1).widget().text())
        return items

class MikidownCfgDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(MikidownCfgDialog, self).__init__(parent)
        #tab = QWidget()
        #tab2 = QWidget()
        self.setWindowTitle(self.tr("Settings - mikidown"))
        self.recentNotesCount = QtWidgets.QSpinBox()
        recent_notes_n = Mikibook.settings.value('recentNotesNumber',type=int, defaultValue=20)
        self.recentNotesCount.setValue(recent_notes_n)
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                                                    QtWidgets.QDialogButtonBox.Cancel)
        self.hltCfg = MikidownHighlightCfgWidget(parent=self)
        self.tabWidth = QtWidgets.QSpinBox(self)
        self.tabWidth.setRange(2, 8)
        self.tabWidth.setSingleStep(2)
        self.iconTheme = QtWidgets.QLineEdit(self)
        self.iconTheme.setText(Mikibook.settings.value('iconTheme', QtGui.QIcon.themeName()))

        self.editorFont = QFontButton(parent=self)
        fontval = QtGui.QFont()
        fontfam = Mikibook.settings.value('editorFont', defaultValue=None)
        fontsize = Mikibook.settings.value('editorFontSize', type=int, defaultValue=12)
        if fontfam is not None:
            fontval.setFamily(fontfam)
        fontval.setPointSize(fontsize)

        self.headerScalesFont = QtWidgets.QCheckBox(self)
        if Mikibook.settings.value('headerScaleFont', type=bool, defaultValue=True):
            self.headerScalesFont.setCheckState(Qt.Checked)
        else:
            self.headerScalesFont.setCheckState(Qt.Unchecked)

        self.editorFont.font = fontval

        self.tabWidth.setValue(Mikibook.settings.value('tabWidth', type=int, defaultValue=4))

        self.tabToSpaces = QtWidgets.QCheckBox(self)
        if Mikibook.settings.value('tabInsertsSpaces', type=bool, defaultValue=True):
            self.tabToSpaces.setCheckState(Qt.Checked)
        else:
            self.tabToSpaces.setCheckState(Qt.Unchecked)

        self.minimizeToTray = QtWidgets.QCheckBox(self)
        if Mikibook.settings.value('minimizeToTray', type=bool, defaultValue=False):
            self.minimizeToTray.setCheckState(Qt.Checked)
        else:
            self.minimizeToTray.setCheckState(Qt.Unchecked)

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(QtWidgets.QLabel(self.tr("Minimize to tray?")),0,0,1,1)
        layout.addWidget(self.minimizeToTray,0,1,1,1)
        layout.addWidget(QtWidgets.QLabel(self.tr("# of recently viewed notes to keep")),1,0,1,1)
        layout.addWidget(self.recentNotesCount,1,1,1,1)
        layout.addWidget(QtWidgets.QLabel(self.tr("Editor font")), 2, 0, 1, 1)
        layout.addWidget(self.editorFont, 2, 1, 1, 1)
        layout.addWidget(QtWidgets.QLabel(self.tr("Header rank scales editor font?")), 3, 0, 1, 1)
        layout.addWidget(self.headerScalesFont, 3, 1, 1, 1)
        qs = QtWidgets.QScrollArea(self)
        qs.setWidget(self.hltCfg)
        layout.addWidget(QtWidgets.QLabel(self.tr("Tabs expand to spaces?")), 4, 0, 1, 1)
        layout.addWidget(self.tabToSpaces, 4, 1, 1, 1)
        layout.addWidget(QtWidgets.QLabel(self.tr("Tab width")), 5, 0, 1, 1)
        layout.addWidget(self.tabWidth, 5, 1, 1, 1)
        layout.addWidget(QtWidgets.QLabel(self.tr("Icon Theme")),6,0,1,1)
        layout.addWidget(self.iconTheme,6,1,1,1)
        layout.addWidget(qs,7,0,1,2)
        layout.addWidget(self.buttonBox,8,0,1,2)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def accept(self):
        Mikibook.settings.setValue('recentNotesNumber', self.recentNotesCount.value())
        Mikibook.settings.setValue('editorFont', self.editorFont.font.family())
        Mikibook.settings.setValue('editorFontSize', self.editorFont.font.pointSize())
        if self.headerScalesFont.isChecked():
            Mikibook.settings.setValue('headerScaleFont', True)
        else:
            Mikibook.settings.setValue('headerScaleFont', False)
        Mikibook.settings.setValue('tabWidth', self.tabWidth.value())
        Mikibook.settings.setValue('iconTheme', self.iconTheme.text())
        if self.tabToSpaces.isChecked():
            Mikibook.settings.setValue('tabInsertsSpaces', True)
        else:
            Mikibook.settings.setValue('tabInsertsSpaces', False)

        Mikibook.settings.setValue(
            'minimizeToTray',
            self.minimizeToTray.isChecked()
        )
        Mikibook.setHighlighterColors(self.hltCfg.configToList())
        QtGui.QIcon.setThemeName(self.iconTheme.text())

        #then make mikidown use these settings NOW
        self.parent().loadHighlighter()
        QtWidgets.QDialog.accept(self)

class Mikibook():
    # ~/.config/mikidown/mikidown.conf
    settings = QtCore.QSettings(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, 'mikidown', 'mikidown')
    lockpath = os.path.join(os.path.dirname(settings.fileName()),'lock').replace(os.sep,'/')
    highlighter_labels = [
            'HTML Tags', 
            '1<sup>st</sup> LVL headers', 
            '2<sup>nd</sup> LVL headers',
            '3<sup>rd</sup> LVL headers', 
            '4<sup>th</sup> and lower LVL headers',
            'HTML Symbols',
            'HTML comments',
            'Strikethrough',
            'Underline',
            'Bold', 
            'Italics',
            'Links', 
            'Links and images', 
            'Block Quotes',
            'Fenced Code',
            'Math'
    ]

    @staticmethod
    def highlighterColors():
        items = []
        defaults = ["#A40000",
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
        """Read notebook list from config file """
        version = Mikibook.settings.value("version", defaultValue=None)
        if not version: #before 0.3.4, since we're migrating the notebooklist to be plaintext
            Mikibook.nbListMigration()
            Mikibook.settings.setValue("version", "0") #dummy value until mikiwindow properly sets this
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
        #print("nbListMigration")
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
        #print("Mikibook.write:", Mikibook.settings.value("notebookList/size"))

    @staticmethod
    def create():
        """ Display a dialog to set notebookName and notebookPath """
        newNotebook = NewNotebookDlg()
        if newNotebook.exec_():
            notebookName = newNotebook.nameEditor.text()
            notebookPath = newNotebook.pathEditor.text()
            Mikibook.initialise(notebookName, notebookPath)

            notebooks = Mikibook.read()
            #print("Mikibook.create -> .read:",notebooks)
            notebooks.append([notebookName, notebookPath])
            Mikibook.write(notebooks)
            #print("Mikibook.create -> .read(2):", Mikibook.read())

    @staticmethod
    def initialise(notebookName, notebookPath):
        """ Called by create()
        A notebook directory will be initialised to:
            css/  notebook.conf  notes/
        """

        # QDir().mkpath will create all necessary parent directories
        QtCore.QDir().mkpath(os.path.join(notebookPath, "notes").replace(os.sep,'/'))
        QtCore.QDir().mkpath(os.path.join(notebookPath, "css").replace(os.sep,'/'))
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
        QtCore.QFile.copy(cssTemplate, cssFile)
        QtCore.QFile.copy(searchCssTemplate, searchCssFile)

    @staticmethod
    def remove(name, path):
        notebooks = Mikibook.read()
        notebooks.remove((name, path))
        Mikibook.write(notebooks)
