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

	def updateUi(self):
		self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
				self.editor.text()!="")


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
		

	def ItemToName(self, item):
		name = item.text(0)
		parent = item.parent()
		while parent is not None:
			name = parent.text(0) + '/' + name
			parent = parent.parent()
		return name

	def NameToItem(self, name):
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
		return self.ItemToName(item)

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
		menu.addAction("New Page", self.newPage)
		self.subpageCallback = lambda item=self.currentItem(): self.newSubpage(item)
		menu.addAction("New Subpage", self.subpageCallback)
		menu.addSeparator()
		menu.addAction("Collapse All", self.collapseAll)
		menu.addAction("Uncollapse All", self.uncollapseAll)
		menu.addSeparator()
		menu.addAction('Rename Page', lambda item=self.currentItem(): self.renamePage(item))
		self.delCallback = lambda item=self.currentItem(): self.delPage(item)
		menu.addAction("Delete Page", self.delCallback)
		menu.exec_(QCursor.pos())
	
	def newPage(self):
		if self.currentItem() is None:
			self.newSubpage(self)
		else:
			parent = self.currentItem().parent()
			if parent is not None:
				self.newSubpage(parent)
			else:
				self.newSubpage(self)

	def newSubpage(self, item):
		dialog = ItemDialog(self)
		if dialog.exec_():
			self.filename = dialog.editor.text()
			self.newPageWrapper(item, self.filename)
			self.sortItems(0, Qt.AscendingOrder)
			
		self.editted = 0
	def newPageWrapper(self, item, pageName):
		pagePath = self.getPath(item)
		if hasattr(item, 'text'):
			pagePath = pagePath + item.text(0) + '/'
		if not QDir(pagePath).exists():
			QDir.current().mkdir(pagePath)
		fh = QFile(pagePath+pageName+'.markdown')
		fh.open(QIODevice.WriteOnly)
		savestream = QTextStream(fh)
		savestream << '# ' + pageName + '\n'
		savestream << 'Created ' + str(datetime.date.today()) + '\n\n'
		fh.close()
		QTreeWidgetItem(item, [pageName])
		if pagePath != '':
			self.expandItem(item)

	def dropEvent(self, event):
		#event.setDropAction(Qt.MoveAction)
		#event.accept()
		sourceItem = self.currentItem()
		sourcePath = self.getPath(sourceItem)
		targetItem = self.itemAt(event.pos())
		targetPath = self.getPath(targetItem)
		oldName = sourcePath + sourceItem.text(0) + '.markdown'
		newName = targetPath + targetItem.text(0) + '/' + sourceItem.text(0) + '.markdown'
		oldDir = sourcePath + sourceItem.text(0)
		newDir = targetPath + targetItem.text(0) + '/' + sourceItem.text(0)
		if not QDir(newName).exists():
			QDir.current().mkpath(targetPath+targetItem.text(0))
		QDir.current().rename(oldName, newName)
		if sourceItem.childCount() != 0: 
			#if not QDir(newDir).exists():
			#	QDir.current.mkpath(newDir)
			QDir.current().rename(oldDir, newDir)
		if sourceItem.parent() is not None:
			parentItem = sourceItem.parent()
			parentPath = self.getPath(parentItem)
			if parentItem.childCount() == 1:
				QDir.current().rmdir(parentPath + parentItem.text(0))
		QTreeWidget.dropEvent(self, event)

	def renamePage(self, item):
		dialog = ItemDialog(self)
		if dialog.exec_():
			pageName = dialog.editor.text()
			pagePath = self.getPath(item)
			oldName = pagePath + item.text(0) + '.markdown'
			newName = pagePath + pageName + '.markdown'
			QDir.current().rename(oldName, newName)
			if item.childCount() != 0:
				oldDir = pagePath + item.text(0)
				newDir = pagePath + pageName
				QDir.current().rename(oldDir, newDir)
			item.setText(0, pageName)
			self.sortItems(0, Qt.AscendingOrder)


	def delPage(self, item):
		index = item.childCount()
		while index > 0:
			index = index -1
			self.dirname = item.child(index).text(0)
			self.delPage(item.child(index))

		path = self.getPath(item)
		QDir.current().remove(path + item.text(0) + '.markdown')
		parent = item.parent()
		if parent is not None:
			index = parent.indexOfChild(item)
			parent.takeChild(index)
			if parent.childCount() == 0:
				QDir.current().rmdir(path)
		else:
			index = self.indexOfTopLevelItem(item)
			self.takeTopLevelItem(index)	
		#self.showNote(self.currentItem())
		QDir.current().rmdir(path + item.text(0))

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


