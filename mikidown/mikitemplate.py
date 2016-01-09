import datetime
from enum import Enum
from os import path
import shlex
import subprocess

from PyQt4.QtGui import QDialog, QListView, QGridLayout, QAbstractItemDelegate, \
                        QComboBox, QWidget, QStandardItem, QStandardItemModel, \
                        QDialogButtonBox, QLabel, QLineEdit, QTabWidget, \
                        QHBoxLayout, QVBoxLayout, QPushButton, QCheckBox, QTextEdit, \
                        QFontMetrics, QMessageBox
from PyQt4.QtCore import Qt, QFile, QTextStream, QIODevice

from .highlighter import MikiHighlighter
from .mikibook import Mikibook
from .mikiedit import MikiEdit
from .utils import NOTE_EXTS, doesFileExist, LineEditDialog, TTPL_COL_DATA, TTPL_COL_EXTRA_DATA

#BANNED_COMMANDS={'rm', 'cp', 'mv', 'unlink', 'mkdir', 'rmdir'}

# --- CORE FUNCTIONALITY
class TitleType(Enum):
    FSTRING  = 0
    DATETIME = 1
    #COMMAND  = 2

def makeDefaultBody(title, dt_in_body_txt):
    dtnow = datetime.datetime.now()
    filled_title = makeTemplateTitle(TitleType.FSTRING, "{}", dtnow=dtnow, userinput=title)
    return makeTemplateBody(filled_title, dt_in_body_txt=dt_in_body_txt)

def makeTemplateTitle(title_type, title, dtnow=None, userinput=""):
    if dtnow is None:
        dtnow = datetime.datetime.now()

    if title_type == TitleType.FSTRING:
        filled_title = title.format(userinput)
    elif title_type == TitleType.DATETIME:
        filled_title = dtnow.strftime(title).format(userinput)
    #elif title_type == TitleType.COMMAND:
    #    args = shlex.split(title)
    #    if args[0] in BANNED_COMMANDS:
    #        raise ValueError("{} contains banned command {}".format(args[0]))
    #    filled_title = subprocess.check_output(args).decode('utf-8')
    else:
        return
    return filled_title

def makeTemplateBody(filled_title, dt_in_body=True, dtnow=None,
        dt_in_body_fmt="%Y-%m-%d", dt_in_body_txt="Created {}", 
        userinput="", body=""):
    if dtnow is None:
        dtnow = datetime.datetime.now()

    if filled_title is None:
        return

    if dt_in_body is True:
        formatted_dt = dt_in_body_txt.format(dtnow.strftime(dt_in_body_fmt))
        return "# {}\n{}\n\n{}".format(filled_title, formatted_dt, body)
    else:
        return "# {}\n{}".format(filled_title, body)

# --- WIDGETS

class EditTitleTemplateDialog(QDialog):
    def __init__(self, pos, settings, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle(self.tr("Edit title template"))
        self.pos = pos
        self.titleFriendlyName = QLineEdit(self)
        self.titleTemplateContent = QLineEdit(self)
        self.titleTemplateContent.textChanged.connect(self.updateUi)
        self.usesDate = QCheckBox(self)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | 
                                          QDialogButtonBox.Cancel)
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        self.settings = settings

        layout = QGridLayout(self)
        layout.addWidget(QLabel(self.tr("Friendly name")), 0, 0)
        layout.addWidget(self.titleFriendlyName, 0, 1)
        layout.addWidget(QLabel(self.tr("Title template")), 1, 0)
        layout.addWidget(self.titleTemplateContent, 1, 1)
        layout.addWidget(QLabel(self.tr("Uses date?")), 2, 0)
        layout.addWidget(self.usesDate, 2, 1)
        layout.addWidget(self.buttonBox, 3, 1, 1, 2)

        if self.pos != -1:
            item = self.settings.titleTemplates.item(self.pos)
            self.titleFriendlyName.setText(item.text())
            self.titleTemplateContent.setText(item.data(TTPL_COL_DATA))
            if item.data(TTPL_COL_EXTRA_DATA) == TitleType.DATETIME:
                self.usesDate.setCheckState(Qt.Checked)
            else:
                self.usesDate.setCheckState(Qt.Unchecked)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def updateUi(self, newstr):
        if newstr:
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    def accept(self):
        acceptable = False
        tplContent = self.titleTemplateContent.text()
        try:
            if self.usesDate.isChecked():
                makeTemplateTitle(TitleType.DATETIME, tplContent, userinput="TestString")
            else:
                makeTemplateTitle(TitleType.FSTRING, tplContent, userinput="TestString")
            acceptable = True
        except Exception as e:
            acceptable = False
            emessage = e.message

        if acceptable:
            if self.pos != -1:
                item = self.settings.titleTemplates.item(self.pos)
                item.setText(self.titleFriendlyName.text())
                item.setData(tplContent, TTPL_COL_DATA)
                if self.usesDate.isChecked():
                    item.setData(TitleType.DATETIME, TTPL_COL_EXTRA_DATA)
                else:
                    item.setData(TitleType.FSTRING, TTPL_COL_EXTRA_DATA)
            else:
                item = QStandardItem()
                item.setText(self.titleFriendlyName.text())
                item.setData(tplContent, TTPL_COL_DATA)
                if self.usesDate.isChecked():
                    item.setData(TitleType.DATETIME, TTPL_COL_EXTRA_DATA)
                else:
                    item.setData(TitleType.FSTRING, TTPL_COL_EXTRA_DATA)
                self.settings.titleTemplates.appendRow(item)
            QDialog.accept(self)
        else:
            QMessageBox.warning(self, self.tr("Error"),
            self.tr("Title format invalid: %s") % emessage)

