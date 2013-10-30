import os
from multiprocessing import Process
from PyQt4.QtCore import QDir, QFile, QFileInfo, QTextStream, QIODevice, QMimeData
from PyQt4.QtGui import QTextEdit, QFileDialog, QMessageBox
import markdown
from whoosh.index import open_dir

from mikidown.config import *
from mikidown.utils import parseTitle


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


    def save(self, pageName, filePath):
        fh = QFile(filePath)
        try:
            if not fh.open(QIODevice.WriteOnly):
                raise IOError(fh.errorString())
        except IOError as e:
            QMessageBox.warning(self, 'Save Error',
                                'Failed to save %s: %s' % (pageName, e))
            raise
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

        # If autoSaveHtml == True, current note will be autoSaved as 
        # **preview.html** in notebook folder
        if self.settings.autoSaveHtml:
            try:
                filename = os.path.join(self.settings.notebookPath, 
                                        "preview.html")
                self.saveAsHtml(filename)
            except IOError as e:
                QMessageBox.warning(self, 'Save Error',
                        'Failed to save %s: %s' % (pageName, e))
                raise

    def toHtml(self):
        '''markdown.Markdown.convert v.s. markdown.markdown
            Previously `convert` was used, but it doens't work with fenced_code
        '''
        htmltext = self.toPlainText()
        return markdown.markdown(htmltext, self.settings.extensions)
        # md = markdown.Markdown(extensions)
        # return md.convert(htmltext)

    def saveAsHtml(self, fileName = None):
        """ Export current note as html file
        """
        if not fileName:
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
