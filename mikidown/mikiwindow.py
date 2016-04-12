"""
The mainwindow module.
"""
import os
import shutil
import re
from threading import Thread

from PyQt4.QtCore import (Qt, QDir, QFile, QFileInfo, QIODevice,
                          QPoint, QSize, QTextStream, QUrl)
from PyQt4.QtGui import (qApp, QAction, QCheckBox, QDesktopWidget, QDialog,
    QDockWidget, QFileDialog, QIcon, QLabel, QLineEdit, QMainWindow, QMenuBar,
    QMessageBox, QKeySequence, QPrintDialog, QPrinter, QStatusBar, QSplitter,
    QTabWidget, QTextCursor, QTextDocument, QToolBar, QTreeWidgetItem,
    QTreeWidgetItemIterator, QVBoxLayout, QWidget, QFontMetrics, QSplitter, QPlainTextEdit, QFont)
from PyQt4.QtWebKit import QWebPage, QWebView
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser, RegexPlugin
from whoosh.writing import AsyncWriter

import mikidown.mikidown_rc
from .slashpleter import SlashPleter
from .config import __appname__, __version__
from .mikibook import NotebookListDialog, NotebookSettingsDialog, Mikibook, MikidownCfgDialog
from .mikitree import MikiTree, TocTree
from .mikiedit import MikiEdit
from .mikiview import MikiView
from .mikisearch import MikiSearch
from .attachment import AttachmentView
from .highlighter import MikiHighlighter
from .findreplacedialog import FindReplaceDialog
from .utils import LineEditDialog, ViewedNoteIcon, parseHeaders, parseTitle, METADATA_CHECKER, JSCRIPT_TPL

class MikiSepNote(QDockWidget):
    #This is a static widget! It is not meant to dynamically update
    def __init__(self, settings, name, filename, plain_text=False, parent=None):
        super().__init__(parent=parent)
        splitty = QSplitter(self)
        self.setWidget(splitty)
        self.setWindowTitle(os.path.basename(name))
        self.setFloating(True)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.plain_text = plain_text
        self.notePath = settings.notePath

        fh = QFile(filename)
        try:
            if not fh.open(QIODevice.ReadOnly):
                raise IOError(fh.errorString())
        except IOError as e:
            QMessageBox.warning(self, self.tr("Read Error"),
                                self.tr("Failed to open %s: %s") % (filename, e))
        finally:
            if fh is not None:
                notestream = QTextStream(fh)
                notestream.setCodec("UTF-8")
                noteBody = notestream.readAll()
                fh.close()
                self.tocw = TocTree(self)
                splitty.addWidget(self.tocw)

                strip_math_for_header_parsing = False
                strip_fence_for_header_parsing = False

                self.tocw.itemClicked.connect(self.tocNavigate)
                if 'asciimathml' in settings.extensions:
                    stuff=JSCRIPT_TPL.format(settings.mathjax)
                    strip_math_for_header_parsing = True
                else:
                    stuff=''
                if 'fenced_code' in settings.extensions or 'extra' in settings.extensions:
                    strip_fence_for_header_parsing = True
                if plain_text:
                    note_view = QPlainTextEdit(self)
                    qfnt = QFont()
                    qfnt.setFamily('monospace')
                    note_view.setFont(qfnt)
                    note_view.setPlainText(noteBody)
                else:
                    note_view = QWebView(self)
                    note_view.setHtml(settings.md.reset().convert(noteBody)+stuff)
                    note_view.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
                    note_view.linkClicked.connect(self.linkClicked)
                    note_view.settings().setUserStyleSheetUrl( 
                     QUrl('file://'+self.parent().settings.cssfile))
                self.note_view = note_view
                splitty.addWidget(note_view)
                self.tocw.updateToc(os.path.basename(name), 
                    parseHeaders(noteBody, strip_fenced_block=strip_fence_for_header_parsing,
                        strip_ascii_math=strip_math_for_header_parsing))

    def tocNavigate(self, current):
        ''' works for notesEdit now '''
        if current is None:
            return
        pos = int(current.text(1))
        if self.plain_text:
            self.note_view.moveCursor(QTextCursor.End)
            cur = self.note_view.textCursor()
            cur.setPosition(pos, QTextCursor.MoveAnchor)
            self.note_view.setTextCursor(cur)
            # Move cursor to END first will ensure
            # header is positioned at the top of visual area.
            #self.note_view.load(QUrl(link))
        else:
            self.note_view.page().mainFrame().scrollToAnchor(current.text(2))

    def findItemByAnchor(self, anchor):
        return self.tocw.findItems(anchor, Qt.MatchExactly|Qt.MatchRecursive, column=2)

    def linkClicked(self, qurl):
        name = qurl.toString()
        http = re.compile('https?://')
        if http.match(name):                        # external uri
            QDesktopServices.openUrl(qurl)
            return

        #"""
        #self.note_view.load(qurl)
        name = name.replace('file://', '')
        name = name.replace(self.notePath, '').split('#')
        item = self.parent().notesTree.pageToItem(name[0])
        if not item or item == self.parent().notesTree.currentItem():
            return
        else:
            if self.plain_text:
                if len(name) == 2:
                    self.parent().newPlainTextNoteDisplay(item, anchor=name[1])
                else:
                    self.parent().newPlainTextNoteDisplay(item)
            else:
                if len(name) == 2:
                    self.parent().newNoteDisplay(item, anchor=name[1])
                else:
                    self.parent().newNoteDisplay(item)
        #"""

