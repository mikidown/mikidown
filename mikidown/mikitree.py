import datetime
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class ItemDialog(QDialog):
	def __init__(self, parent=None):
		super(ItemDialog, self).__init__(parent)
		self.editor = QLineEdit()
		editorLabel = QLabel("Page Name:")
		editorLabel.setBuddy(self.editor)
		self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|
										  QDialogButtonBox.Cancel)
		self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
		layout = QGridLayout()
		layout.addWidget(editorLabel, 0, 0)
		layout.addWidget(self.editor, 0, 1)
		layout.addWidget(self.buttonBox, 1, 1)
		self.setLayout(layout)
		self.connect(self.editor, SIGNAL("textEdited(QString)"),
					 self.updateUi)
		self.connect(self.buttonBox, SIGNAL("accepted()"), self.accept)
		self.connect(self.buttonBox, SIGNAL("rejected()"), self.reject)

	def setPath(self, path):
		self.path = path
	
	def setText(self, text):
		self.editor.setText(text)
		self.editor.selectAll()

	def updateUi(self):
		self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
				self.editor.text()!="")
	
	def accept(self):
		if self.path == '':
			notePath = self.editor.text()
		else:
			notePath = self.path + '/' + self.editor.text()

		if QFile.exists(notePath+'.markdown'):
			QMessageBox.warning(self, 'Error',
					'Page already exists: %s' % notePath)
		else:
			QDialog.accept(self)

