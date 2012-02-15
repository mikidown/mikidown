#!/usr/bin/env python

import os
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class NewNotebookDlg(QDialog):
	def __init__(self, parent=None):

		super(NewNotebookDlg, self).__init__(parent)
		self.nameEditor = QLineEdit()
		self.nameEditor.setText('Notes')
		nameLabel = QLabel('Name:')
		nameLabel.setBuddy(self.nameEditor)
		self.pathEditor = QLineEdit()
		#self.pathEditor.setText('~/mikidown')
		self.pathEditor.setText(os.environ['HOME']+'/mikidown')
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
		#default = "~/Notebooks/Notes/"
		#default = QDesktopServices.storageLocation(QDesktopServices.HomeLocation)
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
	def create():
		XDG_CONFIG_HOME = os.environ['XDG_CONFIG_HOME']
		filename = XDG_CONFIG_HOME + '/mikidown/notebooks.list'
		newNotebook = NewNotebookDlg()
		if newNotebook.exec_():
			fh = QFile(filename)
			fh.open(QIODevice.WriteOnly)
			savestream = QTextStream(fh)
			savestream << newNotebook.nameEditor.text()
			savestream <<  ' '
			savestream << newNotebook.pathEditor.text()
			fh.close()
			None


