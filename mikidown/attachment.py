import os

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets
"""
from PyQt4.QtCore import Qt, QDir, QFile, QRect, QSize
from PyQt4.QtGui import (QColor, QFileIconProvider, QFileSystemModel,
    QListView, QMenu, QPen, QPixmap, QStyle, QStyledItemDelegate)
"""

from urllib import parse as urlparse

class AttachmentItemDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, parent=None):
        super(AttachmentItemDelegate, self).__init__(parent)
        self.model = parent.model
        self.width = 96
        self.height = 128
        self.nameHeight = 48
        self.thumbHeight = self.height - self.nameHeight

    def paint(self, painter, option, index):
        filePath = self.model.filePath(index)
        fileName = self.model.fileName(index)
        r = option.rect

        img = QtGui.QPixmap(filePath)
        if img.isNull():
            # If not image file, try to load icon with QFileIconProvider
            # according to file type (extension name).
            # Currently not work as intended.
            fileInfo = self.model.fileInfo(index)
            icon = QtWidgets.QFileIconProvider().icon(fileInfo)
            img = icon.pixmap(QtCore.QSize(32, 32))

        # Scale to height, align center horizontally, align bottom vertically.
        if img.height() > self.thumbHeight:
            img = img.scaledToHeight(self.thumbHeight, Qt.SmoothTransformation)
        if img.width() > self.thumbHeight:
            img = img.scaledToWidth(self.thumbHeight, Qt.SmoothTransformation)
            
        imgLeft = (self.width - img.width()) / 2
        imgTop = self.thumbHeight - img.height()
        painter.drawPixmap(r.left() + imgLeft, r.top() + imgTop, img)

        rect = QtCore.QRect(r.left(), r.top() + self.thumbHeight,
                            self.width, self.nameHeight)
        flag = Qt.AlignHCenter | Qt.TextWrapAnywhere
        
        # get the bounding rectangle of the fileName
        bdRect = painter.boundingRect(rect, flag, fileName)
        if bdRect.height() < rect.height():
            rect = bdRect

        if option.state & QtWidgets.QStyle.State_Selected:
            painter.setBrush(self.parent().palette().highlight())
            painter.drawRoundedRect(rect, 5, 5)
            pen = QtGui.QPen(self.parent().palette().highlightedText(), 1, Qt.SolidLine)
        else:
            pen = QtGui.QPen(self.parent().palette().text(), 1, Qt.SolidLine)

        painter.setPen(pen)
        painter.drawText(rect, flag, fileName)

    def sizeHint(self, option, index):
        return QtCore.QSize(self.width + 16, self.height + 16)

class AttachmentView(QtWidgets.QListView):
    """A dockwidget displaying attachments of the current note."""

    def __init__(self, parent=None):
        super(AttachmentView, self).__init__(parent)
        self.parent = parent
        self.settings = parent.settings

        self.model = QtWidgets.QFileSystemModel()
        self.model.setFilter(QtCore.QDir.Files)
        self.model.setRootPath(self.settings.attachmentPath)
        self.setModel(self.model)

        # self.setRootIndex(self.model.index(self.settings.attachmentPath))
        self.setViewMode(QtWidgets.QListView.IconMode)
        self.setUniformItemSizes(True)
        self.setResizeMode(QtWidgets.QListView.Adjust)
        self.setItemDelegate(AttachmentItemDelegate(self))
        self.clicked.connect(self.click)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu()
        indice = self.selectedIndexes()
        if indice:
            menu.addAction(self.tr("Insert into note"), self.insert)
            menu.addAction(self.tr("Delete"), self.delete)
        menu.exec_(event.globalPos())

    def mousePressEvent(self, event):
        """ Trigger click() when an item is pressed.
        """
        self.clearSelection()
        QtWidgets.QListView.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        """ Trigger click() when an item is pressed.
        """
        self.clearSelection()
        QtWidgets.QListView.mouseReleaseEvent(self, event)

    def insert(self):
        indice = self.selectedIndexes()
        for i in indice:
            filePath = self.model.filePath(i)
            filePath = filePath.replace(self.settings.notebookPath, "..")
            fileName = os.path.basename(filePath)
            text = "![%s](%s)" % (fileName, urlparse.quote(filePath))
            self.parent.notesEdit.insertPlainText(text)

    def delete(self):
        indice = self.selectedIndexes()
        for i in indice:
            filePath = self.model.filePath(i)
            QtCore.QFile(filePath).remove()

    def click(self, index):
        self.setCurrentIndex(index)
