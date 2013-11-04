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
        self.parent = parent
        self.settings = parent.settings
        self.setFontPointSize(12)
        self.setTabStopWidth(4)
        self.setVisible(False)
        indexdir = os.path.join(self.settings.notePath, 
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

        item = self.parent.notesTree.currentItem()
        attDir = self.parent.notesTree.itemToAttachmentDir(item)
        if not QDir(attDir).exists():
            QDir().mkpath(attDir)

        if source.hasUrls():
            for qurl in source.urls():
                url = qurl.toString()
                filename, extension = os.path.splitext(url)
                filename = os.path.basename(filename)
                newFilePath = os.path.join(attDir, filename + extension)

                # TODO: Add a recognized file types list to config, 
                # listed file types will be copied to attDir 
                if extension.lower() in self.settings.attachmentImage:
                    url = url.replace("file://", "")
                    QFile.copy(url, newFilePath)
                    self.parent.updateAttachmentView()

                    # Rewrite as relative file path
                    newFilePath = newFilePath.replace(self.settings.notebookPath, "..")
                    text = "![%s](%s)" % (filename, newFilePath)
                elif extension.lower() in self.settings.attachmentDocument:
                    url = url.replace("file://", "")
                    QFile.copy(url, newFilePath)
                    self.parent.updateAttachmentView()

                    # Rewrite as relative file path
                    newFilePath = newFilePath.replace(self.settings.notebookPath, "..")
                    text = "[%s%s](%s)\n" % (filename, extension, newFilePath)
                else:
                    text = "[%s%s](%s)\n" % (filename, extension, url)
                super(MikiEdit, self).insertFromMimeData(mimeFromText(text))
        else:
            super(MikiEdit, self).insertFromMimeData(source)

    def save(self, item):
        pageName = self.parent.notesTree.itemToPage(item)
        filePath = self.parent.notesTree.itemToFile(item)
        htmlFile = self.parent.notesTree.itemToHtmlFile(item)

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
                self.saveHtmlOnly(htmlFile)
            except IOError as e:
                QMessageBox.warning(self, 'Save Error',
                        'Failed to saveHtml %s: %s' % (pageName, e))
                raise

    def toHtml(self):
        '''markdown.Markdown.convert v.s. markdown.markdown
            Previously `convert` was used, but it doens't work with fenced_code
        '''
        htmltext = self.toPlainText()
        return markdown.markdown(htmltext, self.settings.extensions)
        # md = markdown.Markdown(extensions)
        # return md.convert(htmltext)

    def saveAsHtml(self, htmlFile = None):
        """ Save as Complete (with css and images) or HTML Only
            To be merged with saveNoteAs
        """
        if not htmlFile:
            (htmlFile, htmlType) = QFileDialog.getSaveFileNameAndFilter(
                self, self.tr("Export to HTML"), "", "Complete;;HTML Only")
        if htmlFile == '':
            return
        if not QFileInfo(htmlFile).suffix():
            htmlFile += '.html'

        if htmlType == "Complete":
            self.saveCompleteHtml(htmlFile)
        else:
            self.saveHtmlOnly(htmlFile)

    def saveCompleteHtml(self, htmlFile):
        html = QFile(htmlFile)
        html.open(QIODevice.WriteOnly)
        savestream = QTextStream(html)
        css = QFile(self.settings.cssfile)
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

    def saveHtmlOnly(self, htmlFile):
        fileDir = os.path.dirname(htmlFile)
        QDir().mkpath(fileDir)

        html = QFile(htmlFile)
        html.open(QIODevice.WriteOnly)
        savestream = QTextStream(html)
        savestream << """
                      <html><head>
                        <meta charset="utf-8">
                        <link rel="stylesheet" href="/css/notebook.css" type="text/css" />
                      </head>
                      """
        # Note content
        savestream << self.toHtml()
        savestream << "</html>"
        html.close()
