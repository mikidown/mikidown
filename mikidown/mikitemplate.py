import datetime
from enum import Enum
import shlex
import subprocess

from PyQt4.QtGui import QDialog, QListView, QAbstractItemDelegate, \
                        QComboBox, QWidget, QStandardItem, QStandardItemModel, \
                        QDialogButtonBox, QLabel
from PyQt4.QtCore import Qt

#BANNED_COMMANDS={'rm', 'cp', 'mv', 'unlink', 'mkdir', 'rmdir'}

# --- CORE FUNCTIONALITY
class TitleType(Enum):
    FSTRING  = 0
    DATETIME = 1
    #COMMAND  = 2

def makeDefaultBody(title, dt_in_body_txt):
    return makeTemplateBody(TitleType.FSTRING, "{}", userinput=title, dt_in_body_txt=dt_in_body_txt)

def makeTemplateBody(title_type, title, dt_in_body=True,
        dt_in_body_fmt="%Y-%m-%d", dt_in_body_txt="Created {}", 
        userinput="", body=""):

    dtnow = datetime.datetime.now()
    if title_type == TitleType.FSTRING:
        filled_title = title.format(userinput)
    elif title_type == TitleType.DATETIME:
        filled_title = dtnow.strftime(title)

    #elif title_type == TitleType.COMMAND:
    #    args = shlex.split(title)
    #    if args[0] in BANNED_COMMANDS:
    #        raise ValueError("{} contains banned command {}".format(args[0]))
    #    filled_title = subprocess.check_output(args).decode('utf-8')

    else:
        return

    if dt_in_body is True:
        formatted_dt = dt_in_body_txt.format(dtnow.strftime(dt_in_body_fmt))
        return "# {}\n{}\n\n{}".format(filled_title, formatted_dt, body)
    else:
        return "# {}\n{}".format(filled_title, body)

# --- WIDGETS
COL_DATA = Qt.UserRole
COL_EXTRA_DATA = COL_DATA + 1

class PickTemplateDialog(QDialog):
    def __init__(self, notebookSettings, parent=None):
        super().__init__(parent=parent)

        self.titleTemplates = QComboBox(self)
        self.bodyTemplates  = QComboBox(self)
        self.bodyTitlePairs = QComboBox(self)
        self.bodyTitlePairs.currentIndexChanged.connect(self.updateTitleBody)

        self.titleTemplates.setModel(notebookSettings.titleTemplates)
        self.bodyTemplates.setModel(notebookSettings.bodyTemplates)
        self.bodyTitlePairs.setModel(notebookSettings.bodyTitlePairs)

        layout = QGridLayout(self)
        layout.addWidget(QLabel(self.tr("Title template:")), 0, 0)
        layout.addWidget(self.titleTemplates, 0, 1)
        layout.addWidget(QLabel(self.tr("Body template:")), 1, 0)
        layout.addWidget(self.bodyTemplates, 1, 1)
        tmpLabel = QLabel(self.tr("--- OR ---"))
        tmpLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(tmpLabel, 2, 0, 1, 2)
        layout.addWidget(QLabel(self.tr("Quick pick pair...")), 3, 0)
        layout.addWidget(self.bodyTemplates, 3, 1)
        layout.addWidget(self.buttonBox, 4, 0, 1, 2)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def updateTitleBody(self, idx):
        modelItem = self.bodyTitlePairs.model().item(idx)
        if modelItem is not None:
            self.titleTemplates.setCurrentIndex(modelItem.data(COL_DATA))
            self.bodyTemplates.setCurrentIndex(self.bodyTemplates.findText(modelItem.data(COL_EXTRA_DATA)))

def genTitleTemplatesModel(values):
    model = QStandardItemModel()
    for value in values:
        item = QStandardItem()
        item.setText(value['friendlyName'])
        item.setData(value['content'], COL_DATA)
        item.setData(value['type'], COL_EXTRA_DATA)
        model.appendRow(item)
    return model

def genTitleBodyPairsModel(values):
    model = QStandardItemModel()
    for value in values:
        item = QStandardItem()
        item.setText(value['friendlyName'])
        item.setData(value['titleNum'], COL_DATA)
        item.setData(value['bodyTpl'], COL_EXTRA_DATA)
        model.appendRow(item)
    return model

def genBodyTemplatesModel(values):
    model = QStandardItemModel()
    for value in values:
        item = QStandardItem()
        item.setText(value)
        model.appendRow(item)
    return model
