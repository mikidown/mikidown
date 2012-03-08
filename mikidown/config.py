#!/usr/bin/env python

import os
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import mikidown

__appname__ = 'mikidown'
__version__ = '0.0.1'
settings = QSettings('mikidown', 'mikidown')

def readListFromSettings(settings, key):
	if not settings.contains(key):
		return []
	value = settings.value(key)
	if isinstance(value, str):
		return [value]
	else:
		return value

def writeListToSettings(settings, key, value):
	if len(value) > 1:
		settings.setValue(key, value)
	elif len(value) == 1:
		settings.setValue(key, value[0])
	else:
		settings.remove(key)

class NotebookListDialog(QDialog):
	def __init__(self, parent=None):
		super(NotebookListDialog, self).__init__(parent)
		self.notebookList = QListWidget()
		self.moveUp = QPushButton('<<')
		self.moveDown = QPushButton('>>')
		self.add = QPushButton('Add')
		self.remove = QPushButton('Remove')
		self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok |
									 QDialogButtonBox.Cancel)
		self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
		layout = QGridLayout()
		layout.addWidget(self.notebookList, 0, 0, 4, 6)
		layout.addWidget(self.moveUp, 1, 6)
		layout.addWidget(self.moveDown, 2, 6)
		layout.addWidget(self.add, 4, 0)
		layout.addWidget(self.remove, 4, 1)
		layout.addWidget(self.buttonBox, 4, 5, 1, 2)
		self.setLayout(layout)

		self.notebookList.currentRowChanged.connect(self.updateUi)
		self.add.clicked.connect(self.actionAdd)
		self.remove.clicked.connect(self.actionRemove)
		self.moveUp.clicked.connect(self.moveItemUp)
		self.moveDown.clicked.connect(self.moveItemDown)
		self.buttonBox.accepted.connect(self.accept)
		self.buttonBox.rejected.connect(self.reject)
		self.initList()
	
	def initList(self):
		self.notebookList.clear()
		notebooks = readListFromSettings(settings, 'notebookList')
		for nb in notebooks:
			QListWidgetItem(nb, self.notebookList)

	def updateUi(self, row):
		flag = (row != -1)
		self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(flag)
		self.remove.setEnabled(flag)
		self.moveUp.setEnabled(flag)
		self.moveDown.setEnabled(flag)

	def actionAdd(self):
		NotebookList.create(settings)
		self.initList()
		count = self.notebookList.count()
		self.notebookList.setCurrentRow(count-1)
	
	def actionRemove(self):
		item = self.notebookList.currentItem()
		row = self.notebookList.currentRow()
		notebookPath = item.text()
		notebooks = readListFromSettings(settings, 'notebookList')
		notebooks.remove(notebookPath)
		writeListToSettings(settings, 'notebookList', notebooks)
		#self.notebookList.removeItemWidget(item)
		self.notebookList.takeItem(row)
		#self.initList()
		#for nb in notebooks:
		#	if nb == notebookPath:
		#		notebooks.remove(nb)
	
	def moveItemUp(self):
		item = self.notebookList.currentItem()
		row = self.notebookList.currentRow()
		if row != 0:
			#self.notebookList.removeItemWidget(item)
			self.notebookList.takeItem(row)
			self.notebookList.insertItem(row-1, item)
			self.notebookList.setCurrentRow(row-1)
	
	def moveItemDown(self):
		item = self.notebookList.currentItem()
		row = self.notebookList.currentRow()
		count = self.notebookList.count()
		if row != count-1:
			self.notebookList.takeItem(row)
			self.notebookList.insertItem(row+1, item)
			self.notebookList.setCurrentRow(row+1)

	def accept(self):
		notebookPath = self.notebookList.currentItem().text()
		window = mikidown.MikiWindow(notebookPath)
		window.show()
		count = self.notebookList.count()
		notebooks = []
		for i in range(count):
			path = self.notebookList.item(i).text()
			notebooks.append(path)
			writeListToSettings(settings, 'notebookList', notebooks)

		QDialog.accept(self)

class NewNotebookDlg(QDialog):
	def __init__(self, parent=None):
		super(NewNotebookDlg, self).__init__(parent)
		self.nameEditor = QLineEdit()
		self.nameEditor.setText('Notes')
		nameLabel = QLabel('Name:')
		nameLabel.setBuddy(self.nameEditor)
		self.pathEditor = QLineEdit()
		#self.pathEditor.setText('~/mikidown')
		self.pathEditor.setText(os.environ['HOME']+'/mikinotes')
		pathLabel = QLabel('Path:')
		pathLabel.setBuddy(self.pathEditor)
		browse = QPushButton('Browse')
		buttonBox = QDialogButtonBox(QDialogButtonBox.Ok |
										  QDialogButtonBox.Cancel)

		grid = QGridLayout()
		grid.addWidget(nameLabel, 0, 0)
		grid.addWidget(self.nameEditor, 0, 1)
		grid.addWidget(pathLabel, 1, 0)
		grid.addWidget(self.pathEditor, 1, 1)
		grid.addWidget(browse, 1, 2)
		grid.addWidget(buttonBox, 3, 2)
		self.setLayout(grid)

		self.connect(browse, SIGNAL("clicked()"),
				self.browse)
		self.connect(buttonBox, SIGNAL("accepted()"), self.accept)
		self.connect(buttonBox, SIGNAL("rejected()"), self.reject)

	def browse(self):
		default = os.environ['HOME']
		path = QFileDialog.getExistingDirectory(self, 
				"Select Folder",
				default,
				QFileDialog.ShowDirsOnly)
		self.pathEditor.setText(path)



class NotebookInfo(object):
	def __init__(self, uri, name=None):
		f = File(uri)
		self.uri = f.uri
		self.name = name or f.basename

class NotebookList():
	def __init__(self, file, default=None):
		self._file = file
		self._defaultfile = default
		self.default = None

		self.read()
	def read(self):
		if self._file.exists():
			file = self._file
		else:
			return
		lines = file.readlines()
		if len(lines) > 0:
			if lines[0].startswith('[NotebookList]'):
				self.parse(lines)
	def parse(self,text):
		assert text[0].strip() == '[NotebookList]'
		text.pop(0)


	def write(self):
		None
	
	@staticmethod
	def create(settings):
		newNotebook = NewNotebookDlg()
		if newNotebook.exec_():
			notebookName = newNotebook.nameEditor.text()
			notebookPath = newNotebook.pathEditor.text()
			if not os.path.isdir(notebookPath):
				os.makedirs(notebookPath)
			notebookList = readListFromSettings(settings, 'notebookList')
			notebookList.append(notebookPath)
			writeListToSettings(settings, 'notebookList', notebookList)


