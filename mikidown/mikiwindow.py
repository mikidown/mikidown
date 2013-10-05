import os
from multiprocessing import Process

import markdown
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import QWebView, QWebPage
from whoosh import sorting
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser, RegexPlugin

import mikidown.mikidown_rc
from mikidown.config import __appname__, __version__
from mikidown.mikibook import NotebookListDialog
from mikidown.mikitree import *
from mikidown.mikiedit import *
from mikidown.mikiview import *
from mikidown.mikisearch import MikiSearch
from mikidown.highlighter import MikiHighlighter
from mikidown.utils import *


class MikiWindow(QMainWindow):
    def __init__(self, settings, parent=None):
        super(MikiWindow, self).__init__(parent)
        self.settings = settings
        self.notebookPath = settings.notebookPath

        self.watcher = QFileSystemWatcher()
        self.watcher.fileChanged.connect(self.refresh)

        self.resize(800, 600)
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((
            screen.width()-size.width())/2, (screen.height()-size.height())/2)
        self.setWindowTitle(
            '{} - {}'.format(settings.notebookName, __appname__))


        self.notesTree = MikiTree(self)
        self.initTree(self.notebookPath, self.notesTree)
        self.notesTree.sortItems(0, Qt.AscendingOrder)

        # Initialize whoosh index, make sure notebookPath/.indexdir exists
        self.ix = None
        indexdir = os.path.join(self.notebookPath, settings.indexdir)
        if not QDir(indexdir).exists():
            QDir().mkdir(indexdir)
            self.ix = create_in(indexdir, settings.schema)
            # Fork a process to update index, which benefit responsiveness.
            p = Process(target=self.whoosh_index, args=())
            p.start()
        else:
            self.ix = open_dir(indexdir)
        
        self.tabWidget = QTabWidget()
        self.viewedList = QToolBar(self.tr('Recently Viewed'), self)
        self.viewedList.setFixedHeight(25)
        self.notesEdit = MikiEdit(self)
        MikiHighlighter(self.notesEdit)
        self.notesView = MikiView(self)
        self.findBar = QToolBar(self.tr('Find'), self)
        self.findBar.setFixedHeight(30)
        self.noteSplitter = QSplitter(Qt.Horizontal)
        self.noteSplitter.addWidget(self.notesEdit)
        self.noteSplitter.addWidget(self.notesView)
        self.rightSplitter = QSplitter(Qt.Vertical)
        self.rightSplitter.setChildrenCollapsible(False)
        self.rightSplitter.addWidget(self.viewedList)
        self.rightSplitter.addWidget(self.noteSplitter)
        self.rightSplitter.addWidget(self.findBar)
        self.mainSplitter = QSplitter(Qt.Horizontal)
        self.mainSplitter.addWidget(self.tabWidget)
        self.mainSplitter.addWidget(self.rightSplitter)
        #self.setCentralWidget(self.mainSplitter)
        self.setCentralWidget(self.rightSplitter)
        self.mainSplitter.setStretchFactor(0, 1)
        self.mainSplitter.setStretchFactor(1, 5)

        self.searchEdit = QLineEdit()
        self.searchEdit.returnPressed.connect(self.searchNote)
        self.searchView = MikiSearch(self)
        self.searchTab = QWidget()
        searchLayout = QVBoxLayout()
        searchLayout.addWidget(self.searchEdit)
        searchLayout.addWidget(self.searchView)
        self.searchTab.setLayout(searchLayout)
        self.tocTree = QTreeWidget()
        self.tocTree.header().close()
        self.dockIndex = QDockWidget("Index")
        self.dockIndex.setObjectName("Index")
        self.dockSearch = QDockWidget("Search")
        self.dockSearch.setObjectName("Search")
        self.dockToc = QDockWidget("TOC")
        self.dockToc.setObjectName("TOC")
        self.dockIndex.setWidget(self.notesTree)
        self.dockSearch.setWidget(self.searchTab)
        self.dockToc.setWidget(self.tocTree)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockIndex)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockSearch)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockToc)
        self.tabifyDockWidget(self.dockIndex, self.dockSearch)
        self.tabifyDockWidget(self.dockSearch, self.dockToc)
        self.setTabPosition(Qt.LeftDockWidgetArea, QTabWidget.North)
        self.dockIndex.raise_()      # Put dockIndex on top of the tab stack
        # left pane
        #self.tabWidget.addTab(self.notesTree, 'Index')
        #self.tabWidget.addTab(self.searchTab, 'Search')
        #self.tabWidget.addTab(self.tocTree, 'TOC')
        #self.tabWidget.setMinimumWidth(200)
        # self.rightSplitter.setSizes([600,20,600,580])
        self.rightSplitter.setStretchFactor(0, 0)

        # Global Actions
        actTabIndex = self.act(self.tr('Switch to Index Tab'),
                               QKeySequence('Ctrl+Shift+I'),
                               lambda: self.tabWidget.setCurrentWidget(self.notesTree))
        actTabSearch = self.act(self.tr('Switch to Search Tab'),
                                QKeySequence('Ctrl+Shift+F'),
                                lambda: self.currentTabChanged(1))
                                # lambda:self.tabWidget.setCurrentWidget(self.searchTab)
        self.addAction(actTabIndex)
        self.addAction(actTabSearch)
        
        # Shortcuts to switch notes.
        actNote1 = self.act(self.tr(""), QKeySequence("Ctrl+1"),
                            lambda: self.switchNote(1))
        actNote2 = self.act(self.tr(""), QKeySequence("Ctrl+2"),
                            lambda: self.switchNote(2))
        actNote3 = self.act(self.tr(""), QKeySequence("Ctrl+3"),
                            lambda: self.switchNote(3))
        actNote4 = self.act(self.tr(""), QKeySequence("Ctrl+4"),
                            lambda: self.switchNote(4))
        actNote5 = self.act(self.tr(""), QKeySequence("Ctrl+5"),
                            lambda: self.switchNote(5))
        actNote6 = self.act(self.tr(""), QKeySequence("Ctrl+6"),
                            lambda: self.switchNote(6))
        actNote7 = self.act(self.tr(""), QKeySequence("Ctrl+7"),
                            lambda: self.switchNote(7))
        actNote8 = self.act(self.tr(""), QKeySequence("Ctrl+8"),
                            lambda: self.switchNote(8))
        actNote9 = self.act(self.tr(""), QKeySequence("Ctrl+9"),
                            lambda: self.switchNote(9))
        self.addAction(actNote1)
        self.addAction(actNote2)
        self.addAction(actNote3)
        self.addAction(actNote4)
        self.addAction(actNote5)
        self.addAction(actNote6)
        self.addAction(actNote7)
        self.addAction(actNote8)
        self.addAction(actNote9)

        # actions in menuFile
        self.actionNewPage = self.act(
            self.tr('&New Page...'), QKeySequence.New, trig=self.notesTree.newPage)
        self.actionNewSubpage = self.act(self.tr('New Sub&page...'), QKeySequence(
            'Ctrl+Shift+N'), trig=self.notesTree.newSubpage)
        self.actionImportPage = self.act(
            self.tr('&Import Page...'), trig=self.importPage)
        self.actionOpenNotebook = self.act(
            self.tr('&Open Notebook...'), QKeySequence.Open, trig=self.openNotebook)
        self.actionSave = self.act(self.tr(
            '&Save'), QKeySequence.Save, trig=self.saveCurrentNote)
        self.actionSave.setEnabled(False)
        self.actionSaveAs = self.act(self.tr('Save &As...'), QKeySequence(
            'Ctrl+Shift+S'), trig=self.saveNoteAs)
        self.actionHtml = self.act(
            self.tr('to &HTML'), trig=self.notesEdit.saveAsHtml)
        self.actionPrint = self.act(self.tr(
            '&Print'), QKeySequence('Ctrl+P'), trig=self.printNote)
        self.actionRenamePage = self.act(self.tr(
            '&Rename Page...'), QKeySequence('F2'), trig=self.notesTree.renamePageWrapper)
        self.actionDelPage = self.act(self.tr(
            '&Delete Page'), QKeySequence('Delete'), trig=self.notesTree.delPageWrapper)
        self.actionQuit = self.act(self.tr('&Quit'), QKeySequence.Quit, SLOT('close()'))
        self.actionQuit.setMenuRole(QAction.QuitRole)
        # actions in menuEdit
        self.actionUndo = self.act(self.tr('&Undo'), QKeySequence.Undo,
                                   trig=lambda: self.notesEdit.undo())
        self.actionUndo.setEnabled(False)
        self.notesEdit.undoAvailable.connect(self.actionUndo.setEnabled)
        self.actionRedo = self.act(self.tr('&Redo'), QKeySequence.Redo,
                                   trig=lambda: self.notesEdit.redo())
        self.actionRedo.setEnabled(False)
        self.notesEdit.redoAvailable.connect(self.actionRedo.setEnabled)
        self.actionFindText = self.act(self.tr('&Find Text'), QKeySequence.Find,
            self.findBar.setVisible, True)
        self.actionFind = self.act(
            self.tr('Next'), QKeySequence.FindNext, trig=self.findText)
        self.actionFindPrev = self.act(
            self.tr('Previous'), QKeySequence.FindPrevious,
            trig=lambda: self.findText(back=True))
        self.actionSortLines = self.act(
            self.tr('&Sort Lines'), trig=self.sortLines)
        self.actionInsertImage = self.act(
            self.tr('&Insert Image'), QKeySequence('Ctrl+I'), trig=self.insertImage)
        self.actionInsertImage.setEnabled(False)

        # actions in menuView
        self.actionEdit = self.act(self.tr('Edit'), QKeySequence('Ctrl+E'),
            self.edit, True, ":/icons/edit.svg", "Edit mode (Ctrl+E)")
        self.actionSplit = self.act(self.tr('Split'), QKeySequence('Ctrl+R'),
            self.liveView, True, ":/icons/split.svg", "Split mode (Ctrl+R)")
        self.actionFlipEditAndView = self.act(
            self.tr('Flip Edit and View'), trig=self.flipEditAndView)
        self.actionFlipEditAndView.setEnabled(False)
        self.actionLeftAndRight = self.act(
            self.tr('Split into Left and Right'), trig=self.leftAndRight)
        self.actionUpAndDown = self.act(
            self.tr('Split into Up and Down'), trig=self.upAndDown)
        self.actionToggleIndex = self.act(
            self.tr('Index tab'), None, self.toggleIndex, True)
        self.actionToggleSearch = self.act(
            self.tr('Search tab'), None, self.toggleSearch, True)
        self.actionToggleToc = self.act(
            self.tr('TOC tab'), None, self.toggleToc, True)
        # self.actionLeftAndRight.setEnabled(False)
        # self.actionUpAndDown.setEnabled(False)
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
        self.menuFile.addAction(self.actionPrint)
        self.menuExport = self.menuFile.addMenu(self.tr('&Export'))
        self.menuExport.addAction(self.actionHtml)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionRenamePage)
        self.menuFile.addAction(self.actionDelPage)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        # menuEdit
        self.menuEdit.addAction(self.actionUndo)
        self.menuEdit.addAction(self.actionRedo)
        self.menuEdit.addAction(self.actionFindText)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionSortLines)
        self.menuEdit.addAction(self.actionInsertImage)
        # menuView
        self.menuView.addAction(self.actionEdit)
        self.menuView.addAction(self.actionSplit)
        self.menuView.addAction(self.actionFlipEditAndView)
        self.menuMode = self.menuView.addMenu(self.tr('Mode'))
        self.menuMode.addAction(self.actionLeftAndRight)
        self.menuMode.addAction(self.actionUpAndDown)
        self.menuPanel = self.menuView.addMenu(self.tr('Side Panel'))
        self.menuPanel.addAction(self.actionToggleIndex)
        self.menuPanel.addAction(self.actionToggleSearch)
        self.menuPanel.addAction(self.actionToggleToc)
        # menuHelp
        self.menuHelp.addAction(self.actionReadme)

        self.toolBar = QToolBar(self.tr("toolbar"), self)
        self.toolBar.setObjectName("toolbar")       # needed in saveState()
        self.toolBar.setIconSize(QSize(16, 16))
        self.toolBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(Qt.TopToolBarArea, self.toolBar)
        self.toolBar.addAction(self.actionEdit)
        self.toolBar.addAction(self.actionSplit)
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

        self.tabWidget.currentChanged.connect(self.currentTabChanged)

        self.notesTree.currentItemChanged.connect(
            self.currentItemChangedWrapper)
        self.tocTree.currentItemChanged.connect(self.tocNavigate)
        self.connect(self.notesEdit, SIGNAL('textChanged()'), self.noteEditted)

        self.notesEdit.document(
        ).modificationChanged.connect(self.modificationChanged)

        self.updateRecentViewedNotes()
        notes = self.settings.recentViewedNotes()
        if len(notes) != 0:
            item = self.notesTree.pageToItem(notes[0])
            self.notesTree.setCurrentItem(item)

    def restore(self):
        """ Restore saved geometry and state.
            Set the status of side panels in View Menu correspondently.
        """
        if self.settings.geometry:
            self.restoreGeometry(self.settings.geometry)
        if self.settings.windowstate:
            self.restoreState(self.settings.windowstate)
        self.actionToggleIndex.setChecked(
            self.dockIndex.isVisible())
        self.actionToggleSearch.setChecked(
            self.dockSearch.isVisible())
        self.actionToggleToc.setChecked(
            self.dockToc.isVisible())

    def initTree(self, notebookPath, parent):
        ''' When there exist foo.md, foo.mkd, foo.markdown, 
            only one item will be shown in notesTree.
        '''
        if not QDir(notebookPath).exists():
            return
        notebookDir = QDir(notebookPath)
        notesList = notebookDir.entryInfoList(['*.md', '*.mkd', '*.markdown'],
                                               QDir.NoFilter,
                                               QDir.Name|QDir.IgnoreCase)
        nl = [note.completeBaseName() for note in notesList]
        noduplicate = list(set(nl))
        for name in noduplicate:
            item = QTreeWidgetItem(parent, [name])
            path = notebookPath + '/' + name 
            self.initTree(path, item)

    def updateToc(self):
        ''' TOC is updated in `updateView`
            tocTree fields: [hdrText, hdrPosition, hdrAnchor]
        '''
        root = self.notesTree.currentPage()
        self.tocTree.clear()
        item = QTreeWidgetItem(self.tocTree, [root, '0'])
        curLevel = 0
        for (l, h, p, a) in parseHeaders(self.notesEdit.toPlainText()):
            ac = len(l)             # hdrLevel is the number of asterisk
            # print("curLevel: %d, ac: %d" % (curLevel, ac))
            val = [h, str(p), a]
            if ac == curLevel:
                item = QTreeWidgetItem(item.parent(), val)
            elif ac < curLevel:
                item = QTreeWidgetItem(item.parent().parent(), val)
                curLevel = ac
            else:
                item = QTreeWidgetItem(item, val)
                curLevel = ac
        self.tocTree.expandAll()

    def openFile(self, filename):
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
                self.notesView.scrollPosition = QPoint(0, 0)
                # self.actionSave.setEnabled(False)
                self.notesEdit.document().setModified(False)
                self.notesView.updateView()
                self.setCurrentNote()
                self.updateRecentViewedNotes()
                self.viewedListActions[0].setChecked(True)
                #self.statusLabel.setText(noteFullName)
                if not filename in self.watcher.files():
                    self.watcher.addPath(filename)

    def refresh(self, filepath):
        QTimer.singleShot(500, lambda: self.openFile(filepath))

    def currentTabChanged(self, index):
        self.tabWidget.setCurrentIndex(index)
        if index == 1:
            self.searchEdit.setFocus()
            self.searchEdit.selectAll()

    def currentItemChangedWrapper(self, current, previous):
        if current is None:
            return
        #if previous != None and self.notesTree.pageExists(previous):
        prev = self.notesTree.itemToPage(previous)
        if self.notesTree.pageExists(prev):
            self.saveNote(previous)
            self.watcher.removePath(self.notesTree.pageToFile(prev))

        currentFile = self.notesTree.itemToFile(current)
        self.watcher.addPath(currentFile)
        self.openFile(currentFile)

    def tocNavigate(self, current, previous):
        ''' works for notesEdit now '''
        if current is None:
            return
        pos = int(current.text(1))
        link = "file://" + self.notebookPath + "/#" + current.text(2)
        # Move cursor to END first will ensure
        # header is positioned at the top of visual area.
        self.notesEdit.moveCursor(QTextCursor.End)
        cur = self.notesEdit.textCursor()
        cur.setPosition(pos, QTextCursor.MoveAnchor)
        self.notesEdit.setTextCursor(cur)
        self.notesView.load(QUrl(link))

    def switchNote(self, num):
        self.viewedListActions[num].trigger()


    def saveCurrentNote(self):
        item = self.notesTree.currentItem()
        self.saveNote(item)

    def saveNote(self, item):
        if self.notesEdit.document().isModified():
            self.notesEdit.document().setModified(False)
        else:
            return
        pageName = item.text(0)
        filePath = os.path.join(self.notebookPath,
                                self.notesTree.itemToPage(item) + self.settings.fileExt)
        self.notesEdit.save(pageName, filePath)

    def saveNoteAs(self):
        self.saveCurrentNote()
        fileName = QFileDialog.getSaveFileName(self, self.tr('Save as'), '',
                                               '(*.md *.mkd *.markdown);;'+self.tr('All files(*)'))
        if fileName == '':
            return
        if not QFileInfo(fileName).suffix():
            fileName += '.md'
        fh = QFile(fileName)
        fh.open(QIODevice.WriteOnly)
        savestream = QTextStream(fh)
        savestream << self.notesEdit.toPlainText()
        fh.close()

    def printNote(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setCreator(__appname__ + ' ' + __version__)
        printer.setDocName(self.notesTree.currentItem().text(0))
        printdialog = QPrintDialog(printer, self)
        if printdialog.exec() == QDialog.Accepted:
            self.notesView.print_(printer)

    def noteEditted(self):
        """ Continuously get fired while editing"""
        self.updateToc()
        self.notesView.updateLiveView()

    def modificationChanged(self, changed):
        """ Fired one time: modified or not """
        self.actionSave.setEnabled(changed)
        name = self.notesTree.currentPage()
        self.statusBar.clearMessage()
        if changed:
            self.statusLabel.setText(name + '*')
        else:
            self.statusLabel.setText(name)

    def importPage(self):
        filename = QFileDialog.getOpenFileName(
            self, self.tr('Import file'), '',
            '(*.md *.mkd *.markdown *.txt);;'+self.tr('All files(*)'))
        if filename == '':
            return
        self.importPageCore(filename)

    def importPageCore(self, filename):
        fh = QFile(filename)
        fh.open(QIODevice.ReadOnly)
        fileBody = QTextStream(fh).readAll()
        fh.close()
        note = QFileInfo(filename)
        path = os.path.join(self.notebookPath, 
                            note.completeBaseName() + self.settings.fileExt)
        fh = QFile(path)
        if fh.exists():
            QMessageBox.warning(self, 'Import Error',
                                'Page already exists: %s' % note.completeBaseName())
            return
        fh.open(QIODevice.WriteOnly)
        savestream = QTextStream(fh)
        savestream << fileBody
        fh.close()
        QTreeWidgetItem(self.notesTree, [note.completeBaseName()])
        self.notesTree.sortItems(0, Qt.AscendingOrder)
        item = self.notesTree.pageToItem(note.completeBaseName())
        self.notesTree.setCurrentItem(item)

    def openNotebook(self):
        dialog = NotebookListDialog(self)
        if dialog.exec_():
            pass

    def act(self, name, shortcut=None, trig=None, checkable=False, 
            icon=None, tooltip=None):
        """ A wrapper to several QAction methods """
        if icon:
            action = QAction(QIcon(icon), name, self)
        else:
            action = QAction(name, self)
        if shortcut:
            action.setShortcut(shortcut)
        action.setCheckable(checkable)
        if tooltip:
            action.setToolTip(tooltip)
        self.connect(action, SIGNAL('triggered(bool)'), trig)
        return action

    def edit(self, viewmode):
        """ Switch between EDIT and VIEW mode. """

        if self.actionSplit.isChecked():
            self.actionSplit.setChecked(False)
        self.notesView.setVisible(not viewmode)
        self.notesEdit.setVisible(viewmode)
        
        # Gives the keyboard input focus to notesEdit/notesView.
        # Without this, keyboard input may change note text even when
        # notesEdit is invisible. 
        if viewmode:
            self.notesEdit.setFocus()
        else:
            self.notesView.setFocus()
        
        self.saveCurrentNote()
        self.actionInsertImage.setEnabled(viewmode)
        self.actionLeftAndRight.setEnabled(True)
        self.actionUpAndDown.setEnabled(True)

        # Render the note text as it is.
        self.notesView.updateView()

    def liveView(self, viewmode):
        """ Switch between VIEW and LIVE VIEW mode. """

        self.actionSplit.setChecked(viewmode)
        sizes = self.noteSplitter.sizes()
        if self.actionEdit.isChecked():
            self.actionEdit.setChecked(False)
            self.notesView.setVisible(viewmode)
            splitSize = [sizes[0]*0.45, sizes[0]*0.55]
        else:
            self.notesEdit.setVisible(viewmode)
            splitSize = [sizes[1]*0.45, sizes[1]*0.55]
        
        # setFocus for the same reason as in edit(self, viewmode)
        if viewmode:
            self.notesEdit.setFocus()
        else:
            self.notesView.setFocus()
        
        self.actionFlipEditAndView.setEnabled(viewmode)
        self.actionUpAndDown.setEnabled(viewmode)
        self.actionInsertImage.setEnabled(viewmode)
        self.noteSplitter.setSizes(splitSize)
        self.saveCurrentNote()

        # Render the note text as it is.
        self.notesView.updateView()

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
        # self.notesView.findText(text, flags)

    def findMain(self, text, flags):
        viewFlags = QWebPage.FindFlags(
            flags) | QWebPage.FindWrapsAroundDocument
        if flags:
            self.notesView.findText(text, viewFlags)
            return self.notesEdit.find(text, flags)
        else:
            self.notesView.findText(text)
            return self.notesEdit.find(text)

    def sortLines(self):
        ''' sort selected lines
            Currently, have to select whole lines. (ToFix)
            TODO: second sort reverse the order
        '''
        cursor = self.notesEdit.textCursor()
        text = cursor.selectedText()
        lines = text.split('\u2029')      # '\u2029' is the line break
        sortedLines = sorted(lines)
        self.notesEdit.insertPlainText('\n'.join(sortedLines))

    def insertImage(self):
        # TODO how to include all image types?
        filename = QFileDialog.getOpenFileName(
            self, self.tr('Insert image'), '',
            '(*.jpg *.png *.gif *.tif);;'+self.tr('All files(*)'))
        filename = '![](file://' + filename + ')'
        self.notesEdit.insertPlainText(filename)

    def notesEditInFocus(self, e):
        if e.gotFocus:
            self.actionInsertImage.setEnabled(True)
        # if e.lostFocus:
        #    self.actionInsertImage.setEnabled(False)

        # QWidget.focusInEvent(self,f)

    def searchNote(self):
        pattern = self.searchEdit.text()
        qres = []
        with self.ix.searcher() as searcher:
            queryp = QueryParser("content", self.ix.schema)
            queryp.add_plugin(RegexPlugin())
            query = queryp.parse('r"' + pattern + '"')
                                 # r"pattern" is the desired regex term format
            pathFacet = sorting.FieldFacet("path")
            scores = sorting.ScoreFacet()
            results = searcher.search(
                query, limit=None, sortedby=[pathFacet, scores])  # default limit is 10!
            for r in results:
                listItem = QListWidgetItem()
                title = r['title']
                text = r['path']
                term = r.highlights("content")
                qres.append([title, text, term])
            html = """
                    <style>
                        body { font-size: 14px; }
                        .path { font-size: 12px; color: #009933; }
                    </style>
                   """
            for ti, te, hi in qres:
                html += ("<p><a href='" + te + "'>" + ti + 
                         "</a><br/><span class='path'>" + 
                        te + "</span><br/>" + hi + "</p>")
            self.searchView.setHtml(html)

    def whoosh_index(self):
        it = QTreeWidgetItemIterator(
            self.notesTree, QTreeWidgetItemIterator.All)
        writer = self.ix.writer()
        while it.value():
            treeItem = it.value()
            name = self.notesTree.itemToPage(treeItem)
            path = os.path.join(self.notesTree.pageToFile(name))
            print(path)
            fileobj = open(path, 'r')
            content = fileobj.read()
            fileobj.close()
            writer.add_document(
                path=name, title=parseTitle(content, name), content=content)
            it += 1
        writer.commit()

    def listItemChanged(self, row):
        if row != -1:
            item = self.searchList.currentItem().data(Qt.UserRole)
            self.notesTree.setCurrentItem(item)
            flags = QWebPage.HighlightAllOccurrences
            self.notesView.findText(self.searchEdit.text(), flags)

    def setCurrentNote(self):
        item = self.notesTree.currentItem()
        name = self.notesTree.itemToPage(item)

        # Current note is inserted to head of list.
        notes = self.settings.recentViewedNotes()
        for f in notes:
            if f == name:
                notes.remove(f)
        notes.insert(0, name)

        # TODO: move this NUM to configuration
        if len(notes) > 20:
            del notes[20:]
        self.settings.updateRecentViewedNotes(notes)

    def updateRecentViewedNotes(self):
        """ Switching notes will triger this. """

        self.viewedList.clear()
        self.viewedListActions = []

        # Check notes exists.
        viewedNotes = self.settings.recentViewedNotes()
        existedNotes = []
        for f in viewedNotes:
            if self.notesTree.pageExists(f):
                existedNotes.append(f)
                splitName = f.split('/')
                self.viewedListActions.append(
                    self.act(splitName[-1], None, self.openFunction(f), True))
                
        self.settings.updateRecentViewedNotes(existedNotes)
        for action in self.viewedListActions:
            self.viewedList.addAction(action)

    def openFunction(self, name):
        item = self.notesTree.pageToItem(name)
        return lambda: self.notesTree.setCurrentItem(item)

    def toggleIndex(self, visible):
        self.actionToggleIndex.setChecked(visible)
        self.toggleTab(self.dockIndex, visible)

    def toggleSearch(self, visible):
        self.actionToggleSearch.setChecked(visible)
        self.toggleTab(self.dockSearch, visible)

    def toggleToc(self, visible):
        self.actionToggleToc.setChecked(visible)
        self.toggleTab(self.dockToc, visible)

    def toggleTab(self, tab, visible):
        if tab.isVisible():
            tab.hide()
        else:
            tab.show()

    def flipEditAndView(self):
        index = self.noteSplitter.indexOf(self.notesEdit)
        if index == 0:
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
        """
            saveGeometry: Saves the current geometry and state for 
                          top-level widgets
            saveState: Restores the state of this mainwindow's toolbars 
                       and dockwidgets 
        """
        self.saveCurrentNote()
        self.settings.saveGeometry(self.saveGeometry())
        self.settings.saveWindowState(self.saveState())
        #self.settings.setValue("geometry", self.saveGeometry())
        #self.settings.setValue("windowstate", self.saveState())
        event.accept()
