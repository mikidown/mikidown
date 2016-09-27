from enum import Enum
import os
import re
import pkgutil

import markdown
from markdown.extensions import __path__ as extpath
from markdown.extensions.headerid import slugify, unique

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets
"""
from PyQt4.QtCore import Qt, QFile, QRect
from PyQt4.QtGui import (QDialog, QDialogButtonBox, QGridLayout, QIcon, QLabel, QLineEdit, QMessageBox, QPainter, QPixmap)
"""
JSCRIPT_TPL = '<script type="text/javascript" src="{}"></script>\n'
METADATA_CHECKER = re.compile(r'((?: {0,3}[\w\-]+:.*)(?:(?:\n {4,}.+)|(?:\n {0,3}[\w\-]+:.*))*)')

class TitleType(Enum):
    FSTRING  = 0
    DATETIME = 1
    #COMMAND  = 2

TTPL_COL_DATA = Qt.ToolTipRole
TTPL_COL_EXTRA_DATA = Qt.UserRole

class Event(list):
    """
    Event subscription.

    A list of callable objects. Calling an instance of this will cause a
    call to each item in the list in ascending order by index.

    Source: http://stackoverflow.com/a/2022629

    Example Usage:

    >>> def f(x):
    ...     print 'f(%s)' % x
    >>> def g(x):
    ...     print 'g(%s)' % x
    >>> e = Event()
    >>> e()
    >>> e.append(f)
    >>> e(123)
    f(123)
    >>> e.remove(f)
    >>> e()
    >>> e += (f, g)
    >>> e(10)
    f(10)
    g(10)
    >>> del e[0]
    >>> e(2)
    g(2)

    """
    def __call__(self, *args, **kwargs):
        for f in self:
            f(*args, **kwargs)

    def __repr__(self):
        return "Event(%s)" % list.__repr__(self)

class ViewedNoteIcon(QtGui.QIcon):
    def __init__(self, num, parent=None):
        super(ViewedNoteIcon, self).__init__(parent)
        pixmap = QtGui.QPixmap(16, 16)
        pixmap.fill(Qt.cyan)
        rect = QtCore.QRect(0, 0, 16, 16)
        painter = QtGui.QPainter(pixmap)
        painter.drawText(rect, Qt.AlignHCenter | Qt.AlignVCenter, str(num))
        self.addPixmap(pixmap)
        del painter

def confirmAction(title, msg, parent=None):
    return QtWidgets.QMessageBox.question(
        parent,
        title, msg,
        buttons=(
            QtWidgets.QMessageBox.Yes
            | QtWidgets.QMessageBox.No
        )
    )


NOTE_EXTS = ['.md', '.markdown', '.mkd']
IMAGE_EXTS = ['', '.jpg']
class LineEditDialog(QtWidgets.QDialog):
    """ A dialog asking for page/file name.
        It also checks for name crash.
    """

    def __init__(self, path, parent=None):
        super(LineEditDialog, self).__init__(parent)
        self.path = path

        # newPage/newSubpage
        if parent.objectName() in ["mikiWindow", "notesTree"]:
            editorLabel = QtWidgets.QLabel(self.tr("Page Name:"))
            self.extNames = NOTE_EXTS
        # Copy Image to notesEdit
        elif parent.objectName() == "notesEdit":
            editorLabel = QtWidgets.QLabel(self.tr("File Name:"))
            self.extNames = IMAGE_EXTS
        else:
            editorLabel = QtWidgets.QLabel(self.tr("Template Name:"))
            self.extNames = NOTE_EXTS

        self.editor = QtWidgets.QLineEdit()
        editorLabel.setBuddy(self.editor)
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                                                    QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        layout = QtWidgets.QGridLayout()
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
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(
            self.editor.text() != "")

    def accept(self):
        notePath = os.path.join(self.path, self.editor.text())

        acceptable, existPath = doesFileExist(notePath, self.extNames)
        if acceptable:
            QtWidgets.QDialog.accept(self)
        else:
            QtWidgets.QMessageBox.warning(self, self.tr("Error"),
                        self.tr("File already exists: %s") % existPath)

def doesFileExist(path, altExts):
    doesntExist = True
    existPath = None
    for ext in altExts:
        if QtCore.QFile.exists(path + ext):
            doesntExist = False
            existPath = path + ext
            break
    return [doesntExist, existPath]

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

# http://stackoverflow.com/questions/1736015/debugging-a-pyqt4-app
def debugTrace():
    from PyQt5.QtCore import pyqtRemoveInputHook, pyqtRestoreInputHook
    import pdb
    import sys
    pyqtRemoveInputHook()
    try:
        debugger = pdb.Pdb()
        debugger.reset()
        debugger.do_next(None)
        user_frame = sys._getframe().f_back
        debugger.interaction(user_frame, None)
    finally:
        pyqtRestoreInputHook()
