#!/usr/bin/env python

import os
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import QWebView, QWebPage
from PyQt4.QtWebKit import QGraphicsWebView
from mikidown.mikitree import *
from mikidown.config import *

import markdown

md = markdown.Markdown()
__version__ = "0.0.1"

settings = QSettings('mikidown', 'mikidown')

class RecentChanged(QListWidget):
	def __init__(self, parent=None):
		super(RecentChanged, self).__init__(parent)

class MikiWindow(QMainWindow):
	def __init__(self, notebookPath=None, parent=None):
		super(MikiWindow, self).__init__(parent)
		self.resize(800,600)
		screen = QDesktopWidget().screenGeometry()
		size = self.geometry()
		self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)
		
		self.tabWidget = QTabWidget()
		self.viewedList = QToolBar(self.tr('Recently Viewed'), self)
		self.notesEdit = QTextEdit()
		self.notesView = QWebView()
		self.findBar = QToolBar(self.tr('Find'), self)
		self.noteSplitter = QSplitter(Qt.Horizontal)
		self.noteSplitter.addWidget(self.notesEdit)
		self.noteSplitter.addWidget(self.notesView)
		self.notesEdit.setVisible(False)
		self.notesView.settings().clearMemoryCaches()
		self.notesView.settings().setUserStyleSheetUrl(QUrl.fromLocalFile('notes.css'))
		self.rightSplitter = QSplitter(Qt.Vertical)
		self.rightSplitter.addWidget(self.viewedList)
		self.rightSplitter.addWidget(self.noteSplitter)
		self.rightSplitter.addWidget(self.findBar)
		self.mainSplitter = QSplitter(Qt.Horizontal)
		self.mainSplitter.addWidget(self.tabWidget)
		self.mainSplitter.addWidget(self.rightSplitter)
		self.setCentralWidget(self.mainSplitter)
		self.mainSplitter.setStretchFactor(0, 1)
		self.mainSplitter.setStretchFactor(1, 5)
		sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
		sizePolicy.setVerticalPolicy(QSizePolicy.Fixed)
		self.viewedList.setSizePolicy(sizePolicy)

		self.notesTree = MikiTree()
		self.changedList = RecentChanged()
		self.tabWidget.addTab(self.notesTree, 'Index')
		self.tabWidget.addTab(self.changedList, 'Recently Changed')
		#self.rightSplitter.setSizes([600,20,600,580])
		self.rightSplitter.setStretchFactor(0, 0)

		self.actionImportPage = self.act(self.tr('Import Page...'), trig=self.importPage)
		self.actionSave = self.act(self.tr('Save'), shct=QKeySequence.Save, trig=self.saveCurrentNote)
		self.actionSave.setEnabled(False)
		self.actionSaveAs = self.act(self.tr('Save As...'), shct=QKeySequence.SaveAs, trig=lambda item=self.notesEdit.isVisible(): self.saveNoteAs(item))
		self.actionQuit = self.act(self.tr('Quit'), shct=QKeySequence.Quit)
		self.connect(self.actionQuit, SIGNAL('triggered()'), self, SLOT('close()'))
		self.actionQuit.setMenuRole(QAction.QuitRole)
		self.actionUndo = self.act(self.tr('Undo'), trig=lambda: self.notesEdit.undo())
		self.actionUndo.setEnabled(False)
		self.notesEdit.undoAvailable.connect(self.actionUndo.setEnabled)
		self.menuActionFind = self.act(self.tr('Find Text'), shct=QKeySequence.Find)
		self.menuActionFind.setCheckable(True)
		self.menuActionFind.triggered.connect(self.findBar.setVisible)
		self.menuActionSearch = self.act(self.tr('Search Note...'), )
		self.findBar.visibilityChanged.connect(self.findBarVisibilityChanged)
		self.actionFind = self.act(self.tr('Next'), shct=QKeySequence.FindNext, trig=self.findText)
		self.actionFindPrev = self.act(self.tr('Previous'), shct=QKeySequence.FindPrevious, 
				trig=lambda:self.findText(back=True))
		self.actionSearch = self.act(self.tr('Search'))

		self.menuBar = QMenuBar(self)
		self.setMenuBar(self.menuBar)
		self.menuFile = self.menuBar.addMenu('File')
		self.menuEdit = self.menuBar.addMenu('Edit')
		self.menuSearch = self.menuBar.addMenu('Search')
		self.menuHelp = self.menuBar.addMenu('Help')
		self.menuFile.addAction(self.actionImportPage)
		self.menuFile.addSeparator()
		self.menuFile.addAction(self.actionSave)
		self.menuFile.addAction(self.actionSaveAs)
		self.menuFile.addSeparator()
		self.menuFile.addAction(self.actionQuit)
		self.menuEdit.addAction(self.actionUndo)
		self.menuSearch.addAction(self.menuActionFind)
		self.menuSearch.addAction(self.menuActionSearch)

		self.toolBar = QToolBar(self.tr('toolbar'), self)
		self.addToolBar(Qt.TopToolBarArea, self.toolBar)
		self.actionEdit = self.act('Edit', trigbool=self.edit)
		self.actionLiveView = self.act('Live Edit', trigbool=self.liveView)
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
		
		self.statusBar = QStatusBar(self)
		self.setStatusBar(self.statusBar)		
		
		#self.connect(self.notesTree, SIGNAL('customContextMenuRequested(QPoint)'), self.treeMenu)
		self.notesTree.currentItemChanged.connect(self.currentItemChangedWrapper)
		self.connect(self.notesEdit,
					 SIGNAL('textChanged()'),
					 self.noteEditted)

		self.notesView.page().linkHovered.connect(self.linkHovered)
		QDir.setCurrent(notebookPath)
		self.initTree(notebookPath, self.notesTree)
		self.updateRecentViewedNotes()
		files = readListFromSettings(settings, 'recentViewedNoteList')
		if len(files) != 0:
			item = self.notesTree.NameToItem(files[0])
			self.notesTree.setCurrentItem(item)

	def initTree(self, notePath, parent):
		if not QDir(notePath).exists():
			return
		noteDir = QDir(notePath)
		self.notesList = noteDir.entryInfoList(["*.markdown"],
							   QDir.NoFilter,
							   QDir.Name|QDir.IgnoreCase)
		for note in self.notesList:
			item = QTreeWidgetItem(parent, [note.baseName()])
			path = self.tr(notePath + '/' + note.baseName())
			self.initTree(path, item)
		self.editted = 0

	def openNote(self, noteFullName):
		filename = noteFullName + '.markdown'
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
				self.editted = 0
				self.actionSave.setEnabled(False)
				self.updateView()
				self.setCurrentFile()
				self.updateRecentViewedNotes()
				self.viewedListActions[-1].setChecked(True)
				self.statusBar.showMessage(noteFullName)

	def currentItemChangedWrapper(self, current, previous):
		if current is None:
			return
		self.saveNote(current, previous)
		name = self.notesTree.ItemToName(current)
		#name = self.notesTree.currentItemName()
		self.openNote(name)

	def saveCurrentNote(self):
		item = self.notesTree.currentItem()
		self.saveNote(None, item)
		name = self.notesTree.currentItemName()
		if hasattr(item, 'text'):
			self.statusBar.showMessage(name)

	def saveNote(self, current, previous):
		if previous is None:
			return
		#if self.editted == 0:
		#	return
		#self.editted = 1
		self.filename = previous.text(0)+".markdown"
		name = self.notesTree.ItemToName(previous)
		fh = QFile(name + '.markdown')
		try:
			if not fh.open(QIODevice.WriteOnly):
				raise IOError(fh.errorString())
		except IOError as e:
			QMessageBox.warning(self, "Save Error",
						"Failed to save %s: %s" % (self.filename, e))
		finally:
			if fh is not None:
				savestream = QTextStream(fh)
				savestream << self.notesEdit.toPlainText()
				fh.close()
				self.actionSave.setEnabled(False)
				self.updateView()
	
	def saveNoteAs(self, test):
		filename = QFileDialog.getSaveFileName(self, self.tr('Save as'), '',
				'(*.markdown *.mkd *.md);;'+self.tr('All files(*)'))
		if filename == '':
			return
		fh = QFile(filename)
		fh.open(QIODevice.WriteOnly)
		savestream = QTextStream(fh)
		savestream << self.notesEdit.toPlainText()
		fh.close()

	def noteEditted(self):
		self.editted = 1
		self.updateLiveView()
		name = self.notesTree.currentItemName()
		self.actionSave.setEnabled(True)
		self.statusBar.showMessage(name + '*')

	def importPage(self):
		filename = QFileDialog.getOpenFileName(self, self.tr('Import file'), '',
				'(*.markdown *.mkd *.md *.txt);;'+self.tr('All files(*)'))
		if filename == '':
			return
		fh = QFile(filename)
		fh.open(QIODevice.ReadOnly)
		fileBody = QTextStream(fh).readAll()
		fh.close()
		note = QFileInfo(filename)
		fh = QFile(note.baseName()+'.markdown')
		fh.open(QIODevice.WriteOnly)
		savestream = QTextStream(fh)
		savestream << fileBody
		fh.close()
		QTreeWidgetItem(self.notesTree, [note.baseName()])

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

	def liveView(self, viewmode):
		if self.actionEdit.isChecked():
			self.actionEdit.setChecked(False)
			self.notesView.setVisible(viewmode)
		else:
			self.notesEdit.setVisible(viewmode)
		self.updateView()

	def updateView(self):
		self.notesView.setHtml(self.parseText())

	def updateLiveView(self):
		if self.actionLiveView.isChecked():
			QTimer.singleShot(1000, self.updateView)

	def parseText(self):
		htmltext = self.notesEdit.toPlainText()
		return md.convert(htmltext)

	def linkHovered(self, link, title, textContent):
		if link == '':
			self.statusBar.showMessage(self.notesTree.currentItemName())
		else:
			self.statusBar.showMessage(link)

	def findBarVisibilityChanged(self, visible):
		self.menuActionFind.setChecked(visible)
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
	
	def setCurrentFile(self):
		noteItem = self.notesTree.currentItem()
		#name = self.notesTree.currentItemName()
		name = self.notesTree.ItemToName(noteItem)
		files = readListFromSettings(settings, 'recentViewedNoteList')
		for f in files:
			if f == name:
				files.remove(f)
		files.insert(0, name)
		if len(files) > 10:
			del files[10:]
		writeListToSettings(settings, 'recentViewedNoteList', files)
		#self.updateRecentViewedNotes()
	
	def updateRecentViewedNotes(self):
		self.viewedList.clear()
		self.viewedListActions = []
		filesOld = readListFromSettings(settings, 'recentViewedNoteList')
		files = []
		for f in reversed(filesOld):
			if self.existsNote(f):
				files.insert(0, f)
				#files.append(f)
				splitName = f.split('/')
				self.viewedListActions.append(self.act(splitName[-1], trigbool=self.openFunction(f)))
		writeListToSettings(settings, 'recentViewedNoteList', files)
		for action in self.viewedListActions:
			self.viewedList.addAction(action)
	
	def existsNote(self, noteFullname):
		filename = noteFullname + '.markdown'
		fh = QFile(filename)
		return fh.exists()

	def openFunction(self, name):
		item = self.notesTree.NameToItem(name)
		return lambda: self.notesTree.setCurrentItem(item)
	
	def closeEvent(self, event):
		reply = QMessageBox.question(self, 'Message',
				'Are you sure to quit?', 
				QMessageBox.Yes|QMessageBox.No,
				QMessageBox.No)
		if reply == QMessageBox.Yes:
			self.saveCurrentNote()
			event.accept()
		else:
			event.ignore()
			
def main():
	app = QApplication(sys.argv)
	notebooks = readListFromSettings(settings, 'notebookList')
	while len(notebooks) == 0:
		NotebookList.create(settings)
		notebooks = readListFromSettings(settings, 'notebookList')

	window = MikiWindow(notebooks[0])
	window.show()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
