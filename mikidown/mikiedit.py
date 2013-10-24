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
        if source.hasImage():
            print ("We have an image ...")
        elif source.hasUrls():
            for qurl in source.urls():
                if qurl.isLocalFile():
                    fullPath = qurl.toLocalFile()
                    filename, extension = os.path.splitext(fullPath)
                    filename = os.path.basename(filename)
                    # TODO: copy the refference file
                    if extension.lower() in (".jpg", ".jpeg", ".png", ".gif"):
                        toInsert = "![%s](%s)" % (filename, fullPath)
                    else:
                        toInsert = "[%s%s](%s)\n" % (filename, extension, fullPath)
                    super(MikiEdit, self).insertFromMimeData(self._mimeFromText(toInsert))
                else:
                    super(MikiEdit, self).insertFromMimeData(
                            self._mimeFromText(
                                "[Broken Link](Remote content not yet supported)")
                    )
        elif source.hasHtml():
            # QT will process this HTML and not add it verbatim to the editor 
            html = source.html()
            # TODO: can we do some reversing on the pasted html ?
            super(MikiEdit, self).insertFromMimeData(self._mimeFromText(html))
        else:
            super(MikiEdit, self).insertFromMimeData(source)

    def _mimeFromText(self, text):
        mime =  QMimeData()
        mime.setText(text)
        return mime

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
        if self.settings.autoSaveHtml:
            try:
                filename, ext = os.path.splitext(filePath)
                self.saveAsHtml("%s.html" % filename)
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
