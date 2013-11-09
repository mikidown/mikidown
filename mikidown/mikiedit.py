import os
from multiprocessing import Process
from PyQt4.QtCore import QDir, QFile, QFileInfo, QTextStream, QIODevice, QMimeData, pyqtSignal
from PyQt4.QtGui import QTextEdit, QFileDialog, QMessageBox, QFont
from PyQt4.Qt import Qt
from PyQt4.Qt import QMouseEvent, QEvent, QAction, QTextCursor
import markdown
from whoosh.index import open_dir

from mikidown.config import *
from mikidown.utils import parseTitle

# Spell checker support
try:
    from enchant import Dict
except ImportError:
    print ("No spell checking available. Pyenchant is not installed.")
    class Dict:
        def check(self, *args):
            return True


class MikiEdit(QTextEdit):

    def __init__(self, parent=None):
        super(MikiEdit, self).__init__(parent)
        self.settings = parent.settings
        self.setFontPointSize(12)
        self.setTabStopWidth(4)
        self.setVisible(False)
        indexdir = os.path.join(self.settings.notebookPath, 
                                self.settings.indexdir)
        self.ix = open_dir(indexdir)
        self.speller = Dict()

    def updateIndex(self, path, content):
            ''' Update whoosh index, which cost much computing resource '''
            writer = self.ix.writer()
            writer.update_document(
                path=path, title=parseTitle(content, path), content=content)
            writer.commit()

    def insertFromMimeData(self, source):
        """ Intended behavior
        If copy/drag something that hasUrls, then check the extension name:
            if image then apply image pattern ![Alt text](/path/to/img.jpg)
                     else apply link  pattern [text](http://example.net)
        Else use the default insertFromMimeData implementation
        """
        
        def mimeFromText(text):
            mime = QMimeData()
            mime.setText(text)
            return mime
        
        if source.hasUrls():
            for qurl in source.urls():
                url = qurl.toString()
                filename, extension = os.path.splitext(url)
                filename = os.path.basename(filename)
                if extension.lower() in (".jpg", ".jpeg", ".png", ".gif", ".svg"):
                    text = "![%s](%s)" % (filename, url)
                else:
                    text = "[%s%s](%s)\n" % (filename, extension, url)
                super(MikiEdit, self).insertFromMimeData(mimeFromText(text))
        else:
            super(MikiEdit, self).insertFromMimeData(source)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            # Rewrite the mouse event to a left button event so the cursor is
            # moved to the location of the pointer.
            event = QMouseEvent(QEvent.MouseButtonPress, event.pos(),
                Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        QTextEdit.mousePressEvent(self, event)
 
    def contextMenuEvent(self, event):
        class SpellAction(QAction):
            correct = pyqtSignal(str)
            def __init__(self, *args):
                QAction.__init__(self, *args)
                self.triggered.connect(
                    lambda x: self.correct.emit(str(self.text()))
                )
 
 
        popup_menu = self.createStandardContextMenu()
 
        # Select the word under the cursor.
        cursor = self.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        self.setTextCursor(cursor)
 
        if self.textCursor().hasSelection():
            text = str(self.textCursor().selectedText())
            font = QFont()
            font.setBold(True)
            if not self.speller.check(text):
                lastAction = popup_menu.actions()[0]
                for word in self.speller.suggest(text)[:10]:
                    action = SpellAction(word, popup_menu)
                    action.setFont(font)
                    action.correct.connect(self.correctWord)
                    popup_menu.insertAction(lastAction, action)
                popup_menu.insertSeparator(lastAction)
        popup_menu.exec_(event.globalPos())
 
    def correctWord(self, word):
        '''
        Replaces the selected text with word.
        '''
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(word)
        cursor.endEditBlock()


    def save(self, pageName, filePath):
        fh = QFile(filePath)
        try:
            if not fh.open(QIODevice.WriteOnly):
                raise IOError(fh.errorString())
        except IOError as e:
            QMessageBox.warning(self, 'Save Error',
                                'Failed to save %s: %s' % (pageName, e))
        finally:
            if fh is not None:
                savestream = QTextStream(fh)
                savestream << self.toPlainText()
                fh.close()
                self.document().setModified(False)
                # Fork a process to update index, which benefit responsiveness.
                p = Process(target=self.updateIndex, args=(
                    pageName, self.toPlainText(),))
                p.start()

    def toHtml(self):
        '''markdown.Markdown.convert v.s. markdown.markdown
            Previously `convert` was used, but it doens't work with fenced_code
        '''
        htmltext = self.toPlainText()
        return markdown.markdown(htmltext, self.settings.extensions)
        # md = markdown.Markdown(extensions)
        # return md.convert(htmltext)

    def saveAsHtml(self):
        """ Export current note as html file
        """
        fileName = QFileDialog.getSaveFileName(self, self.tr('Export to HTML'),
                                               '', '(*.html *.htm);;'+self.tr('All files(*)'))
        if fileName == '':
            return
        if not QFileInfo(fileName).suffix():
            fileName += '.html'
        html = QFile(fileName)
        html.open(QIODevice.WriteOnly)
        savestream = QTextStream(html)
        css = QFile(self.settings.notebookPath + '/notes.css')
        css.open(QIODevice.ReadOnly)
        # Use a html lib may be a better idea?
        savestream << "<html><head><meta charset='utf-8'></head>"
        # Css is inlined.
        savestream << "<style>"
        savestream << QTextStream(css).readAll()
        savestream << "</style>"
        # Note content
        savestream << self.toHtml()
        savestream << "</html>"
        html.close()
