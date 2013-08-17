import os
from multiprocessing import Process
from PyQt4.QtCore import QDir, QFile, QFileInfo, QTextStream, QIODevice
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
