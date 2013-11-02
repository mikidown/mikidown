from PyQt4.QtCore import *
from PyQt4.QtGui import *

class AttachmentItemDelegate(QStyledItemDelegate):

    def __init__(self, model, parent=None):
        super(AttachmentItemDelegate, self).__init__(parent)
        self.model = model
        self.width = 96
        self.height = 96

    def paint(self, painter, option, index):
        filePath = self.model.filePath(index)
        fileName = self.model.fileName(index)
        r = option.rect
        img = QPixmap(filePath)
        if img.isNull():
            fileInfo = self.model.fileInfo(index)
            icon = QFileIconProvider().icon(fileInfo)
            img = icon.pixmap(QSize(32, 32))
        imgLeft = (self.width - img.width()) / 2
        imgTop = (self.height - 32 - img.height()) / 2
        painter.drawPixmap(r.left()+imgLeft, r.top()+imgTop, img)
        painter.drawText(QRect(r.left(), r.top()+64, 96, 32), 
            Qt.AlignHCenter | Qt.TextWrapAnywhere, fileName)

    def sizeHint(self, option, index):
        return QSize(self.width + 16, self.height + 16)

class AttachmentView(QListView):

    def __init__(self, parent=None):
        super(AttachmentView, self).__init__(parent)
        self.settings = parent.settings

        model = QFileSystemModel()
        model.setRootPath(self.settings.attachmentPath)
        self.setModel(model)
        self.setRootIndex(model.index(self.settings.attachmentPath))
        self.setViewMode(QListView.IconMode)
        self.setUniformItemSizes(True)
        self.setResizeMode(QListView.Adjust)
        self.setItemDelegate(AttachmentItemDelegate(model, self))
