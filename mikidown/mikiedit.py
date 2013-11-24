import os
from multiprocessing import Process
from PyQt4.QtCore import Qt, QDir, QFile, QFileInfo, QMimeData, QIODevice, QTextStream, QUrl
from PyQt4.QtGui import QAction, QCursor, QFileDialog, QFont, QTextCursor, QTextEdit, QMessageBox
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest
import markdown
from whoosh.index import open_dir
import html2text

from .utils import LineEditDialog, parseTitle


class MikiEdit(QTextEdit):

    def __init__(self, parent=None):
        super(MikiEdit, self).__init__(parent)
        self.parent = parent
        self.settings = parent.settings
        self.setFontPointSize(12)
        self.setVisible(False)
        self.ix = open_dir(self.settings.indexdir)

        # Spell checker support
        try:
            import enchant
            enchant.Dict()
            self.speller = enchant.Dict()
        except ImportError:
            print("Spell checking unavailable. Need to install pyenchant.")
            self.speller = None
        except enchant.errors.DictNotFoundError:
            print("Spell checking unavailable. Need to install dictionary (e.g. aspell-en).")
            self.speller = None

        self.imageFilter = ""
        self.documentFilter = ""
        for ext in self.settings.attachmentImage:
            self.imageFilter += " *" + ext
        for ext in self.settings.attachmentDocument:
            self.documentFilter += " *" + ext
        self.imageFilter = "Image (" + self.imageFilter.strip() + ")"
        self.documentFilter = "Document (" + self.documentFilter.strip() + ")"

        self.downloadAs = ""
        self.networkManager = QNetworkAccessManager()
        self.networkManager.finished.connect(self.downloadFinished)


    def updateIndex(self):
            ''' Update whoosh index, which cost much computing resource '''
            page = self.parent.notesTree.currentPage()
            content = self.toPlainText()
            try:
                writer = self.ix.writer()
                writer.update_document(
                    path=page, title=parseTitle(content, page), content=content)
                writer.commit()
            except:
                print("Whoosh commit failed.")

    def downloadFinished(self, reply):
        if reply.error():
            print("Failed to download")
        else:
            attFile = QFile(self.downloadAs)
            attFile.open(QIODevice.WriteOnly)
            attFile.write(reply.readAll())
            attFile.close()
            print("Succeeded")
        reply.deleteLater()

    def mimeFromText(self, text):
        mime = QMimeData()
        mime.setText(text)
        return mime

    def createMimeDataFromSelection(self):
        """ Reimplement this to prevent copied text taken as hasHtml() """
        plaintext = self.textCursor().selectedText()

        # From QTextCursor doc:
        # if the selection obtained from an editor spans a line break,
        # the text will contain a Unicode U+2029 paragraph separator character
        # instead of a newline \n character
        text = plaintext.replace('\u2029', '\n')
        return self.mimeFromText(text)

    def insertFromMimeData(self, source):
        """ Intended behavior
        If copy/drag something that hasUrls, then check the extension name:
            if image then apply image pattern ![Alt text](/path/to/img.jpg)
                     else apply link  pattern [text](http://example.net)
        If copy/drag something that hasImage, then ask for file name
        If copy/drag something that hasHtml, then html2text
        Else use the default insertFromMimeData implementation
        """

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
                relativeFilePath = newFilePath.replace(self.settings.notebookPath, "..")
                attachments = self.settings.attachmentImage + self.settings.attachmentDocument

                if QUrl(qurl).isLocalFile():
                    if extension.lower() in attachments:
                        nurl = url.replace("file://", "")
                        QFile.copy(nurl, newFilePath)
                        self.parent.updateAttachmentView()

                        if extension.lower() in self.settings.attachmentImage:
                            text = "![%s](%s)" % (filename, relativeFilePath)
                        elif extension.lower() in self.settings.attachmentDocument:
                            text = "[%s%s](%s)\n" % (filename, extension, relativeFilePath)
                    else:
                        text = "[%s%s](%s)\n" % (filename, extension, url)
                else:
                    if extension.lower() in attachments:
                        self.downloadAs = newFilePath
                        self.networkManager.get(QNetworkRequest(qurl))

                        if extension.lower() in self.settings.attachmentImage:
                            text = "![%s](%s)" % (filename, relativeFilePath)
                        elif extension.lower() in self.settings.attachmentDocument:
                            text = "[%s%s](%s)\n" % (filename, extension, relativeFilePath)
                    else:
                        text = "[%s%s](%s)\n" % (filename, extension, url)

                super(MikiEdit, self).insertFromMimeData(self.mimeFromText(text))
        elif source.hasImage():
            img = source.imageData()
            attDir = self.parent.notesTree.itemToAttachmentDir(item)
            dialog = LineEditDialog(attDir, self)
            if dialog.exec_():
                fileName = dialog.editor.text()
                if not QFileInfo(fileName).suffix():
                    fileName += '.jpg'
                filePath = os.path.join(attDir, fileName)
                img.save(filePath)
                relativeFilePath = filePath.replace(self.settings.notebookPath, "..")
                text = "![%s](%s)" % (fileName, relativeFilePath)
                super(MikiEdit, self).insertFromMimeData(self.mimeFromText(text))
        elif source.hasHtml():
            backToMarkdown = html2text.HTML2Text()
            html = source.html()
            markdown = backToMarkdown.handle(html)
            super(MikiEdit, self).insertFromMimeData(self.mimeFromText(markdown))
        else:
            super(MikiEdit, self).insertFromMimeData(source)

    def insertAttachment(self, filePath, fileType):
        item = self.parent.notesTree.currentItem()
        attDir = self.parent.notesTree.itemToAttachmentDir(item)
        filename, extension = os.path.splitext(filePath)
        filename = os.path.basename(filename)
        newFilePath = os.path.join(attDir, filename + extension)
        relativeFilePath = newFilePath.replace(self.settings.notebookPath, "..")
        QFile.copy(filePath, newFilePath)
        self.parent.updateAttachmentView()
        if fileType == self.imageFilter:
            text = "![%s](%s)" % (filename, relativeFilePath)
        else:
            text = "[%s%s](%s)\n" % (filename, extension, relativeFilePath)
        self.insertPlainText(text)

    def insertAttachmentWrapper(self):
        (filePath, fileType) = QFileDialog.getSaveFileNameAndFilter(
            self, self.tr('Insert attachment'), '',
            self.imageFilter + ";;" + self.documentFilter)
        if filePath == "":
            return
        self.insertAttachment(filePath, fileType)

    def contextMenuEvent(self, event):

        def correctWord(cursor, word):
            # From QTextCursor doc:
            # if there is a selection, the selection is deleted and replaced
            return lambda: cursor.insertText(word)

        popup_menu = self.createStandardContextMenu()

        # Spellcheck the word under mouse cursor, not self.textCursor
        cursor = self.cursorForPosition(event.pos())
        cursor.select(QTextCursor.WordUnderCursor)

        text = cursor.selectedText()
        if self.speller and text:
            if not self.speller.check(text):
                lastAction = popup_menu.actions()[0]
                for word in self.speller.suggest(text)[:10]:
                    action = QAction(word, popup_menu)
                    action.triggered.connect(correctWord(cursor, word))
                    action.setFont(QFont("sans", weight=QFont.Bold))
                    popup_menu.insertAction(lastAction, action)
                popup_menu.insertSeparator(lastAction)

        popup_menu.exec_(event.globalPos())

    def keyPressEvent(self, event):
        """ for Qt.Key_Tab, expand as 4 spaces
            for other keys, use default implementation
        """
        if event.key() == Qt.Key_Tab:
            self.insertPlainText('    ')
        else:
            QTextEdit.keyPressEvent(self, event)

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
                Process(target=self.updateIndex).start()

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
