#!/usr/bin/env python

import os
import re
import sys
from subprocess import call
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import QWebView, QWebPage
from mikidown.config import *
from mikidown.mikitree import *

import markdown
sys.path.append(os.path.dirname(__file__))

extensions = settings.value('extensions',['nl2br','strkundr'])
md = markdown.Markdown(extensions)

__appname__ = 'mikidown'
__version__ = '0.1.4'

class MikiWindow(QMainWindow):
    def __init__(self, notebookPath=None, name=None, parent=None):
        super(MikiWindow, self).__init__(parent)
        self.resize(800,600)
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)

        if name is not None:
            self.setWindowTitle("{} - {}".format(name, __appname__))
        else:
            self.setWindowTitle(__appname__)
        
        self.tabWidget = QTabWidget()
        self.viewedList = QToolBar(self.tr('Recently Viewed'), self)
        self.viewedList.setFixedHeight(25)
        self.notesEdit = QTextEdit()
        self.notesView = QWebView()
        
        self.findBar = QToolBar(self.tr('Find'), self)
        self.findBar.setFixedHeight(30)
        self.noteSplitter = QSplitter(Qt.Horizontal)
        self.noteSplitter.addWidget(self.notesEdit)
        self.noteSplitter.addWidget(self.notesView)
        self.notesEdit.setVisible(False)
        self.notesView.settings().clearMemoryCaches()
        self.notesView.settings().setUserStyleSheetUrl(QUrl.fromLocalFile('notes.css'))
        self.rightSplitter = QSplitter(Qt.Vertical)
        self.rightSplitter.setChildrenCollapsible(False)
        self.rightSplitter.addWidget(self.viewedList)
        self.rightSplitter.addWidget(self.noteSplitter)
        self.rightSplitter.addWidget(self.findBar)
        self.mainSplitter = QSplitter(Qt.Horizontal)
        self.mainSplitter.addWidget(self.tabWidget)
        self.mainSplitter.addWidget(self.rightSplitter)
        self.setCentralWidget(self.mainSplitter)
        self.mainSplitter.setStretchFactor(0, 1)
        self.mainSplitter.setStretchFactor(1, 5)

        self.notesTree = MikiTree()
        self.searchEdit = QLineEdit()
        self.searchEdit.returnPressed.connect(self.searchNote)
        self.searchList = QListWidget()
        self.searchTab = QWidget()
        searchLayout = QVBoxLayout()
        searchLayout.addWidget(self.searchEdit)
        searchLayout.addWidget(self.searchList)
        self.searchTab.setLayout(searchLayout)
        self.tabWidget.addTab(self.notesTree, 'Index')
        self.tabWidget.addTab(self.searchTab, 'Search')
        self.tabWidget.setMinimumWidth(150)
        #self.rightSplitter.setSizes([600,20,600,580])
        self.rightSplitter.setStretchFactor(0, 0)
        
        # actions in menuFile
        self.actionNewPage = self.act(self.tr('&New Page...'), shct=QKeySequence.New, trig=self.notesTree.newPage)
        self.actionNewSubpage = self.act(self.tr('New Sub&page...'), shct=QKeySequence('Ctrl+Shift+N'), trig=self.notesTree.newSubpage)
        self.actionImportPage = self.act(self.tr('&Import Page...'), trig=self.importPage)
        self.actionOpenNotebook = self.act(self.tr('&Open Notebook...'), shct=QKeySequence.Open, trig=self.openNotebook)
        self.actionSave = self.act(self.tr('&Save'), shct=QKeySequence.Save, trig=self.saveCurrentNote)
        self.actionSave.setEnabled(False)
        self.actionSaveAs = self.act(self.tr('Save &As...'), shct=QKeySequence('Ctrl+Shift+S'), trig=self.saveNoteAs)
        self.actionHtml = self.act(self.tr('to &HTML'), trig=self.saveNoteAsHtml)
        self.actionPdf = self.act(self.tr('to &PDF'), trig=self.saveNoteAsPdf)
        self.actionRenamePage = self.act(self.tr('&Rename Page...'), shct=QKeySequence('F2'), trig=self.notesTree.renamePageWrapper)
        self.actionDelPage = self.act(self.tr('&Delete Page'), shct=QKeySequence('Delete'), trig=self.notesTree.delPageWrapper)
        self.actionQuit = self.act(self.tr('&Quit'), shct=QKeySequence.Quit)
        self.connect(self.actionQuit, SIGNAL('triggered()'), self, SLOT('close()'))
        self.actionQuit.setMenuRole(QAction.QuitRole)
        # actions in menuEdit
        self.actionUndo = self.act(self.tr('&Undo'), shct=QKeySequence.Undo, trig=lambda: self.notesEdit.undo())
        self.actionUndo.setEnabled(False)
        self.notesEdit.undoAvailable.connect(self.actionUndo.setEnabled)
        self.actionRedo = self.act(self.tr('&Redo'), shct=QKeySequence.Redo, trig=lambda: self.notesEdit.redo())
        self.actionRedo.setEnabled(False)
        self.notesEdit.redoAvailable.connect(self.actionRedo.setEnabled)
        self.actionFindText = self.act(self.tr('&Find Text'), shct=QKeySequence.Find)
        self.actionFindText.setCheckable(True)
        self.actionFindText.triggered.connect(self.findBar.setVisible)
        self.actionFind = self.act(self.tr('Next'), shct=QKeySequence.FindNext, trig=self.findText)
        self.actionFindPrev = self.act(self.tr('Previous'), shct=QKeySequence.FindPrevious, 
                trig=lambda:self.findText(back=True))
        # actions in menuView
        self.actionEdit = self.act(self.tr('Edit'), shct=QKeySequence('Ctrl+E'), trigbool=self.edit)
        self.actionLiveView = self.act(self.tr('Live Edit'), shct=QKeySequence('Ctrl+R'), trigbool=self.liveView)
        self.actionFlipEditAndView = self.act(self.tr('Flip Edit and View'), trig=self.flipEditAndView)
        self.actionFlipEditAndView.setEnabled(False)
        self.actionLeftAndRight = self.act(self.tr('Split into Left and Right'), trig=self.leftAndRight)
        self.actionUpAndDown = self.act(self.tr('Split into Up and Down'), trig=self.upAndDown)
        #self.actionLeftAndRight.setEnabled(False)
        #self.actionUpAndDown.setEnabled(False)
        # actions in menuHelp
        self.actionReadme = self.act(self.tr('README'), trig=self.readmeHelp)

        self.menuBar = QMenuBar(self)
        self.setMenuBar(self.menuBar)
        self.menuFile = self.menuBar.addMenu(self.tr('&File'))
        self.menuEdit = self.menuBar.addMenu(self.tr('&Edit'))
        self.menuView = self.menuBar.addMenu(self.tr('&View'))
        self.menuHelp = self.menuBar.addMenu(self.tr('&Help'))
        # menuFile
        self.menuFile.addAction(self.actionNewPage)
        self.menuFile.addAction(self.actionNewSubpage)
        self.menuFile.addAction(self.actionImportPage)
        self.menuFile.addAction(self.actionOpenNotebook)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSaveAs)
        self.menuExport = self.menuFile.addMenu(self.tr('&Export'))
        self.menuExport.addAction(self.actionHtml)
        self.menuExport.addAction(self.actionPdf)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionRenamePage)
        self.menuFile.addAction(self.actionDelPage)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        # menuEdit
        self.menuEdit.addAction(self.actionUndo)
        self.menuEdit.addAction(self.actionRedo)
        self.menuEdit.addAction(self.actionFindText)
        # menuView
        self.menuView.addAction(self.actionEdit)
        self.menuView.addAction(self.actionLiveView)
        self.menuView.addAction(self.actionFlipEditAndView)
        self.menuMode = self.menuView.addMenu(self.tr('Mode'))
        self.menuMode.addAction(self.actionLeftAndRight)
        self.menuMode.addAction(self.actionUpAndDown)
        # menuHelp
        self.menuHelp.addAction(self.actionReadme)

        self.toolBar = QToolBar(self.tr('toolbar'), self)
        self.addToolBar(Qt.TopToolBarArea, self.toolBar)
        self.toolBar.addAction(self.actionEdit)
        self.toolBar.addAction(self.actionLiveView)
        self.findEdit = QLineEdit(self.findBar)
        self.findEdit.returnPressed.connect(self.findText)
        self.checkBox = QCheckBox(self.tr('Match case'), self.findBar)
        self.findBar.addWidget(self.findEdit)
        self.findBar.addWidget(self.checkBox)
        self.findBar.addAction(self.actionFindPrev)
        self.findBar.addAction(self.actionFind)
        self.findBar.setVisible(False)
        self.findBar.visibilityChanged.connect(self.findBarVisibilityChanged)
        
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)
        self.statusLabel = QLabel(self)
        self.statusBar.addWidget(self.statusLabel, 1)
        
        #self.connect(self.notesTree, SIGNAL('customContextMenuRequested(QPoint)'), self.treeMenu)
        self.notesTree.currentItemChanged.connect(self.currentItemChangedWrapper)
        self.searchList.currentRowChanged.connect(self.listItemChanged)
        self.connect(self.notesEdit, SIGNAL('textChanged()'), self.noteEditted)

        self.notesEdit.document().modificationChanged.connect(self.modificationChanged)
        self.notesView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.notesView.page().linkClicked.connect(self.linkClicked)
        self.notesView.page().linkHovered.connect(self.linkHovered)
        self.notesView.page().mainFrame().contentsSizeChanged.connect(self.contentsSizeChanged)

        self.scrollPosition = QPoint(0, 0)
        self.contentsSize = QSize(0, 0)

        QDir.setCurrent(notebookPath)
        #QSettings.setPath(QSettings.NativeFormat, QSettings.UserScope, notebookPath)
        #self.notebookSettings = QSettings('mikidown', 'notebook')
        self.notebookSettings = QSettings(os.path.join(notebookPath,
                                                    'notebook.conf'),
                                          QSettings.IniFormat)
        self.initTree(notebookPath, self.notesTree)
        self.updateRecentViewedNotes()
        self.notebookPath = notebookPath
        files = readListFromSettings(self.notebookSettings, 'recentViewedNoteList')
        if len(files) != 0:
            item = self.notesTree.pagePathToItem(files[0])
            self.notesTree.setCurrentItem(item)

    def initTree(self, notePath, parent):
        if not QDir(notePath).exists():
            return
        noteDir = QDir(notePath)
        self.notesList = noteDir.entryInfoList(['*.md'],
                               QDir.NoFilter,
                               QDir.Name|QDir.IgnoreCase)
        for note in self.notesList:
            item = QTreeWidgetItem(parent, [note.baseName()])
            path = notePath + '/' + note.baseName()
            self.initTree(path, item)
        self.editted = 0

    def openNote(self, noteFullName):
        filename = noteFullName + '.md'
        print(filename)
        fh = QFile(filename)
        try:
            if not fh.open(QIODevice.ReadOnly):
                raise IOError(fh.errorString())
        except IOError as e:
            QMessageBox.warning(self, 'Read Error', 
                    'Failed to open %s: %s' % (filename, e))
        finally:
            if fh is not None:
                noteBody = QTextStream(fh).readAll()
                fh.close()
                self.notesEdit.setPlainText(noteBody)
                #self.editted = 0
                #self.actionSave.setEnabled(False)
                self.notesEdit.document().setModified(False)
                self.updateView()
                self.setCurrentFile()
                self.updateRecentViewedNotes()
                self.viewedListActions[-1].setChecked(True)
                self.statusLabel.setText(noteFullName)
                #self.statusBar.showMessage(noteFullName)

    def currentItemChangedWrapper(self, current, previous):
        if current is None:
            return
        if self.notesTree.exists(previous):
            self.saveNote(current, previous)
        name = self.notesTree.itemToPagePath(current)
        self.openNote(name)
        #name = self.notesTree.currentItemName()

    def saveCurrentNote(self):
        item = self.notesTree.currentItem()
        self.saveNote(None, item)
        name = self.notesTree.currentItemName()
        if hasattr(item, 'text'):
            self.statusBar.showMessage(name)

    def saveNote(self, current, previous):
        if previous is None:
            return
        if self.editted == 0:
            return
        #self.editted = 1
        self.filename = previous.text(0)+'.md'
        name = self.notesTree.itemToPagePath(previous)
        fh = QFile(name + '.md')
        try:
            if not fh.open(QIODevice.WriteOnly):
                raise IOError(fh.errorString())
        except IOError as e:
            QMessageBox.warning(self, 'Save Error',
                        'Failed to save %s: %s' % (self.filename, e))
        finally:
            if fh is not None:
                savestream = QTextStream(fh)
                savestream << self.notesEdit.toPlainText()
                fh.close()
                self.notesEdit.document().setModified(False)
                #self.actionSave.setEnabled(False)
                self.updateView()
                self.editted = 0
    
    def saveNoteAs(self):
        fileName = QFileDialog.getSaveFileName(self, self.tr('Save as'), '',
                '(*.markdown *.mkd *.md);;'+self.tr('All files(*)'))
        if fileName == '':
            return
        if not QFileInfo(fileName).suffix():
            fileName += '.md'
        fh = QFile(fileName)
        fh.open(QIODevice.WriteOnly)
        savestream = QTextStream(fh)
        savestream << self.notesEdit.toPlainText()
        fh.close()

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
        savestream << self.parseText()
        fh.close()
        
    def saveNoteAsPdf(self):
        fileName = QFileDialog.getSaveFileName(self, self.tr('Export to PDF'), '',
                '(*.pdf);;'+self.tr('All files(*)'))
        if fileName == '':
            return
        if not QFileInfo(fileName).suffix():
            fileName += '.pdf'
        printer = QPrinter(QPrinter.HighResolution)
        printer.setDocName(self.notesTree.currentItem().text(0))
        printer.setCreator(__appname__ + ' ' + __version__)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(fileName)
        self.notesView.print_(printer)

    def noteEditted(self):
        self.editted = 1
        self.updateLiveView()

    def modificationChanged(self, changed):
        self.updateLiveView()
        self.actionSave.setEnabled(changed)
        name = self.notesTree.currentItemName()
        self.statusBar.clearMessage()
        if changed:
            self.editted = 1
            self.statusLabel.setText(name + '*')
        else:
            self.editted = 0
            self.statusLabel.setText(name)

    def importPage(self):
        filename = QFileDialog.getOpenFileName(self, self.tr('Import file'), '',
                '(*.markdown *.mkd *.md *.txt);;'+self.tr('All files(*)'))
        if filename == '':
            return
        self.importPageCore(filename)
            
    def importPageCore(self, filename):
        fh = QFile(filename)
        fh.open(QIODevice.ReadOnly)
        fileBody = QTextStream(fh).readAll()
        fh.close()
        note = QFileInfo(filename)
        fh = QFile(note.baseName()+'.md')
        if fh.exists():
            QMessageBox.warning(self, 'Import Error', 
                    'Page already exists: %s' % note.baseName())
            return
        fh.open(QIODevice.WriteOnly)
        savestream = QTextStream(fh)
        savestream << fileBody
        fh.close()
        QTreeWidgetItem(self.notesTree, [note.baseName()])
        self.notesTree.sortItems(0, Qt.AscendingOrder)
        item = self.notesTree.pagePathToItem(note.baseName())
        self.notesTree.setCurrentItem(item)

    def openNotebook(self):
        dialog = NotebookListDialog(self)
        if dialog.exec_():
            pass

    def act(self, name, icon=None, trig=None, trigbool=None, shct=None):
        if icon:
            action = QAction(self.actIcon(icon), name, self)
        else:
            action = QAction(name, self)
        if trig:
            self.connect(action, SIGNAL('triggered()'), trig)
        elif trigbool:
            action.setCheckable(True)
            self.connect(action, SIGNAL('triggered(bool)'), trigbool)
        if shct:
            action.setShortcut(shct)
        return action

    def edit(self, viewmode):
        if self.actionLiveView.isChecked():
            self.actionLiveView.setChecked(False)
        self.saveCurrentNote()
        self.notesView.setVisible(not viewmode)
        self.notesEdit.setVisible(viewmode)
        self.actionLeftAndRight.setEnabled(True)
        self.actionUpAndDown.setEnabled(True)

    def liveView(self, viewmode):
        self.actionLiveView.setChecked(viewmode)
        sizes = self.noteSplitter.sizes()
        if self.actionEdit.isChecked():
            self.actionEdit.setChecked(False)
            self.notesView.setVisible(viewmode)
            splitSize = [sizes[0]*0.45, sizes[0]*0.55]
        else:
            self.notesEdit.setVisible(viewmode)
            splitSize = [sizes[1]*0.45, sizes[1]*0.55]
        self.actionFlipEditAndView.setEnabled(viewmode)
        self.actionUpAndDown.setEnabled(viewmode)
        self.noteSplitter.setSizes(splitSize)
        self.saveCurrentNote()
        self.updateView()

    def updateView(self):
        viewFrame = self.notesView.page().mainFrame()
        self.scrollPosition = viewFrame.scrollPosition()
        self.contentsSize = viewFrame.contentsSize()

        noteItem = self.notesTree.currentItem()
        name = self.notesTree.itemToPagePath(noteItem)
        url_here = 'file://' + os.path.join(self.notebookPath,name)

        self.notesView.setHtml(self.parseText(), QUrl(url_here))
        viewFrame.setScrollPosition(self.scrollPosition)

    def updateLiveView(self):
        if self.actionLiveView.isChecked():
            QTimer.singleShot(1000, self.updateView)

    def contentsSizeChanged(self, newSize):
        #print('newSize: %d%d' % newSize.height, newSize.width)
        viewFrame = self.notesView.page().mainFrame()
        # scroll notesView when adding new line
        newPositionY = self.scrollPosition.y() + newSize.height() - self.contentsSize.height()
        self.scrollPosition.setY(newPositionY)
        viewFrame.setScrollPosition(self.scrollPosition)

    def parseText(self):
        htmltext = self.notesEdit.toPlainText()
        return md.convert(htmltext)

    def linkClicked(self, qlink):
        name = qlink.toString()
        p = re.compile('(https?|file)://')
        if p.match(name):
            QDesktopServices.openUrl(qlink)
        elif re.match('wiki://', name):
            item = self.notesTree.pagePathToItem(name.replace('wiki://',''))
            self.notesTree.setCurrentItem(item)

    def linkHovered(self, link, title, textContent):
        if link == '':
            self.statusBar.showMessage(self.notesTree.currentItemName())
        else:
            self.statusBar.showMessage(link)

    def findBarVisibilityChanged(self, visible):
        self.actionFindText.setChecked(visible)
        if visible:
            self.findEdit.setFocus(Qt.ShortcutFocusReason)

    def findText(self, back=False):
        flags = 0
        if back:
            flags = QTextDocument.FindBackward
        if self.checkBox.isChecked():
            flags = flags | QTextDocument.FindCaseSensitively
        text = self.findEdit.text()
        if not self.findMain(text, flags):
            if text in self.notesEdit.toPlainText():
                cursor = self.notesEdit.textCursor()
                if back:
                    cursor.movePosition(QTextCursor.End)
                else:
                    cursor.movePosition(QTextCursor.Start)
                self.notesEdit.setTextCursor(cursor)
                self.findMain(text, flags)
        #self.notesView.findText(text, flags)

    def findMain(self, text, flags):
        viewFlags = QWebPage.FindFlags(flags) | QWebPage.FindWrapsAroundDocument
        if flags:
            self.notesView.findText(text, viewFlags)
            return self.notesEdit.find(text, flags)
        else:
            self.notesView.findText(text)           
            return self.notesEdit.find(text)

    def containWords(self, item, pattern):
        if not pattern:
            return True
        pagePath = self.notesTree.itemToPagePath(item)
        pageFile = pagePath + '.md'
        # not sure this is safe
        cmd = ['grep', '-i', pattern, pageFile]
        # grep return 0 when pattern found
        return not call(cmd, stdout=None, shell=True)

    def searchNote(self):
        self.searchList.clear()
        it = QTreeWidgetItemIterator(self.notesTree, QTreeWidgetItemIterator.All)
        while it.value():
            treeItem = it.value()
            pattern = self.searchEdit.text()
            if self.containWords(treeItem, pattern):
                listItem = QListWidgetItem()
                listItem.setData(Qt.DisplayRole, treeItem.text(0))
                listItem.setData(Qt.UserRole, treeItem)
                self.searchList.addItem(listItem)
            it += 1

    def listItemChanged(self, row):
        if row != -1:
            item = self.searchList.currentItem().data(Qt.UserRole)
            self.notesTree.setCurrentItem(item)
            flags = QWebPage.HighlightAllOccurrences
            self.notesView.findText(self.searchEdit.text(), flags)

    def setCurrentFile(self):
        noteItem = self.notesTree.currentItem()
        #name = self.notesTree.currentItemName()
        name = self.notesTree.itemToPagePath(noteItem)
        files = readListFromSettings(self.notebookSettings, 'recentViewedNoteList')
        for f in files:
            if f == name:
                files.remove(f)
        files.insert(0, name)
        if len(files) > 10:
            del files[10:]
        writeListToSettings(self.notebookSettings, 'recentViewedNoteList', files)
        #self.updateRecentViewedNotes()
    
    def updateRecentViewedNotes(self):
        self.viewedList.clear()
        self.viewedListActions = []
        filesOld = readListFromSettings(self.notebookSettings, 'recentViewedNoteList')
        files = []
        for f in reversed(filesOld):
            if self.existsNote(f):
                files.insert(0, f)
                #files.append(f)
                splitName = f.split('/')
                self.viewedListActions.append(self.act(splitName[-1], trigbool=self.openFunction(f)))
        writeListToSettings(self.notebookSettings, 'recentViewedNoteList', files)
        for action in self.viewedListActions:
            self.viewedList.addAction(action)
    
    def existsNote(self, noteFullname):
        filename = noteFullname + '.md'
        fh = QFile(filename)
        return fh.exists()

    def openFunction(self, name):
        item = self.notesTree.pagePathToItem(name)
        return lambda: self.notesTree.setCurrentItem(item)
    
    def flipEditAndView(self):
        index = self.noteSplitter.indexOf(self.notesEdit)
        if index ==  0:
            self.noteSplitter.insertWidget(1, self.notesEdit)
        else:
            self.noteSplitter.insertWidget(0, self.notesEdit)

    def leftAndRight(self):
        self.liveView(True)
        self.noteSplitter.setOrientation(Qt.Horizontal)
        self.actionLeftAndRight.setEnabled(False)
        self.actionUpAndDown.setEnabled(True)

    def upAndDown(self):
        self.liveView(True)
        self.noteSplitter.setOrientation(Qt.Vertical)
        self.actionUpAndDown.setEnabled(False)
        self.actionLeftAndRight.setEnabled(True)

    def readmeHelp(self):
        readmeFile = '/usr/share/mikidown/README.mkd'
        self.importPageCore(readmeFile)

    def closeEvent(self, event):
        self.saveCurrentNote()
        event.accept()
        '''
        reply = QMessageBox.question(self, 'Message',
                'Are you sure to quit?', 
                QMessageBox.Yes|QMessageBox.No,
                QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.saveCurrentNote()
            event.accept()
        else:
            event.ignore()
        '''

def main():
    app = QApplication(sys.argv)
    notebooks = readListFromSettings(settings, 'notebookList')
    if len(notebooks) == 0:
        NotebookList.create(settings)
        notebooks = readListFromSettings(settings, 'notebookList')
    if len(notebooks) == 0:
        return
    window = MikiWindow(notebookPath=notebooks[0][1], 
        name=notebooks[0][0])
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