class MikiWindow(QMainWindow):
    def __init__(self, settings, parent=None):
        super(MikiWindow, self).__init__(parent)
        self.setObjectName("mikiWindow")
        self.settings = settings
        self.notePath = settings.notePath
        lockPath = os.path.join(settings.notebookPath, '.mikidown_lock')
        if not os.path.exists(lockPath):
            self.lockPathFH = os.open(lockPath, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        ################ Setup core components ################
        self.notesTree = MikiTree(self)
        self.quickNoteNav = QLineEdit()
        self.notesTab = QWidget()
        self.completer = SlashPleter()
        self.completer.setModel(self.notesTree.model())
        self.quickNoteNav.setCompleter(self.completer)
        self.notesTree.setObjectName("notesTree")
        self.initTree(self.notePath, self.notesTree)
        self.notesTree.sortItems(0, Qt.AscendingOrder)

        self.ix = None
        self.setupWhoosh()

        self.viewedList = QToolBar(self.tr('Recently Viewed'), self)
        self.viewedList.setIconSize(QSize(16, 16))
        self.viewedList.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.viewedListActions = []
        self.noteSplitter = QSplitter(Qt.Horizontal)

        self.dockIndex = QDockWidget(self.tr("Index"))
        self.dockSearch = QDockWidget(self.tr("Search"))
        self.searchEdit = QLineEdit()
        self.searchView = MikiSearch(self)
        self.searchTab = QWidget()
        self.dockToc = QDockWidget(self.tr("TOC"))
        self.tocTree = TocTree()
        self.dockAttachment = QDockWidget(self.tr("Attachment"))
        self.attachmentView = AttachmentView(self)

        self.notesEdit = MikiEdit(self)
        self.notesEdit.setObjectName(self.tr("notesEdit"))
        self.loadHighlighter()
        self.notesView = MikiView(self)

        self.findBar = QToolBar(self.tr('Find'), self)
        self.findBar.setFixedHeight(30)
        self.findEdit = QLineEdit(self.findBar)
        self.checkBox = QCheckBox(self.tr('Match case'), self.findBar)

        self.statusBar = QStatusBar(self)
        self.statusLabel = QLabel(self)

        self.altPressed = False


        ################ Setup actions ################
        self.actions = dict()
        self.setupActions()


        ################ Setup mainwindow ################
        self.setupMainWindow()

        # show changelogs after upgrade mikidown
        if self.settings.version < __version__ or Mikibook.settings.value("version", defaultValue="0") < __version__:
            self.changelogHelp()
            self.settings.qsettings.setValue("version", __version__)
            Mikibook.settings.setValue("version", __version__)


    def loadHighlighter(self):
        fnt = Mikibook.settings.value('editorFont', defaultValue=None)
        fntsize = Mikibook.settings.value('editorFontSize', type=int, defaultValue=12)
        header_scales_font = Mikibook.settings.value('headerScaleFont', type=bool, defaultValue=True)
        if fnt is not None:
            self.notesEdit.setFontFamily(fnt)
            self.notesEdit.setFontPointSize(fntsize)
        h = MikiHighlighter(parent=self.notesEdit, scale_font_sizes=header_scales_font)
        tw = Mikibook.settings.value('tabWidth', type=int, defaultValue=4)
        qfm = QFontMetrics(h.patterns[0][1].font())
        self.notesEdit.setTabStopWidth(tw * qfm.width(' '))

    def setupActions(self):

        # Global Actions
        actTabIndex = self.act(self.tr('Switch to Index Tab'),
            lambda: self.raiseDock(self.dockIndex), self.tr('Ctrl+Shift+I'))
        actTabSearch = self.act(self.tr('Switch to Search Tab'),
            lambda: self.raiseDock(self.dockSearch), self.tr('Ctrl+Shift+F'))
        self.addAction(actTabIndex)
        self.addAction(actTabSearch)

        ################ Menu Actions ################
        # actions in menuFile
        actionNewPage = self.act(self.tr('&New Page...'),
            self.notesTree.newPage, QKeySequence.New)
        self.actions.update(newPage=actionNewPage)

        actionNewSubpage = self.act(self.tr('New Sub&page...'),
            self.notesTree.newSubpage, self.tr('Ctrl+Shift+N'))
        self.actions.update(newSubpage=actionNewSubpage)

        actionImportPage = self.act(self.tr('&Import Page...'), self.importPage)
        self.actions.update(importPage=actionImportPage)

        actionNBSettings = self.act(self.tr('Notebook Set&tings...'), self.notebookSettings)
        self.actions.update(NBSettings=actionNBSettings)

        actionMDSettings = self.act(self.tr('&Mikidown Settings...'), self.mikidownSettings)
        self.actions.update(MDSettings=actionMDSettings)

        actionOpenNotebook = self.act(self.tr('&Open Notebook...'),
            self.openNotebook, QKeySequence.Open)
        self.actions.update(openNotebook=actionOpenNotebook)

        actionReIndex = self.act(self.tr('Re-index'), self.reIndex)
        self.actions.update(reIndex=actionReIndex)

        actionSave = self.act(self.tr('&Save'),
            self.saveCurrentNote, QKeySequence.Save)
        actionSave.setEnabled(False)
        self.actions.update(save=actionSave)

        actionSaveAs = self.act(self.tr('Save &As...'),
            self.saveNoteAs, QKeySequence.SaveAs)
        self.actions.update(saveAs=actionSaveAs)

        actionHtml = self.act(self.tr('to &HTML'), self.notesEdit.saveAsHtml)
        self.actions.update(html=actionHtml)

        actionPrint = self.act(self.tr('&Print'),
            self.printNote, QKeySequence.Print)
        self.actions.update(print_=actionPrint)

        actionRenamePage = self.act(self.tr('&Rename Page...'),
            self.notesTree.renamePage, 'F2')
        self.actions.update(renamePage=actionRenamePage)

        actionDelPage = self.act(self.tr('&Delete Page'),
            self.notesTree.delPageWrapper, QKeySequence.Delete)
        self.actions.update(delPage=actionDelPage)

        actionQuit = self.act(self.tr('&Quit'), self.close, QKeySequence.Quit)
        actionQuit.setMenuRole(QAction.QuitRole)
        self.actions.update(quit=actionQuit)

        # actions in menuEdit
        actionUndo = self.act(self.tr('&Undo'),
            lambda: self.notesEdit.undo(), QKeySequence.Undo)
        actionUndo.setEnabled(False)
        self.notesEdit.undoAvailable.connect(actionUndo.setEnabled)
        self.actions.update(undo=actionUndo)

        actionRedo = self.act(self.tr('&Redo'),
            lambda: self.notesEdit.redo(), QKeySequence.Redo)
        actionRedo.setEnabled(False)
        self.notesEdit.redoAvailable.connect(actionRedo.setEnabled)
        self.actions.update(redo=actionRedo)

        actionFindText = self.act(self.tr('&Find Text'),
            self.findBar.setVisible, QKeySequence.Find, True)
        self.actions.update(findText=actionFindText)

        actionFindRepl = self.act(self.tr('Find and Replace'),
                FindReplaceDialog(self.notesEdit).open, QKeySequence.Replace)
        self.actions.update(findRepl=actionFindRepl)

        actionFind = self.act(self.tr('Next'),
            self.findText, QKeySequence.FindNext)
        self.actions.update(find=actionFind)

        actionFindPrev = self.act(self.tr('Previous'),
            lambda: self.findText(back=True), QKeySequence.FindPrevious)
        self.actions.update(findPrev=actionFindPrev)

        actionSortLines = self.act(self.tr('&Sort Lines'), self.sortLines)
        self.actions.update(sortLines=actionSortLines)

        actionQuickNav = self.act(self.tr("&Quick Open Note"),
                        self.quickNoteNav.setFocus, self.tr('Ctrl+G'))
        self.addAction(actionQuickNav)

        actionInsertImage = self.act(self.tr('&Insert Attachment'),
            self.notesEdit.insertAttachmentWrapper, self.tr('Ctrl+I'))
        actionInsertImage.setEnabled(False)
        self.actions.update(insertImage=actionInsertImage)

        # actions in menuView
        QIcon.setThemeName(Mikibook.settings.value('iconTheme', QIcon.themeName()))
        #print(QIcon.themeName())
        actionEdit = self.act(self.tr('Edit'), self.edit, self.tr('Ctrl+E'),
            True, QIcon.fromTheme('document-edit'), self.tr('Edit mode (Ctrl+E)'))
        self.actions.update(edit=actionEdit)

        actionSplit = self.act(self.tr('Split'), self.liveView, self.tr('Ctrl+R'),
            True, QIcon.fromTheme('view-split-left-right'), self.tr('Split mode (Ctrl+R)'))
        self.actions.update(split=actionSplit)

        actionFlipEditAndView = self.act(self.tr('Flip Edit and View'),
            self.flipEditAndView)
        actionFlipEditAndView.setEnabled(False)
        self.actions.update(flipEditAndView=actionFlipEditAndView)

        #actionLeftAndRight = self.act(
        #    self.tr('Split into Left and Right'), trig=self.leftAndRight)
        #actionUpAndDown = self.act(
        #    self.tr('Split into Up and Down'), trig=self.upAndDown)
        # self.actionLeftAndRight.setEnabled(False)
        # self.actionUpAndDown.setEnabled(False)

        # actions in menuHelp
        actionReadme = self.act(self.tr('README'), self.readmeHelp)
        self.actions.update(readme=actionReadme)

        actionChangelog = self.act(self.tr('Changelog'), self.changelogHelp)
        self.actions.update(changelog=actionChangelog)

        actionAboutQt = self.act(self.tr('About Qt'), qApp.aboutQt)
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
        self.quickNoteNav.returnPressed.connect(self.openFuncWrapper)
        searchLayout = QVBoxLayout()
        searchLayout.addWidget(self.searchEdit)
        searchLayout.addWidget(self.searchView)
        self.searchTab.setLayout(searchLayout)

        indexLayout = QVBoxLayout(self.notesTab)
        indexLayout.addWidget(self.quickNoteNav)
        indexLayout.addWidget(self.notesTree)

        self.dockIndex.setObjectName("Index")
        self.dockIndex.setWidget(self.notesTab)
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
        menuFile.addAction(self.actions['newPage'])
        menuFile.addAction(self.actions['newSubpage'])
        menuFile.addAction(self.actions['NBSettings'])
        menuFile.addAction(self.actions['MDSettings'])
        menuFile.addAction(self.actions['importPage'])
        menuFile.addAction(self.actions['openNotebook'])
        menuFile.addAction(self.actions['reIndex'])
        menuFile.addSeparator()
        menuFile.addAction(self.actions['save'])
        menuFile.addAction(self.actions['saveAs'])
        menuFile.addAction(self.actions['print_'])
        menuExport = menuFile.addMenu(self.tr('&Export'))
        menuExport.addAction(self.actions['html'])
        menuFile.addSeparator()
        menuFile.addAction(self.actions['renamePage'])
        menuFile.addAction(self.actions['delPage'])
        menuFile.addSeparator()
        menuFile.addAction(self.actions['quit'])
        # menuEdit
        menuEdit.addAction(self.actions['undo'])
        menuEdit.addAction(self.actions['redo'])
        menuEdit.addAction(self.actions['findText'])
        menuEdit.addAction(self.actions['findRepl'])
        menuEdit.addSeparator()
        menuEdit.addAction(self.actions['sortLines'])
        menuEdit.addAction(self.actions['insertImage'])
        # menuView
        menuView.addAction(self.actions['edit'])
        menuView.addAction(self.actions['split'])
        menuView.addAction(self.actions['flipEditAndView'])
        menuShowHide = menuView.addMenu(self.tr('Show/Hide'))
        menuShowHide.addAction(self.dockIndex.toggleViewAction())
        menuShowHide.addAction(self.dockSearch.toggleViewAction())
        menuShowHide.addAction(self.dockToc.toggleViewAction())
        menuShowHide.addAction(self.dockAttachment.toggleViewAction())
        #menuMode = menuView.addMenu(self.tr('Mode'))
        #menuMode.addAction(self.actionLeftAndRight)
        #menuMode.addAction(self.actionUpAndDown)
        # menuHelp
        menuHelp.addAction(self.actions['readme'])
        menuHelp.addAction(self.actions['changelog'])
        menuHelp.addAction(self.actions['aboutQt'])

        toolBar = QToolBar(self.tr("toolbar"), self)
        toolBar.setObjectName("toolbar")       # needed in saveState()
        #toolBar.setIconSize(QSize(16, 16))
        toolBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(Qt.TopToolBarArea, toolBar)
        toolBar.addAction(self.actions['edit'])
        toolBar.addAction(self.actions['split'])
        self.findEdit.returnPressed.connect(self.findText)
        self.findBar.addWidget(self.findEdit)
        self.findBar.addWidget(self.checkBox)
        self.findBar.addAction(self.actions['findPrev'])
        self.findBar.addAction(self.actions['find'])
        self.findBar.setVisible(False)
        self.findBar.visibilityChanged.connect(self.findBarVisibilityChanged)

        self.setStatusBar(self.statusBar)
        self.statusBar.addWidget(self.statusLabel, 1)

        self.notesTree.currentItemChanged.connect(
            self.currentItemChangedWrapper)
        self.notesTree.nvwCallback = self.newNoteDisplay
        self.notesTree.nvwtCallback = self.newPlainTextNoteDisplay
        self.tocTree.itemClicked.connect(self.tocNavigate)
        self.notesEdit.textChanged.connect(self.noteEditted)

        self.notesEdit.document(
        ).modificationChanged.connect(self.modificationChanged)

        self.updateRecentViewedNotes()
        notes = self.settings.recentViewedNotes()
        if len(notes) != 0:
            item = self.notesTree.pageToItem(notes[0])
            self.notesTree.setCurrentItem(item)

    def newNoteDisplay(self, item, anchor=None):
        msn = MikiSepNote(self.settings, item.text(0), self.notesTree.itemToFile(item), plain_text=False, parent=self)
        if anchor:
            msn.note_view.page().mainFrame().scrollToAnchor(anchor)
        msn.show()

    def newPlainTextNoteDisplay(self, item, anchor=None):
        msn = MikiSepNote(self.settings, item.text(0), self.notesTree.itemToFile(item), plain_text=True, parent=self)
        if anchor:
            item = msn.findItemByAnchor(anchor)[0]
            msn.tocNavigate(item)
        msn.show()

    def openFuncWrapper(self):
        self.openFunction(self.quickNoteNav.text())()

    def setupWhoosh(self):
        # Initialize whoosh index, make sure notePath/.indexdir exists
        indexdir = self.settings.indexdir
        try:
            self.ix = open_dir(indexdir)
        except:
            QDir().mkpath(indexdir)
            self.ix = create_in(indexdir, self.settings.schema)
            # Fork a process to update index, which benefit responsiveness.
            p = Thread(target=self.whoosh_index, args=())
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
        strip_math_for_header_parsing = False
        strip_fence_for_header_parsing = False
        if 'asciimathml' in self.settings.extensions:
            strip_math_for_header_parsing = True
        if 'fenced_code' in self.settings.extensions or 'extra' in self.settings.extensions:
            strip_fence_for_header_parsing = True
        self.tocTree.updateToc(root, parseHeaders(self.notesEdit.toPlainText(), 
                        strip_fenced_block=strip_fence_for_header_parsing,
                        strip_ascii_math=strip_math_for_header_parsing))


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
            QMessageBox.warning(self, self.tr('Read Error'),
                                self.tr('Failed to open %s: %s') % (filename, e))
        finally:
            if fh is not None:
                notestream = QTextStream(fh)
                notestream.setCodec("UTF-8")
                noteBody = notestream.readAll()
                fh.close()
                self.notesEdit.setPlainText(noteBody)
                self.notesView.scrollPosition = QPoint(0, 0)
                # self.actionSave.setEnabled(False)
                self.notesEdit.document().setModified(False)
                self.notesView.updateView()
                self.setCurrentNote()
                self.updateRecentViewedNotes()
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
        if num < len(self.viewedListActions):
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
        savestream.setCodec("UTF-8")
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
        self.actions['save'].setEnabled(changed)
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
        filestream = QTextStream(fh)
        filestream.setCodec("UTF-8")
        fileBody = filestream.readAll()
        fh.close()
        page = QFileInfo(filename).completeBaseName()
        fh = QFile(self.notesTree.pageToFile(page))
        if fh.exists():
            QMessageBox.warning(self, self.tr("Import Error"),
                self.tr("Page already exists: %s") % page)
            dialog = LineEditDialog(self.notePath, self)
            if dialog.exec_():
                page = dialog.editor.text()
                fh.close()
                fh = QFile(self.notesTree.pageToFile(page))
            else:
                return
        fh.open(QIODevice.WriteOnly)
        savestream = QTextStream(fh)
        savestream.setCodec("UTF-8")
        savestream << fileBody
        fh.close()
        item = QTreeWidgetItem(self.notesTree, [page])
        self.notesTree.sortItems(0, Qt.AscendingOrder)
        self.notesTree.setCurrentItem(item)

    def openNotebook(self):
        dialog = NotebookListDialog(self)
        if dialog.exec_():
            pass

    def notebookSettings(self):
        dialog = NotebookSettingsDialog(self)
        if dialog.exec_():
            pass

    def mikidownSettings(self):
        dialog = MikidownCfgDialog(self)
        if dialog.exec_():
            pass


    def reIndex(self):
        """ Whoosh index breaks for unknown reasons (sometimes) """
        shutil.rmtree(self.settings.indexdir)
        self.setupWhoosh()

    def act(self, name, trig, shortcut=None, checkable=False,
            icon=None, tooltip=None):
        """ A wrapper to several QAction methods """
        if icon:
            action = QAction(icon, name, self)
        else:
            action = QAction(name, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.setCheckable(checkable)
        if tooltip:
            action.setToolTip(tooltip)
        action.triggered.connect(trig)
        return action

    def edit(self, viewmode):
        """ Switch between EDIT and VIEW mode. """

        if self.actions['split'].isChecked():
            self.actions['split'].setChecked(False)
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
        self.actions['insertImage'].setEnabled(viewmode)
        #self.actionLeftAndRight.setEnabled(True)
        #self.actionUpAndDown.setEnabled(True)

        # Render the note text as it is.
        self.notesView.updateView()

    def liveView(self, viewmode):
        """ Switch between VIEW and LIVE VIEW mode. """

        self.actions['split'].setChecked(viewmode)
        sizes = self.noteSplitter.sizes()
        if self.actions['edit'].isChecked():
            self.actions['edit'].setChecked(False)
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

        self.actions['flipEditAndView'].setEnabled(viewmode)
        #self.actionUpAndDown.setEnabled(viewmode)
        self.actions['insertImage'].setEnabled(viewmode)
        self.noteSplitter.setSizes(splitSize)
        self.saveCurrentNote()

        # Render the note text as it is.
        self.notesView.updateView()

    def findBarVisibilityChanged(self, visible):
        self.actions['findText'].setChecked(visible)
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
            TODO: second sort reverse the order
        '''
        cursor = self.notesEdit.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.setPosition(end, mode=QTextCursor.KeepAnchor)
        cursor.movePosition(QTextCursor.EndOfLine, mode=QTextCursor.KeepAnchor)
        text = cursor.selectedText()
        lines = text.split('\u2029')      # '\u2029' is the line break
        sortedLines = sorted(lines)
        cursor.insertText('\n'.join(sortedLines))

    def notesEditInFocus(self, e):
        if e.gotFocus:
            self.actions['insertImage'].setEnabled(True)
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
        print("Searching using", pattern)
        with self.ix.searcher() as searcher:
            matches = []
            queryp = QueryParser("content", self.ix.schema)
            #allow escaped qutoes when regex searching
            queryp.add_plugin(RegexPlugin(expr=r'r"(?P<text>[^"\\]*(\\.[^"\\]*)*)"'))
            # ~~r"pattern" is the desired regex term format~~ Don't autoforce regexing
            query = queryp.parse(pattern)
            #print("durp durp", query)
            ms = searcher.search(query, limit=None) # default limit is 10!
            for m in ms:
                #if not m in matches:
                matches.append(m)

            for r in matches:
                title = r['title']
                path = r['path']
                term = r.highlights("content")
                results.append([title, path, term])

            html = ""
            for title, path, hi in results:
                html += ("<p><a href='" + path + "'>" + title +
                         "</a><br/><span class='path'>" +
                         path + "</span><br/>" + hi + "</p>")
            self.searchView.setHtml(html)
            print("Finished searching", pattern)

    def whoosh_index(self):
        it = QTreeWidgetItemIterator(
            self.notesTree, QTreeWidgetItemIterator.All)
        print("Starting complete indexing.")
        #writer = self.ix.writer()
        writer = AsyncWriter(self.ix)
        while it.value():
            treeItem = it.value()
            name = self.notesTree.itemToPage(treeItem)
            path = os.path.join(self.notesTree.pageToFile(name)).replace(os.sep, '/')
            print(path)
            fileobj = open(path, 'r', encoding='utf-8')
            content = fileobj.read()
            fileobj.close()
            if METADATA_CHECKER.match(content) and 'meta' in self.settings.extensions:
                no_metadata_content = METADATA_CHECKER.sub("", content, count=1).lstrip()
                self.settings.md.reset().convert(content)
                writer.update_document(
                    path=name, title=parseTitle(content, name), content=no_metadata_content,
                    tags=','.join(self.settings.md.Meta.get('tags', [])).strip())
            else:
                writer.add_document(path=name, title=parseTitle(content, name), content=content, tags='')
           
            it += 1
        writer.commit()
        print("Finished completely reindexing.")

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

        recent_notes_n = Mikibook.settings.value('recentNotesNumber',type=int, defaultValue=20)
        if len(notes) > recent_notes_n:
            del notes[recent_notes_n:]
        self.settings.updateRecentViewedNotes(notes)

    def updateRecentViewedNotes(self):
        """ Switching notes will trigger this.
            When Alt pressed, show note number.
        """

        self.viewedList.clear()
        self.viewedListActions = []

        # Check notes exists.
        viewedNotes = self.settings.recentViewedNotes()
        existedNotes = []
        i = 0
        for f in viewedNotes:
            if self.notesTree.pageExists(f):
                existedNotes.append(f)
                names = f.split('/')
                if self.altPressed and i in range(1, 10):
                    action = self.act(names[-1], self.openFunction(f),
                        'Alt+'+str(i), True, ViewedNoteIcon(i), 'Alt+'+str(i))
                else:
                    action = self.act(names[-1], self.openFunction(f),
                        None, True)
                self.viewedListActions.append(action)
                i += 1

        if not self.altPressed:
            self.settings.updateRecentViewedNotes(existedNotes)
        for action in self.viewedListActions:
            self.viewedList.addAction(action)
        if len(self.viewedListActions):
            self.viewedListActions[0].setChecked(True)

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
                os.path.dirname(os.path.dirname(__file__)), 'README.mkd').replace(os.sep, '/')
        self.importPageCore(readmeFile)

    def changelogHelp(self):
        changeLog = "/usr/share/mikidown/Changelog.md"
        if not os.path.exists(changeLog):
            changeLog = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 'Changelog.md').replace(os.sep, '/')
        self.importPageCore(changeLog)

    def keyPressEvent(self, event):
        """ When Alt pressed, note number will be shown in viewedList. """
        if event.key() == Qt.Key_Alt:
            self.altPressed = True
            self.updateRecentViewedNotes()
        else:
            QMainWindow.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Alt:
            self.altPressed = False
            self.updateRecentViewedNotes()
        else:
            QMainWindow.keyPressEvent(self, event)

    def closeEvent(self, event):
        """
            saveGeometry: Saves the current geometry and state for
                          top-level widgets
            saveState: Restores the state of this mainwindow's toolbars
                       and dockwidgets
        """
        self.saveCurrentNote()
        self.ix.close()
        self.notesEdit.ix.close()
        if hasattr(self.notesTree, 'ix'):
            self.notesTree.ix.close()
        self.settings.saveGeometry(self.saveGeometry())
        self.settings.saveWindowState(self.saveState())
        event.accept()
        os.close(self.lockPathFH)
        lockPath = os.path.join(self.settings.notebookPath, '.mikidown_lock')
        os.remove(lockPath)
