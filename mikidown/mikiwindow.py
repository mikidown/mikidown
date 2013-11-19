"""
The mainwindow module.
"""
import os
from multiprocessing import Process

from PyQt4.QtCore import (Qt, QDir, QFile, QFileInfo, QIODevice,
                          QPoint, QSize, QTextStream, QUrl)
from PyQt4.QtGui import (qApp, QAction, QCheckBox, QDesktopWidget, QDialog,
    QDockWidget, QFileDialog, QIcon, QLabel, QLineEdit, QMainWindow, QMenuBar,
    QMessageBox, QKeySequence, QPrintDialog, QPrinter, QStatusBar, QSplitter,
    QTabWidget, QTextCursor, QTextDocument, QToolBar, QTreeWidgetItem,
    QTreeWidgetItemIterator, QVBoxLayout, QWidget)
from PyQt4.QtWebKit import QWebPage
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser, RegexPlugin

import mikidown.mikidown_rc
from .config import __appname__, __version__
from .mikibook import NotebookListDialog
from .mikitree import MikiTree, TocTree
from .mikiedit import MikiEdit
from .mikiview import MikiView
from .mikisearch import MikiSearch
from .attachment import AttachmentView
from .highlighter import MikiHighlighter
from .utils import parseHeaders, parseTitle


