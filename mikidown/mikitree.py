import os
import datetime

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from whoosh.index import open_dir
from whoosh.qparser import QueryParser

from mikidown.config import Setting


class ItemDialog(QDialog):
    def __init__(self, parent=None):
        super(ItemDialog, self).__init__(parent)
        self.editor = QLineEdit()
        editorLabel = QLabel("Page Name:")
        editorLabel.setBuddy(self.editor)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok |
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
            self.editor.text() != "")

    def accept(self):
        if self.path == '':
            notePath = self.editor.text()
        else:
            notePath = self.path + '/' + self.editor.text()

        if QFile.exists(notePath+'.md') or QFile.exists(notePath+'.mkd') or QFile.exists(notePath+'.markdown'):
            QMessageBox.warning(self, 'Error',
                                'Page already exists: %s' % notePath)
        else:
            QDialog.accept(self)


class MikiTree(QTreeWidget):

    def __init__(self, parent=None):
        super(MikiTree, self).__init__(parent)
        self.settings = parent.settings
        self.notebookPath = self.settings.notebookPath

        self.header().close()
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        # self.setDropIndicatorShown(True)
        self.setDragDropOverwriteMode(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        # self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.customContextMenuRequested.connect(self.treeMenu)
        self.indexdir = os.path.join(self.notebookPath, self.settings.indexdir)

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
        if name[0] == '/':
            name = name[1:len(name)]
        if name[-1] == '/':
            name = name[0:-1]
        splitPath = name.split('/')
        depth = len(splitPath)
        # print(depth)
        itemList = self.findItems(
            splitPath[depth-1], Qt.MatchExactly|Qt.MatchRecursive)
        if len(itemList) == 1:
            # print(itemList[0].text(0))
            return itemList[0]
        for item in itemList:
            path = self.itemToPagePath(item)
            if name == path:
                return item
            '''
            parent = item.parent()
            for i in range(depth):
                print(i)
                if parent == None:
                    if i == depth-1:
                        return item
                    else:
                        continue
                if depth-i-2 < 0:
                    break
                if parent.text(0) == splitPath[depth-i-2]:
                    if depth-i-2 == 0:
                        return item
                    else:
                        parent = parent.parent()
            '''

    def noteFullPath(self, noteFullName):
        ''' FullPath = notebookPath + noteFullName + fileExt
        fileExt is stored in notebook.conf 
        '''
        extName = ['.md', '.mkd', '.markdown']
        defExt = self.settings.fileExt
        extName.remove(defExt)
        extName.insert(0, defExt)
        for ext in extName:
            filename = os.path.join(self.notebookPath,
                                    noteFullName + ext)
            if QFile.exists(filename):
                return filename

        return ""

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
        menu.addAction("Collapse This Note Tree",
                       lambda item=self.currentItem(): self.recurseCollapse(item))
        menu.addAction("Uncollapse This Note Tree",
                       lambda item=self.currentItem():  self.recurseExpand(item))
        menu.addAction("Collapse All", self.collapseAll)
        menu.addAction("Uncollapse All", self.expandAll)
        menu.addSeparator()
        menu.addAction('Rename Page...',
                       lambda item=self.currentItem(): self.renamePage(item))
        self.delCallback = lambda item=self.currentItem(): self.delPage(item)
        menu.addAction("Delete Page", self.delCallback)
        menu.exec_(QCursor.pos())

    def newPage(self, name=None):
        if self.currentItem() is None:
            self.newPageCore(self, name)
        else:
            parent = self.currentItem().parent()
            if parent is not None:
                self.newPageCore(parent, name)
            else:
                self.newPageCore(self, name)

    def newSubpage(self, name=None):
        item = self.currentItem()
        self.newPageCore(item, name)

    def newPageCore(self, item, newPageName):
        pagePath = os.path.join(self.notebookPath, self.itemToPagePath(item))
        if not newPageName:
            dialog = ItemDialog(self)
            dialog.setPath(pagePath)
            if dialog.exec_():
                newPageName = dialog.editor.text()
        if newPageName:
            if hasattr(item, 'text'):
                pagePath = os.path.join(self.notebookPath, 
                                        pagePath + '/')
            if not QDir(pagePath).exists():
                QDir(self.notebookPath).mkdir(pagePath)
            fileName = pagePath + newPageName + self.settings.fileExt
            fh = QFile(fileName)
            fh.open(QIODevice.WriteOnly)
            savestream = QTextStream(fh)
            savestream << '# ' + newPageName + '\n'
            savestream << 'Created ' + str(datetime.date.today()) + '\n\n'
            fh.close()
            QTreeWidgetItem(item, [newPageName])
            newItem = self.pagePathToItem(pagePath + newPageName)
            self.sortItems(0, Qt.AscendingOrder)
            self.setCurrentItem(newItem)
            if hasattr(item, 'text'):
                self.expandItem(item)

            # TODO improvement needed, can be reused somehow
            fileobj = open(fileName, 'r')
            content = fileobj.read()
            fileobj.close()
            self.ix = open_dir(self.indexdir)
            writer = self.ix.writer()
            writer.add_document(path=pagePath+newPageName, content=content)
            writer.commit()

    def dropEvent(self, event):
        sourceItem = self.currentItem()
        sourcePath = self.itemToPagePath(sourceItem)
        targetItem = self.itemAt(event.pos())
        targetPath = self.itemToPagePath(targetItem)
        if targetPath != '':
            targetPath = targetPath + '/'
        oldName = self.noteFullPath(sourceItem.text(0))
        newName = targetPath + sourceItem.text(0) + self.settings.fileExt
        oldDir = sourcePath
        newDir = targetPath + sourceItem.text(0)
        print(newName)
        # if QDir(newName).exists():
        if QFile.exists(newName):
            QMessageBox.warning(self, 'Error',
                                'Page already exists: %s' % newName)
            return

        # if not QDir(newName).exists():
        QDir(self.notebookPath).mkpath(targetPath)
        QDir(self.notebookPath).rename(oldName, newName)
        if sourceItem.childCount() != 0:
            QDir(self.notebookPath).rename(oldDir, newDir)
        if sourceItem.parent() is not None:
            parentItem = sourceItem.parent()
            parentPath = self.itemToPagePath(parentItem)
            if parentItem.childCount() == 1:
                QDir(self.notebookPath).rmdir(parentPath)
        QTreeWidget.dropEvent(self, event)
        self.sortItems(0, Qt.AscendingOrder)
        if hasattr(targetItem, 'text'):
            self.expandItem(targetItem)

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
            # pagePath = self.getPath(item)
            # if hasattr(item, 'text'):       # if item is not QTreeWidget
            if parentPath != '':
                parentPath = parentPath + '/'
            oldName = self.noteFullPath(item.text(0))
            newName = parentPath + newPageName + self.settings.fileExt
            QDir(self.notebookPath).rename(oldName, newName)
            if item.childCount() != 0:
                oldDir = parentPath + item.text(0)
                newDir = parentPath + newPageName
                QDir(self.notebookPath).rename(oldDir, newDir)
            item.setText(0, newPageName)
            self.sortItems(0, Qt.AscendingOrder)

    def exists(self, noteFullName):
        if self.noteFullPath(noteFullName) != "" :
            return True
        else:
            return False

    def delPageWrapper(self):
        item = self.currentItem()
        self.delPage(item)

    def delPage(self, item):

        index = item.childCount()
        while index > 0:
            index = index - 1
            self.dirname = item.child(index).text(0)
            self.delPage(item.child(index))

        pagePath = self.itemToPagePath(item)
        self.ix = open_dir(self.indexdir)
        query = QueryParser('path', self.ix.schema).parse(pagePath)
        writer = self.ix.writer()
        n = writer.delete_by_query(query)
        # n = writer.delete_by_term('path', pagePath)
        writer.commit()
        b = QDir(self.notebookPath).remove(self.noteFullPath(pagePath))
        parent = item.parent()
        parentPath = self.itemToPagePath(parent)
        if parent is not None:
            index = parent.indexOfChild(item)
            parent.takeChild(index)
            if parent.childCount() == 0:  # if no child, dir not needed
                QDir(self.notebookPath).rmdir(parentPath)
        else:
            index = self.indexOfTopLevelItem(item)
            self.takeTopLevelItem(index)
        QDir(self.notebookPath).rmdir(pagePath)

    def recurseCollapse(self, item):
        for i in range(item.childCount()):
            a_item = item.child(i)
            self.recurseCollapse(a_item)
            self.collapseItem(item)

    def recurseExpand(self, item):
        self.expandItem(item)
        for i in range(item.childCount()):
            a_item = item.child(i)
            self.recurseExpand(a_item)