class EditBodyTemplateDialog(QDialog):
    def __init__(self, fpath, settings, parent=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.setWindowTitle(self.tr("Edit body template"))

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | 
                                          QDialogButtonBox.Cancel)

        self.templateEdit = MikiEdit(self)
        fnt = Mikibook.settings.value('editorFont', defaultValue=None)
        fntsize = Mikibook.settings.value('editorFontSize', type=int, defaultValue=12)
        header_scales_font = Mikibook.settings.value('headerScaleFont', type=bool, defaultValue=True)
        if fnt is not None:
            self.templateEdit.setFontFamily(fnt)
            self.templateEdit.setFontPointSize(fntsize)
        h = MikiHighlighter(parent=self.templateEdit, scale_font_sizes=header_scales_font)
        tw = Mikibook.settings.value('tabWidth', type=int, defaultValue=4)
        qfm = QFontMetrics(h.patterns[0][1].font())
        self.templateEdit.setTabStopWidth(tw * qfm.width(' '))
        self.templateEdit.setVisible(True)

        fh = QFile(fpath)
        try:
            if not fh.open(QIODevice.ReadOnly):
                raise IOError(fh.errorString())
        except IOError as e:
            QMessageBox.warning(self, self.tr("Read Error"),
                                self.tr("Failed to open %s: %s") % (fpath, e))
        finally:
            if fh is not None:
                noteBody = QTextStream(fh).readAll()
                fh.close()
                self.templateEdit.setPlainText(noteBody)
                self.templateEdit.document().setModified(False)

        layout = QVBoxLayout(self)
        layout.addWidget(self.templateEdit)
        layout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

class ManageTitlesWidget(QWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent=parent)
        self.settings = settings

        layout = QVBoxLayout(self)
        self.titlesList = QListView()
        self.titlesList.setModel(self.settings.titleTemplates)

        self.buttonBox = QHBoxLayout()
        editButton = QPushButton(self.tr("Edit"))
        addButton = QPushButton("+")
        delButton = QPushButton("-")
        self.buttonBox.addWidget(editButton)
        self.buttonBox.addWidget(addButton)
        self.buttonBox.addWidget(delButton)

        editButton.clicked.connect(self.editItem)
        delButton.clicked.connect(self.deleteItems)
        addButton.clicked.connect(self.addItem)

        layout.addWidget(self.titlesList)
        layout.addLayout(self.buttonBox)

    def editItem(self, checked):
        idx = self.titlesList.currentIndex()
        dialog = EditTitleTemplateDialog(idx.row(), self.settings, parent=self)

        if dialog.exec_():
            self.settings.updateTitleTemplates()

    def addItem(self, checked):
        contents = self.titlesList.model()

        item = QStandardItem()
        item.setText("Test Date Format (YYYYmmdd)")
        item.setData("%Y%m%d_Test_{}", TTPL_COL_DATA)
        item.setData(TitleType.DATETIME, TTPL_COL_EXTRA_DATA)
        contents.appendRow(item)

        self.settings.updateTitleTemplates()

    def deleteItems(self, checked):
        items = self.titlesList.selectedIndexes()
        contents = self.titlesList.model()

        for idx in reversed(items):
            contents.takeRow(idx.row())

        self.settings.updateTitleTemplates()


class ManageBodiesWidget(QWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent=parent)
        self.settings = settings

        self.bodiesList = QListView()
        self.bodiesList.setModel(self.settings.bodyTemplates)
        pathToIdx = self.settings.bodyTemplates.index(self.settings.templatesPath)
        self.bodiesList.setRootIndex(pathToIdx)

        self.buttonBox = QHBoxLayout()
        editButton = QPushButton(self.tr("Edit"))
        addButton = QPushButton("+")
        delButton = QPushButton("-")
        self.buttonBox.addWidget(editButton)
        self.buttonBox.addWidget(addButton)
        self.buttonBox.addWidget(delButton)

        editButton.clicked.connect(self.editItem)
        delButton.clicked.connect(self.deleteItems)
        addButton.clicked.connect(self.addItem)

        layout = QVBoxLayout(self)
        layout.addWidget(self.bodiesList)
        layout.addLayout(self.buttonBox)

    def editItem(self, checked):
        idx = self.bodiesList.currentIndex()
        model = self.bodiesList.model()
        filePath = model.filePath(idx)
        if not path.isfile(filePath):
            return

        dialog = EditBodyTemplateDialog(filePath, self.settings, parent=self)
        if dialog.exec_():
            fh = QFile(filePath)
            try:
                if not fh.open(QIODevice.WriteOnly):
                    raise IOError(fh.errorString())
            except IOError as e:
                QMessageBox.warning(self, self.tr("Save Error"),
                                    self.tr("Failed to save %s: %s") % (path.basename(filepath), e))
                raise
            finally:
                if fh is not None:
                    savestream = QTextStream(fh)
                    savestream << dialog.templateEdit.toPlainText()
                    fh.close()

    def deleteItems(self, checked):
        items = self.bodiesList.selectedIndexes()
        contents = self.bodiesList.model()

        for idx in reversed(items):
            contents.remove(idx)

    def addItem(self, checked):
        dialog = LineEditDialog(self.settings.templatesPath, self)
        if dialog.exec_():
            templateName = '{}{}'.format(dialog.editor.text(), self.settings.fileExt)
            outPath = path.join(self.settings.templatesPath, templateName)
            with open(outPath, 'w', encoding='utf-8') as f:
                pass


class ManageTemplatesDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle(self.tr("Manage templates"))
        self.settings = settings

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Close)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.templatePages = QTabWidget()

        self.titlesPage = ManageTitlesWidget(settings)
        self.bodiesPage = ManageBodiesWidget(settings)

        self.templatePages.addTab(self.titlesPage, self.tr("Titles"))
        self.templatePages.addTab(self.bodiesPage, self.tr("Bodies"))

        layout = QVBoxLayout(self)
        layout.addWidget(self.templatePages)
        layout.addWidget(self.buttonBox)


class PickTemplateDialog(QDialog):
    def __init__(self, path, settings, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle(self.tr("Create note from template"))
        self.path = path

        self.titleTemplates = QComboBox(self)
        self.bodyTemplates  = QComboBox(self)
        self.bodyTitlePairs = QComboBox(self)
        self.titleTemplateParameter = QLineEdit(self)
        self.bodyTitlePairs.currentIndexChanged.connect(self.updateTitleBody)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok |
                                          QDialogButtonBox.Cancel)
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        self.settings = settings

        self.titleTemplates.setModel(self.settings.titleTemplates)
        self.bodyTemplates.setModel(self.settings.bodyTemplates)
        pathToIdx = self.settings.bodyTemplates.index(self.settings.templatesPath)
        self.bodyTemplates.setRootModelIndex(pathToIdx)
        self.bodyTemplates.model().directoryLoaded.connect(self.updateUi)
        self.bodyTitlePairs.setModel(self.settings.bodyTitlePairs)

        layout = QGridLayout(self)
        layout.addWidget(QLabel(self.tr("Title template:")), 0, 0)
        layout.addWidget(self.titleTemplates, 0, 1)

        layout.addWidget(QLabel(self.tr("Title parameter:")), 1, 0)
        layout.addWidget(self.titleTemplateParameter, 1, 1)

        layout.addWidget(QLabel(self.tr("Body template:")), 2, 0)
        layout.addWidget(self.bodyTemplates, 2, 1)

        tmpLabel = QLabel(self.tr("--- OR ---"))
        tmpLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(tmpLabel, 3, 0, 1, 2)

        layout.addWidget(QLabel(self.tr("Quick pick pair...")), 4, 0)
        layout.addWidget(self.bodyTitlePairs, 4, 1)
        layout.addWidget(self.buttonBox, 5, 0, 1, 2)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.updateUi()

    def accept(self):
        dtnow = datetime.datetime.now()
        curTitleIdx = self.titleTemplates.currentIndex()
        titleItem = self.titleTemplates.model().item(curTitleIdx)
        titleItemContent = titleItem.data(TTPL_COL_DATA)
        titleItemType = titleItem.data(TTPL_COL_EXTRA_DATA)
        titleParameter = self.titleTemplateParameter.text()
        newPageName = makeTemplateTitle(titleItemType, 
            titleItemContent, dtnow=dtnow, userinput=titleParameter)
        notePath = path.join(self.path, newPageName)
        acceptable, existPath = doesFileExist(notePath, NOTE_EXTS)
        if acceptable:
            QDialog.accept(self)
        else:
            QMessageBox.warning(self, self.tr("Error"),
            self.tr("File already exists: %s") % existPath)

    def updateUi(self):
        comboModel = self.bodyTemplates.model()
        rowCount = comboModel.rowCount()
        itemIdx = comboModel.index(0, 0, parent=self.bodyTemplates.rootModelIndex())
        singleNotRoot = itemIdx.isValid()
        shouldEnable = rowCount > 1 or singleNotRoot
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(shouldEnable)
        self.bodyTemplates.setEnabled(shouldEnable)

    def updateTitleBody(self, idx):
        modelItem = self.bodyTitlePairs.model().item(idx)
        if modelItem is not None:
            self.titleTemplates.setCurrentIndex(modelItem.data(TTPL_COL_DATA))
            self.bodyTemplates.setCurrentIndex(self.bodyTemplates.findText(modelItem.data(TTPL_COL_EXTRA_DATA)))