class MikiWindow(QMainWindow):
    def __init__(self, settings, parent=None):
        super(MikiWindow, self).__init__(parent)
        self.settings = settings
        self.notePath = settings.notePath

        ################ Setup core components ################
        self.notesTree = MikiTree(self)
        self.notesTree.setObjectName("notesTree")
        self.initTree(self.notePath, self.notesTree)
        self.notesTree.sortItems(0, Qt.AscendingOrder)

        self.ix = None
        self.setupWhoosh()

        self.viewedList = QToolBar(self.tr('Recently Viewed'), self)
        self.viewedListActions = []
        self.noteSplitter = QSplitter(Qt.Horizontal)

        self.dockIndex = QDockWidget("Index")
        self.dockSearch = QDockWidget("Search")
        self.searchEdit = QLineEdit()
        self.searchView = MikiSearch(self)
        self.searchTab = QWidget()
        self.dockToc = QDockWidget("TOC")
        self.tocTree = TocTree()
        self.dockAttachment = QDockWidget("Attachment")
        self.attachmentView = AttachmentView(self)

        self.notesEdit = MikiEdit(self)
        self.notesEdit.setObjectName("notesEdit")
        MikiHighlighter(self.notesEdit)
        self.notesView = MikiView(self)

        self.findBar = QToolBar(self.tr('Find'), self)
        self.findBar.setFixedHeight(30)
        self.findEdit = QLineEdit(self.findBar)
        self.checkBox = QCheckBox(self.tr('Match case'), self.findBar)

        self.statusBar = QStatusBar(self)
        self.statusLabel = QLabel(self)


        ################ Setup actions ################
        self.actions = dict()
        self.setupActions()


        ################ Setup mainwindow ################
        self.setupMainWindow()

        # show changelogs after upgrade mikidown
        if self.settings.version < __version__:
            self.changelogHelp()
            self.settings.qsettings.setValue("version", __version__)


    def setupActions(self):

        # Global Actions
        actTabIndex = self.act(self.tr('Switch to Index Tab'),
                               QKeySequence('Ctrl+Shift+I'),
                               lambda: self.raiseDock(self.dockIndex))
        actTabSearch = self.act(self.tr('Switch to Search Tab'),
                                QKeySequence('Ctrl+Shift+F'),
                               lambda: self.raiseDock(self.dockSearch))
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

        ################ Menu Actions ################
        # actions in menuFile
        actionNewPage = self.act(self.tr('&New Page...'),
            QKeySequence.New, trig=self.notesTree.newPage)
        self.actions.update(newPage=actionNewPage)

        actionNewSubpage = self.act(self.tr('New Sub&page...'),
            QKeySequence('Ctrl+Shift+N'), trig=self.notesTree.newSubpage)
        self.actions.update(newSubPage=actionNewSubpage)

        actionImportPage = self.act(
            self.tr('&Import Page...'), trig=self.importPage)
        self.actions.update(importPage=actionImportPage)

        actionOpenNotebook = self.act(
            self.tr('&Open Notebook...'), QKeySequence.Open, self.openNotebook)
        self.actions.update(openNotebook=actionOpenNotebook)

        actionSave = self.act(self.tr(
            '&Save'), QKeySequence.Save, trig=self.saveCurrentNote)
        actionSave.setEnabled(False)
        self.actions.update(save=actionSave)

        actionSaveAs = self.act(self.tr('Save &As...'), QKeySequence(
            'Ctrl+Shift+S'), trig=self.saveNoteAs)
        self.actions.update(saveAs=actionSaveAs)

        actionHtml = self.act(
            self.tr('to &HTML'), trig=self.notesEdit.saveAsHtml)
        self.actions.update(html=actionHtml)

        actionPrint = self.act(self.tr(
            '&Print'), QKeySequence('Ctrl+P'), trig=self.printNote)
        self.actions.update(print_=actionPrint)

        actionRenamePage = self.act(self.tr('&Rename Page...'),
            QKeySequence('F2'), trig=self.notesTree.renamePage)
        self.actions.update(renamePage=actionRenamePage)

        actionDelPage = self.act(self.tr('&Delete Page'),
            QKeySequence('Delete'), trig=self.notesTree.delPageWrapper)
        self.actions.update(delPage=actionDelPage)

        actionQuit = self.act(
            self.tr('&Quit'), QKeySequence.Quit, self.close)
        actionQuit.setMenuRole(QAction.QuitRole)
        self.actions.update(quit=actionQuit)

        # actions in menuEdit
        actionUndo = self.act(self.tr('&Undo'), QKeySequence.Undo,
                                   trig=lambda: self.notesEdit.undo())
        actionUndo.setEnabled(False)
        self.notesEdit.undoAvailable.connect(actionUndo.setEnabled)
        self.actions.update(undo=actionUndo)

        actionRedo = self.act(self.tr('&Redo'), QKeySequence.Redo,
                                   trig=lambda: self.notesEdit.redo())
        actionRedo.setEnabled(False)
        self.notesEdit.redoAvailable.connect(actionRedo.setEnabled)
        self.actions.update(redo=actionRedo)

        actionFindText = self.act(self.tr('&Find Text'), QKeySequence.Find,
            self.findBar.setVisible, True)
        self.actions.update(findText=actionFindText)

        actionFind = self.act(
            self.tr('Next'), QKeySequence.FindNext, trig=self.findText)
        self.actions.update(find=actionFind)

        actionFindPrev = self.act(
            self.tr('Previous'), QKeySequence.FindPrevious,
            trig=lambda: self.findText(back=True))
        self.actions.update(findPrev=actionFindPrev)

        actionSortLines = self.act(
            self.tr('&Sort Lines'), trig=self.sortLines)
        self.actions.update(sortLines=actionSortLines)

        actionInsertImage = self.act(self.tr('&Insert Attachment'),
            QKeySequence('Ctrl+I'), self.notesEdit.insertAttachmentWrapper)
        actionInsertImage.setEnabled(False)
        self.actions.update(insertImage=actionInsertImage)

        # actions in menuView
        actionEdit = self.act(self.tr('Edit'), QKeySequence('Ctrl+E'),
            self.edit, True, ":/icons/edit.svg", "Edit mode (Ctrl+E)")
        self.actions.update(edit=actionEdit)

        actionSplit = self.act(self.tr('Split'), QKeySequence('Ctrl+R'),
            self.liveView, True, ":/icons/split.svg", "Split mode (Ctrl+R)")
        self.actions.update(split=actionSplit)

        actionFlipEditAndView = self.act(
            self.tr('Flip Edit and View'), trig=self.flipEditAndView)
        actionFlipEditAndView.setEnabled(False)
        self.actions.update(flipEditAndView=actionFlipEditAndView)

        #actionLeftAndRight = self.act(
        #    self.tr('Split into Left and Right'), trig=self.leftAndRight)
        #actionUpAndDown = self.act(
        #    self.tr('Split into Up and Down'), trig=self.upAndDown)
        # self.actionLeftAndRight.setEnabled(False)
        # self.actionUpAndDown.setEnabled(False)

        # actions in menuHelp
        actionReadme = self.act(self.tr('README'), trig=self.readmeHelp)
        self.actions.update(readme=actionReadme)

        actionChangelog = self.act(self.tr('Changelog'),
            trig=self.changelogHelp)
        self.actions.update(changelog=actionChangelog)

        #actionAboutQt = QAction(self.tr('About Qt'), self)
        #actionAboutQt.triggered.connect(qApp.aboutQt)
        actionAboutQt = self.act(self.tr('About Qt'), trig=qApp.aboutQt)
        self.actions.update(aboutQt=actionAboutQt)


    def setupMainWindow(self):
        self.resize(800, 600)
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((
            screen.width()-size.width())/2, (screen.height()-size.height())/2)
        self.setWindowTitle(
            '{} - {}'.format(self.settings.notebookName, __appname__))

        self.viewedList.setFixedHeight(25)
        self.noteSplitter.addWidget(self.notesEdit)
        self.noteSplitter.addWidget(self.notesView)
        mainSplitter = QSplitter(Qt.Vertical)
        mainSplitter.setChildrenCollapsible(False)
        mainSplitter.addWidget(self.viewedList)
        mainSplitter.addWidget(self.noteSplitter)
        mainSplitter.addWidget(self.findBar)
        self.setCentralWidget(mainSplitter)

        self.searchEdit.returnPressed.connect(self.searchNote)
        searchLayout = QVBoxLayout()
        searchLayout.addWidget(self.searchEdit)
        searchLayout.addWidget(self.searchView)
        self.searchTab.setLayout(searchLayout)
        self.tocTree.header().close()

        self.dockIndex.setObjectName("Index")
        self.dockIndex.setWidget(self.notesTree)
        self.dockSearch.setObjectName("Search")
        self.dockSearch.setWidget(self.searchTab)
        self.dockToc.setObjectName("TOC")
        self.dockToc.setWidget(self.tocTree)
        self.dockAttachment.setObjectName("Attachment")
        self.dockAttachment.setWidget(self.attachmentView)

        self.setDockOptions(QMainWindow.VerticalTabs)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockIndex)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockSearch)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockToc)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockAttachment)
        self.tabifyDockWidget(self.dockIndex, self.dockSearch)
        self.tabifyDockWidget(self.dockSearch, self.dockToc)
        self.tabifyDockWidget(self.dockToc, self.dockAttachment)
        self.setTabPosition(Qt.LeftDockWidgetArea, QTabWidget.North)
        self.dockIndex.raise_()      # Put dockIndex on top of the tab stack

        menuBar = QMenuBar(self)
        self.setMenuBar(menuBar)
        menuFile = menuBar.addMenu(self.tr('&File'))
        menuEdit = menuBar.addMenu(self.tr('&Edit'))
        menuView = menuBar.addMenu(self.tr('&View'))
        menuHelp = menuBar.addMenu(self.tr('&Help'))
        # menuFile
        menuFile.addAction(self.actions.get('newPage'))
        menuFile.addAction(self.actions.get('newSubpage'))
        menuFile.addAction(self.actions.get('importPage'))
        menuFile.addAction(self.actions.get('openNotebook'))
        menuFile.addSeparator()
        menuFile.addAction(self.actions.get('save'))
        menuFile.addAction(self.actions.get('saveAs'))
        menuFile.addAction(self.actions.get('print_'))
        menuExport = menuFile.addMenu(self.tr('&Export'))
        menuExport.addAction(self.actions.get('html'))
        menuFile.addSeparator()
        menuFile.addAction(self.actions.get('renamePage'))
        menuFile.addAction(self.actions.get('delPage'))
        menuFile.addSeparator()
        menuFile.addAction(self.actions.get('quit'))
        # menuEdit
        menuEdit.addAction(self.actions.get('undo'))
        menuEdit.addAction(self.actions.get('redo'))
        menuEdit.addAction(self.actions.get('findText'))
        menuEdit.addSeparator()
        menuEdit.addAction(self.actions.get('sortLines'))
        menuEdit.addAction(self.actions.get('insertImage'))
        # menuView
        menuView.addAction(self.actions.get('edit'))
        menuView.addAction(self.actions.get('split'))
        menuView.addAction(self.actions.get('flipEditAndView'))
        menuShowHide = menuView.addMenu(self.tr('Show/Hide'))
        menuShowHide.addAction(self.dockIndex.toggleViewAction())
        menuShowHide.addAction(self.dockSearch.toggleViewAction())
        menuShowHide.addAction(self.dockToc.toggleViewAction())
        menuShowHide.addAction(self.dockAttachment.toggleViewAction())
        #menuMode = menuView.addMenu(self.tr('Mode'))
        #menuMode.addAction(self.actionLeftAndRight)
        #menuMode.addAction(self.actionUpAndDown)
        # menuHelp
        menuHelp.addAction(self.actions.get('readme'))
        menuHelp.addAction(self.actions.get('changelog'))
        menuHelp.addAction(self.actions.get('AboutQt'))

        toolBar = QToolBar(self.tr("toolbar"), self)
        toolBar.setObjectName("toolbar")       # needed in saveState()
        toolBar.setIconSize(QSize(16, 16))
        toolBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(Qt.TopToolBarArea, toolBar)
        toolBar.addAction(self.actions.get('edit'))
        toolBar.addAction(self.actions.get('split'))
        self.findEdit.returnPressed.connect(self.findText)
        self.findBar.addWidget(self.findEdit)
        self.findBar.addWidget(self.checkBox)
        self.findBar.addAction(self.actions.get('findPrev'))
        self.findBar.addAction(self.actions.get('find'))
        self.findBar.setVisible(False)
        self.findBar.visibilityChanged.connect(self.findBarVisibilityChanged)

        self.setStatusBar(self.statusBar)
        self.statusBar.addWidget(self.statusLabel, 1)

        self.notesTree.currentItemChanged.connect(
            self.currentItemChangedWrapper)
        self.tocTree.itemClicked.connect(self.tocNavigate)
        self.notesEdit.textChanged.connect(self.noteEditted)

        self.notesEdit.document(
        ).modificationChanged.connect(self.modificationChanged)

        self.updateRecentViewedNotes()
        notes = self.settings.recentViewedNotes()
        if len(notes) != 0:
            item = self.notesTree.pageToItem(notes[0])
            self.notesTree.setCurrentItem(item)

    def setupWhoosh(self):
        # Initialize whoosh index, make sure notePath/.indexdir exists
        indexdir = self.settings.indexdir
        try:
            self.ix = open_dir(indexdir)
        except:
            QDir().mkpath(indexdir)
            self.ix = create_in(indexdir, self.settings.schema)
            # Fork a process to update index, which benefit responsiveness.
            p = Process(target=self.whoosh_index, args=())
            p.start()


    def restore(self):
        """ Restore saved geometry and state.
            Set the status of side panels in View Menu correspondently.
        """
        if self.settings.geometry:
            self.restoreGeometry(self.settings.geometry)
        if self.settings.windowstate:
            self.restoreState(self.settings.windowstate)

    def initTree(self, notePath, parent):
        ''' When there exist foo.md, foo.mkd, foo.markdown,
            only one item will be shown in notesTree.
        '''
        if not QDir(notePath).exists():
            return
        notebookDir = QDir(notePath)
        notesList = notebookDir.entryInfoList(['*.md', '*.mkd', '*.markdown'],
                                               QDir.NoFilter,
                                               QDir.Name|QDir.IgnoreCase)
        nl = [note.completeBaseName() for note in notesList]
        noduplicate = list(set(nl))
        for name in noduplicate:
            item = QTreeWidgetItem(parent, [name])
            path = notePath + '/' + name
            self.initTree(path, item)

    def updateToc(self):
        ''' TOC is updated in `updateView`
            tocTree fields: [hdrText, hdrPosition, hdrAnchor]
        '''
        root = self.notesTree.currentPage()
        self.tocTree.clear()
        item = QTreeWidgetItem(self.tocTree, [root, '0'])
        curLevel = 0
        for (level, h, p, a) in parseHeaders(self.notesEdit.toPlainText()):
            val = [h, str(p), a]
            if level == curLevel:
                item = QTreeWidgetItem(item.parent(), val)
            elif level < curLevel:
                item = QTreeWidgetItem(item.parent().parent(), val)
                curLevel = level
            else:
                item = QTreeWidgetItem(item, val)
                curLevel = level
        self.tocTree.expandAll()

    def updateAttachmentView(self):
        # Update attachmentView to show corresponding attachments.
        item = self.notesTree.currentItem()
        index = self.attachmentView.model.index(
            self.notesTree.itemToAttachmentDir(item))
        self.attachmentView.setRootIndex(index)

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

    def currentItemChangedWrapper(self, current, previous):
        if current is None:
            return
        #if previous != None and self.notesTree.pageExists(previous):
        prev = self.notesTree.itemToPage(previous)
        if self.notesTree.pageExists(prev):
            self.saveNote(previous)

        currentFile = self.notesTree.itemToFile(current)
        self.openFile(currentFile)

        # Update attachmentView to show corresponding attachments.
        index = self.attachmentView.model.index(
            self.notesTree.itemToAttachmentDir(current))
        self.attachmentView.setRootIndex(index)

    def tocNavigate(self, current):
        ''' works for notesEdit now '''
        if current is None:
            return
        pos = int(current.text(1))
        link = "file://" + self.notePath + "/#" + current.text(2)
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
        self.notesEdit.save(item)

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
        self.actions.get('save').setEnabled(changed)
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
        path = os.path.join(self.notePath,
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
        action.triggered.connect(trig)
        return action

    def edit(self, viewmode):
        """ Switch between EDIT and VIEW mode. """

        if self.actions.get('split').isChecked():
            self.actions.get('split').setChecked(False)
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
        self.actions.get('insertImage').setEnabled(viewmode)
        #self.actionLeftAndRight.setEnabled(True)
        #self.actionUpAndDown.setEnabled(True)

        # Render the note text as it is.
        self.notesView.updateView()

    def liveView(self, viewmode):
        """ Switch between VIEW and LIVE VIEW mode. """

        self.actions.get('split').setChecked(viewmode)
        sizes = self.noteSplitter.sizes()
        if self.actions.get('edit').isChecked():
            self.actions.get('edit').setChecked(False)
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

        self.actions.get('flipEditAndView').setEnabled(viewmode)
        #self.actionUpAndDown.setEnabled(viewmode)
        self.actions.get('insertImage').setEnabled(viewmode)
        self.noteSplitter.setSizes(splitSize)
        self.saveCurrentNote()

        # Render the note text as it is.
        self.notesView.updateView()

    def findBarVisibilityChanged(self, visible):
        self.actions.get('findText').setChecked(visible)
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

    def notesEditInFocus(self, e):
        if e.gotFocus:
            self.actions.get('insertImage').setEnabled(True)
        # if e.lostFocus:
        #    self.actionInsertImage.setEnabled(False)

        # QWidget.focusInEvent(self,f)

    def searchNote(self):
        """ Sorting criteria: "title > path > content"
            Search matches are organized into html source.
        """

        pattern = self.searchEdit.text()
        if not pattern:
            return
        results = []

        with self.ix.searcher() as searcher:
            matches = []
            for f in ["title", "path", "content"]:
                queryp = QueryParser(f, self.ix.schema)
                queryp.add_plugin(RegexPlugin())
                # r"pattern" is the desired regex term format
                query = queryp.parse('r"' + pattern + '"')
                ms = searcher.search(query, limit=None) # default limit is 10!
                for m in ms:
                    if not m in matches:
                        matches.append(m)

            for r in matches:
                title = r['title']
                path = r['path']
                term = r.highlights("content")
                results.append([title, path, term])

            html = """
                    <style>
                        body { font-size: 14px; }
                        .path { font-size: 12px; color: #009933; }
                    </style>
                   """
            for title, path, hi in results:
                html += ("<p><a href='" + path + "'>" + title +
                         "</a><br/><span class='path'>" +
                         path + "</span><br/>" + hi + "</p>")
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

    def raiseDock(self, widget):
        if not widget.isVisible():
            widget.show()
        if widget == self.dockSearch:
            self.searchEdit.setFocus()
        widget.raise_()

    def flipEditAndView(self):
        index = self.noteSplitter.indexOf(self.notesEdit)
        if index == 0:
            self.noteSplitter.insertWidget(1, self.notesEdit)
        else:
            self.noteSplitter.insertWidget(0, self.notesEdit)

    def leftAndRight(self):
        self.liveView(True)
        self.noteSplitter.setOrientation(Qt.Horizontal)
        #self.actionLeftAndRight.setEnabled(False)
        #self.actionUpAndDown.setEnabled(True)

    def upAndDown(self):
        self.liveView(True)
        self.noteSplitter.setOrientation(Qt.Vertical)
        #self.actionUpAndDown.setEnabled(False)
        #self.actionLeftAndRight.setEnabled(True)

    def readmeHelp(self):
        readmeFile = '/usr/share/mikidown/README.mkd'
        if not os.path.exists(readmeFile):
            readmeFile = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 'README.mkd')
        self.importPageCore(readmeFile)

    def changelogHelp(self):
        changeLog = "/usr/share/mikidown/Changelog.md"
        if not os.path.exists(changeLog):
            changeLog = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 'Changelog.md')
        self.importPageCore(changeLog)

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
        event.accept()