class MikiTree(QTreeWidget):

	def __init__(self, parent=None):
		super(MikiTree, self).__init__(parent)
		self.header().close()
		self.setAcceptDrops(True)
		self.setDragEnabled(True)
		#self.setDropIndicatorShown(True)
		self.setDragDropOverwriteMode(True)
		self.setDragDropMode(QAbstractItemView.InternalMove)
		#self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.setContextMenuPolicy(Qt.CustomContextMenu)

		self.customContextMenuRequested.connect(self.treeMenu)
		

	def itemToPagePath(self, item):
		path = ''
		if not hasattr(item, 'text'):
			return path
		path = item.text(0)
		parent = item.parent()
		while parent is not None:
			path = parent.text(0) + '/' + path
			parent = parent.parent()
		return path

	def pagePathToItem(self, name):
		splitPath = name.split('/')
		depth = len(splitPath)
		itemList = self.findItems(splitPath[depth-1], Qt.MatchExactly|Qt.MatchRecursive)
		if len(itemList) == 1:
			return itemList[0]
		for item in itemList:
			parent = item.parent()
			for i in range(depth):
				if parent == None:
					break
				if depth-i-2 < 0:
					break
				if parent.text(0) == splitPath[depth-i-2]:
					if depth-i-2 == 0:
						return item
					else:
						parent = parent.parent()
	
	def currentItemName(self):
		item = self.currentItem()
		return self.itemToPagePath(item)

	def getPath(self, item):
		path = ''
		if not hasattr(item, 'text'):
			return path
		item = item.parent()
		while item is not None:
			path = item.text(0) + '/' + path
			item = item.parent()
		return path
	
	def treeMenu(self):
		menu = QMenu()
		menu.addAction("New Page...", self.newPage)
		menu.addAction("New Subpage...", self.newSubpage)
		menu.addSeparator()
		menu.addAction("Collapse All", self.collapseAll)
		menu.addAction("Uncollapse All", self.uncollapseAll)
		menu.addSeparator()
		menu.addAction('Rename Page...', lambda item=self.currentItem(): self.renamePage(item))
		self.delCallback = lambda item=self.currentItem(): self.delPage(item)
		menu.addAction("Delete Page", self.delCallback)
		menu.exec_(QCursor.pos())
	
	def newPage(self):
		if self.currentItem() is None:
			self.newSubpage(self)
		else:
			parent = self.currentItem().parent()
			if parent is not None:
				self.newPageCore(parent)
			else:
				self.newPageCore(self)

	def newSubpage(self):
		item = self.currentItem()
		self.newPageCore(item)
			
	def newPageCore(self, item):
		pagePath = self.itemToPagePath(item)
		dialog = ItemDialog(self)
		dialog.setPath(pagePath)
		if dialog.exec_():
			newPageName = dialog.editor.text()
			if hasattr(item, 'text'):
				pagePath = pagePath + '/'
			if not QDir(pagePath).exists():
				QDir.current().mkdir(pagePath)
			fileName = pagePath + newPageName + '.markdown'
			fh = QFile(fileName)
			fh.open(QIODevice.WriteOnly)
			savestream = QTextStream(fh)
			savestream << '# ' + newPageName + '\n'
			savestream << 'Created ' + str(datetime.date.today()) + '\n\n'
			fh.close()
			QTreeWidgetItem(item, [newPageName])
			self.sortItems(0, Qt.AscendingOrder)
			if pagePath != '':
				self.expandItem(item)

	def dropEvent(self, event):
		sourceItem = self.currentItem()
		sourcePath = self.itemToPagePath(sourceItem)
		targetItem = self.itemAt(event.pos())
		targetPath = self.itemToPagePath(targetItem)
		oldName = sourcePath + '.markdown'
		newName = targetPath + '/' + sourceItem.text(0) + '.markdown'
		oldDir = sourcePath
		newDir = targetPath + '/' + sourceItem.text(0)
		if not QDir(newName).exists():
			QDir.current().mkpath(targetPath)
		QDir.current().rename(oldName, newName)
		if sourceItem.childCount() != 0: 
			QDir.current().rename(oldDir, newDir)
		if sourceItem.parent() is not None:
			parentItem = sourceItem.parent()
			parentPath = self.itemToPagePath(parentItem)
			if parentItem.childCount() == 1:
				QDir.current().rmdir(parentPath)
		QTreeWidget.dropEvent(self, event)

	def renamePageWrapper(self):
		item = self.currentItem()
		self.renamePage(item)

	def renamePage(self, item):
		parent = item.parent()
		parentPath = self.itemToPagePath(parent)
		dialog = ItemDialog(self)
		dialog.setPath(parentPath)
		dialog.setText(item.text(0))
		if dialog.exec_():
			newPageName = dialog.editor.text()
			#pagePath = self.getPath(item)
			if hasattr(item, 'text'):		# if item is not QTreeWidget
				parentPath = parentPath + '/'
			oldName = parentPath + item.text(0)  + '.markdown'
			newName = parentPath + newPageName + '.markdown'
			QDir.current().rename(oldName, newName)
			if item.childCount() != 0:
				oldDir = parentPath + item.text(0)
				newDir = parentPath + newPageName
				QDir.current().rename(oldDir, newDir)
			item.setText(0, newPageName)
			self.sortItems(0, Qt.AscendingOrder)

	def exists(self, item):
		notePath = self.itemToPagePath(item) + '.markdown'
		return QFile.exists(notePath)

	def delPageWrapper(self):
		item = self.currentItem()
		self.delPage(item)

	def delPage(self, item):
		index = item.childCount()
		while index > 0:
			index = index -1
			self.dirname = item.child(index).text(0)
			self.delPage(item.child(index))

		pagePath = self.itemToPagePath(item)
		QDir.current().remove(pagePath + '.markdown')
		parent = item.parent()
		parentPath = self.itemToPagePath(parent)
		if parent is not None:
			index = parent.indexOfChild(item)
			parent.takeChild(index)
			if parent.childCount() == 0:	#if no child, dir not needed
				QDir.current().rmdir(parentPath)
		else:
			index = self.indexOfTopLevelItem(item)
			self.takeTopLevelItem(index)	
		QDir.current().rmdir(pagePath)

	def collapseAll(self):
		self.collapseAll()

	def uncollapseAll(self):
		self.expandAll()

	#def mouseMoveEvent(self, event):
	#	self.startDrag()
	#	QWidget.mouseMoveEvent(self, event)

	#def mousePressEvent(self, event):
		#self.clearSelection()
	#	QWidget.mousePressEvent(self, event)


