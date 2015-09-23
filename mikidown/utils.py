import os
import re
import pkgutil

import markdown
from markdown.extensions import __path__ as extpath
from markdown.extensions.headerid import slugify, unique
from PyQt4.QtCore import Qt, QFile, QRect
from PyQt4.QtGui import (QDialog, QDialogButtonBox, QGridLayout, QIcon, QLabel, QLineEdit, QMessageBox, QPainter, QPixmap)

JSCRIPT_TPL = '<script type="text/javascript" src="{}"></script>\n'
METADATA_CHECKER = re.compile(r'((?: {0,3}[\w\-]+:.*)(?:(?:\n {4,}.+)|(?:\n {0,3}[\w\-]+:.*))*)')

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
        if parent.objectName() in ["mikiWindow", "notesTree"]:
            editorLabel = QLabel(self.tr("Page Name:"))
            self.extNames = [".md", ".markdown", ".mkd"]
        # Copy Image to notesEdit
        elif parent.objectName() == "notesEdit":
            editorLabel = QLabel(self.tr("File Name:"))
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
                QMessageBox.warning(self, self.tr("Error"),
                                    self.tr("File already exists: %s") % notePath + ext)
                break
        if acceptable:
            QDialog.accept(self)

def allMDExtensions():
    exts=[]
    for m in pkgutil.iter_modules(path=extpath):
        exts.append(m[1])
    for m in pkgutil.iter_modules():
        if m[1].startswith('mdx_'):
            if pkgutil.find_loader(m[1][4:]) is None:
                #prefer the non-prefixed listing if there's no conflicting module
                exts.append(m[1][4:])
            else:
                #otherwise, prefer nonprefixed it if that really is the module for markdown
                try:
                    markdown.markdown("",extensions=[m[1][4:]])
                except AttributeError:
                    exts.append(m[1])
                else:
                    exts.append(m[1][4:])
    return exts

def parseHeaders(source, strip_fenced_block=False, strip_ascii_math=False):
    """ Parse headers to construct Table Of Contents
        return: [(level, text, position, anchor)]
        position/anchor is the header position in notesEdit/notesView
    """

    hdrs = []
    headers = []
    used_ids = set()           # In case there are headers with the same name.

    # copied from the asciimathml so we don't have to have a hard dependency to strip
    ASCIIMATHML_RE = re.compile(r'^(.*)\$\$([^\$]*)\$\$(.*)$', re.M)

    # copied from the fenced block code
    FENCED_BLOCK_RE = re.compile(r'''
(?P<fence>^(?:~{3,}|`{3,}))[ ]*         # Opening ``` or ~~~
(\{?\.?(?P<lang>[a-zA-Z0-9_+-]*))?[ ]*  # Optional {, and lang
# Optional highlight lines, single- or double-quote-delimited
(hl_lines=(?P<quot>"|')(?P<hl_lines>.*?)(?P=quot))?[ ]*
}?[ ]*\n                                # Optional closing }
(?P<code>.*?)(?<=\n)
(?P=fence)[ ]*$''', re.MULTILINE | re.DOTALL | re.VERBOSE)

    filtered_source = source
    #if applicable, strip out any trouble text before we start parsing the headers
    if strip_fenced_block:
        m = FENCED_BLOCK_RE.search(filtered_source)
        while m is not None:
            nfillers = (m.end() - m.start())
            filtered_source = FENCED_BLOCK_RE.sub("\n"*nfillers, filtered_source, count=1)
            m = FENCED_BLOCK_RE.search(filtered_source)

    if strip_ascii_math:
        m = ASCIIMATHML_RE.search(filtered_source)
        while m is not None:
            nfillers = (m.end() - m.start())
            filtered_source = ASCIIMATHML_RE.sub("\n"*nfillers, filtered_source, count=1)
            m = ASCIIMATHML_RE.search(filtered_source)


    # hash headers
    RE = re.compile(r'^(#+)(.+)', re.MULTILINE)
    for m in RE.finditer(filtered_source):
        level = len(m.group(1))
        hdr = m.group(2)
        pos = m.start()
        hdrs.append((pos, level, hdr))

    # setext headers
    RE = re.compile(r'(.+)\n([=-]+[ ]*)(\n|$)', re.MULTILINE)
    for m in RE.finditer(filtered_source):
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
