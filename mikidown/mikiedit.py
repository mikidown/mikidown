from PyQt4.QtCore import QFile, QTextStream, QIODevice
from PyQt4.QtGui import QTextEdit 
import markdown
from whoosh.index import open_dir

from mikidown.config import *

class MikiEdit(QTextEdit):

    def __init__(self, settings, parent=None):
        super(MikiEdit, self).__init__(parent)
        self.setFontPointSize(12)
        self.setTabStopWidth(4)
        self.setVisible(False)
        self.ix = open_dir(Default.indexdir)

        # Enabled extensions of python-markdown
        self.extensions = readListFromSettings(settings, 'extensions')
        if not self.extensions:
            self.extensions = Default.extensionList
            writeListToSettings(settings, 'extensions', self.extensions)
        # This is needed if a GUI to select extensions is provided later.
        settings.setValue('extensions', self.extensions)
        
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
                #fileobj = open(filePath, 'r')
                #content = fileobj.read()
                #fileobj.close()
                self.document().setModified(False)
                ''' update whoosh index '''
                writer = self.ix.writer()
                writer.update_document(path = pageName, content = self.toPlainText())
                writer.commit()

    def toHtml(self):
        '''markdown.Markdown.convert v.s. markdown.markdown
            Previously `convert` was used, but it doens't work with fenced_code
        '''
        htmltext = self.toPlainText()
        return markdown.markdown(htmltext, self.extensions)
        #md = markdown.Markdown(extensions)
        #return md.convert(htmltext)

    def saveNoteAsHtml(self):
        fileName = QFileDialog.getSaveFileName(self, self.tr('Export to HTML'), '',
                '(*.html *.htm);;'+self.tr('All files(*)'))
        if fileName == '':
            return
        if not QFileInfo(fileName).suffix():
            fileName += '.html'
        fh = QFile(fileName)
        fh.open(QIODevice.WriteOnly)
        savestream = QTextStream(fh)
        savestream << self.toHtml()
        fh.close()


