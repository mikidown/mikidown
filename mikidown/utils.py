import os
import re
from markdown.extensions.headerid import slugify, unique
from PyQt4.QtCore import Qt, QFile, QRect
from PyQt4.QtGui import (QDialog, QDialogButtonBox, QGridLayout, QIcon, QLabel, QLineEdit, QMessageBox, QPainter, QPixmap)


class ViewedNoteIcon(QIcon):
    def __init__(self, num, parent=None):
        super(ViewedNoteIcon, self).__init__(parent)
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.cyan)
        rect = QRect(0, 0, 16, 16)
        painter = QPainter(pixmap)
        painter.drawText(rect, Qt.AlignHCenter | Qt.AlignVCenter, str(num))
        self.addPixmap(pixmap)
        del painter

class LineEditDialog(QDialog):
    """ A dialog asking for page/file name.
        It also checks for name crash.
    """

    def __init__(self, path, parent=None):
        super(LineEditDialog, self).__init__(parent)
        self.path = path

        # newPage/newSubpage
        if parent.objectName() == "notesTree":
            editorLabel = QLabel("Page Name:")
            self.extNames = [".md", ".markdown", ".mkd"]
        # Copy Image to notesEdit
        elif parent.objectName() == "notesEdit":
            editorLabel = QLabel("File Name:")
            self.extNames = ["", ".jpg"]
        else:
            return

        self.editor = QLineEdit()
        editorLabel.setBuddy(self.editor)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok |
                                          QDialogButtonBox.Cancel)
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        layout = QGridLayout()
        layout.addWidget(editorLabel, 0, 0)
        layout.addWidget(self.editor, 0, 1)
        layout.addWidget(self.buttonBox, 1, 1)
        self.setLayout(layout)

        self.editor.textEdited.connect(self.updateUi)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def setText(self, text):
        self.editor.setText(text)
        self.editor.selectAll()

    def updateUi(self):
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
            self.editor.text() != "")

    def accept(self):
        notePath = os.path.join(self.path, self.editor.text())

        acceptable = True
        for ext in self.extNames:
            if QFile.exists(notePath + ext):
                acceptable = False
                QMessageBox.warning(self, 'Error',
                                    'File already exists: %s' % notePath + ext)
                break
        if acceptable:
            QDialog.accept(self)

def parseHeaders(source):
    """ Parse headers to construct Table Of Contents
        return: [(level, text, position, anchor)]
        position/anchor is the header position in notesEdit/notesView
    """

    hdrs = []
    headers = []
    used_ids = set()           # In case there are headers with the same name.

    # hash headers
    RE = re.compile(r'^(#+)(.+)', re.MULTILINE)
    for m in RE.finditer(source):
        level = len(m.group(1))
        hdr = m.group(2)
        pos = m.start()
        hdrs.append((pos, level, hdr))

    # setext headers
    RE = re.compile(r'(.+)\n([=-]+[ ]*)(\n|$)', re.MULTILINE)
    for m in RE.finditer(source):
        if m.group(2).startswith('='):
            level = 1
        else:
            level = 2
        hdr = m.group(1)
        pos = m.start()
        hdrs.append((pos, level, hdr))

    hdrs.sort()
    for (p, l, h) in hdrs:
        anchor = unique(slugify(h, '-'), used_ids)
        headers.append((l, h, p, anchor))
    return headers

def parseTitle(source, fallback):
    """ Quite basic title parser, the first header1 is taken as title """
    title_re = re.compile(r'^#([^#].+)')
    title = title_re.search(source)
    if title:
        return title.group(1).strip()
    else:
        return fallback
