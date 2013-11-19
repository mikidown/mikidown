"""
Notebook management module.
"""

import os

from PyQt4.QtCore import Qt, QDir, QFile, QSettings, QSize
from PyQt4.QtGui import (QAbstractItemDelegate, QAbstractItemView, QColor, QDialog, QDialogButtonBox, QFileDialog, QFont, QGridLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPen, QPushButton, QStyle)

import mikidown
from .config import Setting, readListFromSettings, writeListToSettings


class ListDelegate(QAbstractItemDelegate):
    """ Customize view and behavior of notebook list """

    def __init__(self, parent=None):
        super(ListDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        r = option.rect
        fontPen = QPen(QColor.fromRgb(51, 51, 51), 1, Qt.SolidLine)

        if option.state & QStyle.State_Selected:
            painter.setBrush(Qt.cyan)
            painter.drawRect(r)
        else:
            painter.setBrush(
                Qt.white if (index.row() % 2) == 0 else QColor(252, 252, 252))
            painter.drawRect(r)

        painter.setPen(fontPen)

        name = index.data(Qt.DisplayRole)
        path = index.data(Qt.UserRole)

        imageSpace = 10
        # notebook name
        r = option.rect.adjusted(imageSpace, 0, -10, -20)
        painter.setFont(QFont('Lucida Grande', 10, QFont.Bold))
        painter.drawText(r.left(), r.top(
        ), r.width(), r.height(), Qt.AlignBottom|Qt.AlignLeft, name)
        # notebook path
        r = option.rect.adjusted(imageSpace, 20, -10, 0)
        painter.setFont(QFont('Lucida Grande', 8, QFont.Normal))
        painter.drawText(
            r.left(), r.top(), r.width(), r.height(), Qt.AlignLeft, path)

    def sizeHint(self, option, index):
        return QSize(200, 40)


class NotebookListDialog(QDialog):
    """ Funtions to display, create, remove, modify notebookList """

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
        self.pathEditor.setText(os.environ['HOME']+'/mikinotes')
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
        default = os.environ['HOME']
        path = QFileDialog.getExistingDirectory(self,
                                                "Select Folder",
                                                default,
                                                QFileDialog.ShowDirsOnly)
        self.pathEditor.setText(path)

    def closeEvent(self, event):
        event.accept()


class Mikibook():

    # ~/.config/mikidown/mikidown.conf
    settings = QSettings('mikidown', 'mikidown')

    def read():
        """ Read notebook list from config file """
        return readListFromSettings(Mikibook.settings, 'notebookList')

    def write(notebooks):
        """ Write notebook list to config file """
        return writeListToSettings(
            Mikibook.settings, 'notebookList', notebooks)

    def create():
        """ Display a dialog to set notebookName and notebookPath """
        newNotebook = NewNotebookDlg()
        if newNotebook.exec_():
            notebookName = newNotebook.nameEditor.text()
            notebookPath = newNotebook.pathEditor.text()
            Mikibook.initialise(notebookName, notebookPath)

            notebooks = Mikibook.read()
            notebooks.append([notebookName, notebookPath])
            # TODO: make mikidown.conf become plain text
            Mikibook.write(notebooks)

    def initialise(notebookName, notebookPath):
        """ Called by create()
        A notebook directory will be initialised to:
            css/  notebook.conf  notes/
        """

        # QDir().mkpath will create all necessary parent directories
        QDir().mkpath(os.path.join(notebookPath, "notes"))
        QDir().mkpath(os.path.join(notebookPath, "css"))
        cssFile = os.path.join(notebookPath, "css", "notebook.css")
        cssTemplate = "/usr/share/mikidown/notebook.css"
        if not os.path.exists(cssTemplate):
            cssTemplate = os.path.join(
                os.path.dirname(__file__), "notebook.css")
        # If //cssFile// already exists, copy() returns false!
        QFile.copy(cssTemplate, cssFile)

    def remove(name, path):
        notebooks = Mikibook.read()
        notebooks.remove([name, path])
        Mikibook.write(notebooks)
