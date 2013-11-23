import os
from PyQt4.QtCore import Qt, QDir, QFile, QRect, QSize
from PyQt4.QtGui import (QColor, QFileIconProvider, QFileSystemModel,
    QListView, QMenu, QPen, QPixmap, QStyle, QStyledItemDelegate)

class AttachmentItemDelegate(QStyledItemDelegate):

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

        img = QPixmap(filePath)
        if img.isNull():
            # If not image file, try to load icon with QFileIconProvider
            # according to file type (extension name).
            # Currently not work as intended.
            fileInfo = self.model.fileInfo(index)
            icon = QFileIconProvider().icon(fileInfo)
            img = icon.pixmap(QSize(32, 32))

        # Scale to height, align center horizontally, align bottom vertically.
        if img.height() > self.thumbHeight:
            img = img.scaledToHeight(self.thumbHeight, Qt.SmoothTransformation)
        imgLeft = (self.width - img.width()) / 2
        imgTop = self.thumbHeight - img.height()
        painter.drawPixmap(r.left()+imgLeft, r.top()+imgTop, img)

        rect = QRect(r.left(), r.top()+self.thumbHeight,
                     self.width, self.nameHeight)
        flag = Qt.AlignHCenter | Qt.TextWrapAnywhere
        # get the bounding rectangle of the fileName
        bdRect = painter.boundingRect(rect, flag, fileName)
        if bdRect.height() < rect.height():
            rect = bdRect

        if option.state & QStyle.State_Selected:
            painter.setBrush(Qt.darkBlue)
            painter.drawRoundedRect(rect, 5, 5)
            pen = QPen(QColor.fromRgb(255, 255, 255), 1, Qt.SolidLine)
        else:
            pen = QPen(QColor.fromRgb(51, 51, 51), 1, Qt.SolidLine)

        painter.setPen(pen)
        painter.drawText(rect, flag, fileName)

    def sizeHint(self, option, index):
        return QSize(self.width + 16, self.height + 16)

class AttachmentView(QListView):
    """ A dockWidget displaying attachments of the current note.
    """

    def __init__(self, parent=None):
        super(AttachmentView, self).__init__(parent)
        self.parent = parent
        self.settings = parent.settings

        self.model = QFileSystemModel()
        self.model.setFilter(QDir.Files)
        self.model.setRootPath(self.settings.attachmentPath)
        self.setModel(self.model)

        # self.setRootIndex(self.model.index(self.settings.attachmentPath))
        self.setViewMode(QListView.IconMode)
        self.setUniformItemSizes(True)
        self.setResizeMode(QListView.Adjust)
        self.setItemDelegate(AttachmentItemDelegate(self))
        self.clicked.connect(self.click)

    def contextMenuEvent(self, event):
        menu = QMenu()
        indice = self.selectedIndexes()
        if len(indice):
            menu.addAction("Insert into note", self.insert)
            menu.addAction("Delete", self.delete)
        else:
            pass
        menu.exec_(event.globalPos())

    def mousePressEvent(self, event):
        """ Trigger click() when an item is pressed.
        """
        self.clearSelection()
        QListView.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        """ Trigger click() when an item is pressed.
        """
        self.clearSelection()
        QListView.mouseReleaseEvent(self, event)

    def insert(self):
        indice = self.selectedIndexes()
        for i in indice:
            filePath = self.model.filePath(i)
            filePath = filePath.replace(self.settings.notebookPath, "..")
            fileName = os.path.basename(filePath)
            text = "![%s](%s)" % (fileName, filePath)
            self.parent.notesEdit.insertPlainText(text)

    def delete(self):
        indice = self.selectedIndexes()
        for i in indice:
            filePath = self.model.filePath(i)
            QFile(filePath).remove()

    def click(self, index):
        self.setCurrentIndex(index)
