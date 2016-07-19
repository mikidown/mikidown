import os
from threading import Thread
from multiprocessing import Process

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork
"""
from PyQt4.QtCore import Qt, QDir, QFile, QFileInfo, QMimeData, QIODevice, QTextStream, QUrl
from PyQt4.QtGui import QAction, QCursor, QFileDialog, QFont, QTextCursor, QTextEdit, QMessageBox, QKeySequence, QApplication
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest
"""
import markdown
from whoosh.index import open_dir
from whoosh.writing import AsyncWriter
try:
    import html2text
    HAS_HTML2TEXT=True # let's make this user configurable later?
except ImportError:
    HAS_HTML2TEXT=False

from urllib import parse as urlparse
from .utils import LineEditDialog, parseTitle, JSCRIPT_TPL, METADATA_CHECKER
from .mikibook import Mikibook

class SimpleMikiEdit(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.settings = parent.settings
        self.setFontPointSize(12)
        self.setVisible(False)

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

    def insertFromRawHtml(self):
        qclippy = QtWidgets.QApplication.clipboard()
        if qclippy.mimeData().hasHtml():
            self.insertFromMimeData(self.mimeFromText(qclippy.mimeData().html()))
        else:
            self.insertFromMimeData(qclippy.mimeData())

    def keyPressEvent(self, event):
        """ for Qt.Key_Tab, expand as 4 spaces (if expandTab is enabled)
            for other keys, use default implementation
        """

        moddies = QtWidgets.QApplication.keyboardModifiers()
        expandTab = Mikibook.settings.value(
            'tabInsertsSpaces',
            type=bool,
            defaultValue=True
        )
        if event.key() == Qt.Key_Tab and expandTab:
            tabWidth = Mikibook.settings.value('tabWidth', type=int, defaultValue=4)
            self.insertPlainText(' ' * tabWidth) # use the tabWidth for tabstop!
        elif moddies & Qt.ControlModifier and moddies & Qt.ShiftModifier and event.key() == Qt.Key_V:
            self.insertFromRawHtml()
        else:
            QtWidgets.QTextEdit.keyPressEvent(self, event)

    def contextMenuEvent(self, event):

        def correctWord(cursor, word):
            # From QTextCursor doc:
            # if there is a selection, the selection is deleted and replaced
            return lambda: cursor.insertText(word)

        popup_menu = self.createStandardContextMenu()
        paste_action = popup_menu.actions()[6]
        paste_formatted_action = QtWidgets.QAction(self.tr("Paste raw HTML"), popup_menu)
        paste_formatted_action.triggered.connect(self.insertFromRawHtml)
        paste_formatted_action.setShortcut(QtGui.QKeySequence("Ctrl+Shift+V"))
        popup_menu.insertAction(paste_action, paste_formatted_action)

        # Spellcheck the word under mouse cursor, not self.textCursor
        cursor = self.cursorForPosition(event.pos())
        cursor.select(QtGui.QTextCursor.WordUnderCursor)

        text = cursor.selectedText()
        if self.speller and text:
            if not self.speller.check(text):
                lastAction = popup_menu.actions()[0]
                for word in self.speller.suggest(text)[:10]:
                    action = QtWidgets.QAction(word, popup_menu)
                    action.triggered.connect(correctWord(cursor, word))
                    defaultFamily = QtWidgets.QApplication.font().family()
                    action.setFont(QtGui.QFont(defaultFamily, weight=QtGui.QFont.Bold))
                    popup_menu.insertAction(lastAction, action)
                popup_menu.insertSeparator(lastAction)

        popup_menu.exec_(event.globalPos())

    def mimeFromText(self, text):
        mime = QtCore.QMimeData()
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
        if source.hasHtml():
            html = source.html()
            if HAS_HTML2TEXT:
                backToMarkdown = html2text.HTML2Text()
                markdown = backToMarkdown.handle(html)
                super(SimpleMikiEdit, self).insertFromMimeData(self.mimeFromText(markdown))
            else:
                super(SimpleMikiEdit, self).insertFromMimeData(self.mimeFromText(source.text()))
        else:
            super(SimpleMikiEdit, self).insertFromMimeData(source)

class MikiEdit(SimpleMikiEdit):
    def __init__(self, parent=None):
        super(MikiEdit, self).__init__(parent)
        self.ix = open_dir(self.settings.indexdir)

        self.imageFilter = ""
        self.documentFilter = ""
        for ext in self.settings.attachmentImage:
            self.imageFilter += " *" + ext
        for ext in self.settings.attachmentDocument:
            self.documentFilter += " *" + ext
        self.imageFilter = "Image (" + self.imageFilter.strip() + ")"
        self.documentFilter = "Document (" + self.documentFilter.strip() + ")"

        self.downloadAs = ""
        self.networkManager = QtNetwork.QNetworkAccessManager()
        self.networkManager.finished.connect(self.downloadFinished)


    def updateIndex(self):
        ''' Update whoosh index, which cost much computing resource '''
        page = self.parent.notesTree.currentPage()
        content = self.toPlainText()
        try:
            #writer = self.ix.writer()
            writer = AsyncWriter(self.ix)
            if METADATA_CHECKER.match(content) and 'meta' in self.settings.extensions:
                no_metadata_content = METADATA_CHECKER.sub("", content, count=1).lstrip()
                self.settings.md.reset().convert(content)
                writer.update_document(
                    path=page, title=parseTitle(content, page), content=no_metadata_content,
                    tags=','.join(self.settings.md.Meta.get('tags', [])).strip())
                writer.commit()
            else:
                writer.update_document(
                    path=page, title=parseTitle(content, page), content=content, tags='')
                writer.commit()
        except:
            print("Whoosh commit failed.")

    def downloadFinished(self, reply):
        if reply.error():
            print("Failed to download")
        else:
            attFile = QtCore.QFile(self.downloadAs)
            attFile.open(QtCore.QIODevice.WriteOnly)
            attFile.write(reply.readAll())
            attFile.close()
            print("Succeeded")
        reply.deleteLater()

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
        if not QtCore.QDir(attDir).exists():
            QtCore.QDir().mkpath(attDir)

        if source.hasUrls():
            for qurl in source.urls():
                url = qurl.toString()
                filename, extension = os.path.splitext(url)
                filename = os.path.basename(filename)
                newFilePath = os.path.join(attDir, filename + extension).replace(os.sep, '/')
                relativeFilePath = newFilePath.replace(self.settings.notebookPath, "..")
                quotedRFPath = urlparse.quote(relativeFilePath)
                attachments = self.settings.attachmentImage + self.settings.attachmentDocument

                if QtCore.QUrl(qurl).isLocalFile():
                    if extension.lower() in attachments:
                        nurl = url.replace("file://", "")
                        QtCore.QFile.copy(nurl, newFilePath)
                        self.parent.updateAttachmentView()

                        if extension.lower() in self.settings.attachmentImage:
                            text = "![%s](%s)" % (filename, quotedRFPath)
                        elif extension.lower() in self.settings.attachmentDocument:
                            text = "[%s%s](%s)\n" % (filename, extension, quotedRFPath)
                    else:
                        text = "[%s%s](%s)\n" % (filename, extension, url)
                else:
                    if extension.lower() in attachments:
                        self.downloadAs = newFilePath
                        self.networkManager.get(QtNetwork.QNetworkRequest(qurl))

                        if extension.lower() in self.settings.attachmentImage:
                            text = "![%s](%s)" % (filename, quotedRFPath)
                        elif extension.lower() in self.settings.attachmentDocument:
                            text = "[%s%s](%s)\n" % (filename, extension, quotedRFPath)
                    else:
                        text = "[%s%s](%s)\n" % (filename, extension, url)

                super(MikiEdit, self).insertFromMimeData(self.mimeFromText(text))
        elif source.hasImage():
            img = source.imageData()
            attDir = self.parent.notesTree.itemToAttachmentDir(item)
            dialog = LineEditDialog(attDir, self)
            if dialog.exec_():
                fileName = dialog.editor.text()
                if not QtCore.QFileInfo(fileName).suffix():
                    fileName += '.jpg'
                filePath = os.path.join(attDir, fileName).replace(os.sep, '/')
                img.save(filePath)
                relativeFilePath = filePath.replace(self.settings.notebookPath, "..")
                text = "![%s](%s)" % (fileName, quotedRFPath)
                super(MikiEdit, self).insertFromMimeData(self.mimeFromText(text))
        else:
            super(MikiEdit, self).insertFromMimeData(source)

    def insertAttachment(self, filePath, fileType):
        item = self.parent.notesTree.currentItem()
        attDir = self.parent.notesTree.itemToAttachmentDir(item)
        filename, extension = os.path.splitext(filePath)
        filename = os.path.basename(filename)
        newFilePath = os.path.join(attDir, filename + extension).replace(os.sep, '/')
        relativeFilePath = newFilePath.replace(self.settings.notebookPath, "..")
        quotedRFPath = urlparse.quote(relativeFilePath)
        if not os.path.exists(attDir):
            os.makedirs(attDir)
        QtCore.QFile.copy(filePath, newFilePath)
        self.parent.updateAttachmentView()
        if fileType == self.imageFilter:
            text = "![%s](%s)" % (filename, quotedRFPath)
        else:
            text = "[%s%s](%s)\n" % (filename, extension, quotedRFPath)
        self.insertPlainText(text)

    def insertAttachmentWrapper(self):
        (filePath, fileType) = QtWidgets.QFileDialog.getOpenFileName(
            self, self.tr('Insert attachment'), self.settings.notePath,
            self.imageFilter + ";;" + self.documentFilter)
        if filePath == "":
            return
        self.insertAttachment(filePath, fileType)

    '''
    def closeEvent(self, event):
        self.ix.close()
        print('closed idx')
        event.accept()
    '''
    def save(self, item):
        pageName = self.parent.notesTree.itemToPage(item)
        filePath = self.parent.notesTree.itemToFile(item)
        htmlFile = self.parent.notesTree.itemToHtmlFile(item)

        fh = QtCore.QFile(filePath)
        try:
            if not fh.open(QtCore.QIODevice.WriteOnly):
                raise IOError(fh.errorString())
        except IOError as e:
            QtWidgets.QMessageBox.warning(self, self.tr("Save Error"),
                                self.tr("Failed to save %s: %s") % (pageName, e))
            raise
        finally:
            if fh is not None:
                savestream = QtCore.QTextStream(fh)
                savestream.setCodec("UTF-8")
                savestream << self.toPlainText()
                fh.close()
                self.document().setModified(False)

                # Fork a process to update index, which benefit responsiveness.
                Thread(target=self.updateIndex).start()


    def toHtml(self):
        '''markdown.Markdown.convert v.s. markdown.markdown
            ~~Previously `convert` was used, but it doens't work with fenced_code~~
            fixed that by calling markdown.Markdown.reset before each conversion
        '''
        htmltext = self.toPlainText()
        if 'asciimathml' in self.settings.extensions:
            stuff=JSCRIPT_TPL.format(self.settings.mathjax)
        else:
            stuff=''
        return self.settings.md.reset().convert(htmltext)+stuff
        # md = markdown.Markdown(extensions)
        # return md.convert(htmltext)

    def saveAsHtml(self, htmlFile = None):
        """ Save as Complete (with css and images) or HTML Only
            To be merged with saveNoteAs
        """
        if not htmlFile:
            (htmlFile, htmlType) = QtWidgets.QFileDialog.getSaveFileNameAndFilter(
                self, self.tr("Export to HTML"), "", "Complete;;HTML Only")
        if htmlFile == '':
            return
        if not QtCore.QFileInfo(htmlFile).suffix():
            htmlFile += '.html'

        if htmlType == "Complete":
            self.saveCompleteHtml(htmlFile)
        else:
            self.saveHtmlOnly(htmlFile)

    def saveCompleteHtml(self, htmlFile):
        html = QtCore.QFile(htmlFile)
        html.open(QtCore.QIODevice.WriteOnly)
        savestream = QtCore.QTextStream(html)
        savestream.setCodec("UTF-8")
        css = QtCore.QFile(self.settings.cssfile)
        css.open(QtCore.QIODevice.ReadOnly)
        # Use a html lib may be a better idea?
        savestream << "<html><head><meta charset='utf-8'></head>"
        # Css is inlined.
        savestream << "<style>"
        cssstream = QtCore.QTextStream(css)
        cssstream.setCodec("UTF-8")
        savestream << cssstream.readAll()
        savestream << "</style>"
        # Note content
        savestream << self.toHtml()
        savestream << "</html>"
        html.close()

    def saveHtmlOnly(self, htmlFile):
        fileDir = os.path.dirname(htmlFile)
        QtCore.QDir().mkpath(fileDir)

        html = QtCore.QFile(htmlFile)
        html.open(QtCore.QIODevice.WriteOnly)
        savestream = QtCore.QTextStream(html)
        savestream.setCodec("UTF-8")
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
