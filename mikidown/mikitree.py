"""

Naming convention:
    * item - the visual element in MikiTree
    * page - denoted by item hierarchy e.g. `foo/bar` is a subpage of `foo`
    * file - the actual file on disk
"""
import os
import datetime

from PyQt4.QtCore import Qt, QDir, QFile, QIODevice, QSize, QTextStream
from PyQt4.QtGui import (QAbstractItemView, QCursor, QMenu, QMessageBox, QTreeWidget, QTreeWidgetItem)
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from whoosh.writing import AsyncWriter

from .config import Setting
from .utils import LineEditDialog


class MikiTree(QTreeWidget):

    def __init__(self, parent=None):
        super(MikiTree, self).__init__(parent)
        self.parent = parent
        self.settings = parent.settings
        self.notePath = self.settings.notePath

        self.header().close()
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        # self.setDropIndicatorShown(True)
        self.setDragDropOverwriteMode(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        # self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.customContextMenuRequested.connect(self.contextMenu)

    def itemToPage(self, item):
        """ get item hierarchy from item """

        page = ''
        if not hasattr(item, 'text'):
            return page
        page = item.text(0)
        parent = item.parent()
        while parent is not None:
            page = parent.text(0) + '/' + page
            parent = parent.parent()
        return page

    def pageToItem(self, page):
        """ get item from item hierarchy """

        # strip the beginning and ending '/' character
        if page[0] == '/':
            page = page[1:len(page)]
        if page[-1] == '/':
            page = page[0:-1]

        # find all items named pieces[-1], then match the page name.
        pieces = page.split('/')
        itemList = self.findItems(
            pieces[-1], Qt.MatchExactly|Qt.MatchRecursive)
        if len(itemList) == 1:
            return itemList[0]
        for item in itemList:
            if page == self.itemToPage(item):
                return item

    def itemToFile(self, item):
        return self.pageToFile(self.itemToPage(item))

    def pageToFile(self, page):
        """ get filepath from page
            filepath = notePath + page + fileExt
            fileExt is stored in notebook.conf
        """

        # When exists foo.md, foo.mkd, foo.markdown,
        # the one with defExt will be returned
        extName = ['.md', '.mkd', '.markdown']
        defExt = self.settings.fileExt
        if defExt in extName:
            extName.remove(defExt)
        else:
            print("Warning: detected file extension name is", defExt)
            print("    Your config file is located in", self.notePath + "/notebook.conf")
        extName.insert(0, defExt)
        for ext in extName:
            filepath = os.path.join(self.notePath, page + ext)
            if QFile.exists(filepath):
                return filepath

        # return filename with default extension name even if file not exists.
        return os.path.join(self.notePath, page + defExt)

    def itemToHtmlFile(self, item):
        """ The corresponding html file path """
        page = self.itemToPage(item)
        return os.path.join(self.settings.htmlPath, page + ".html")

    def itemToAttachmentDir(self, item):
        """ The corresponding attachment directory
        dirName is constructed by pageName and md5(page), so that no nesting
        needed and manipulation become easy
        """
        page = self.itemToPage(item)
        return os.path.join(self.settings.attachmentPath, page)

    def currentPage(self):
        return self.itemToPage(self.currentItem())

    def contextMenu(self):
        """ contextMenu shown when right click the mouse """

        menu = QMenu()
        menu.addAction("New Page...", self.newPage)
        menu.addAction("New Subpage...", self.newSubpage)
        menu.addSeparator()
        menu.addAction("Collapse This Note Tree",
                       lambda item=self.currentItem(): self.recurseCollapse(item))
        menu.addAction("Uncollapse This Note Tree",
                       lambda item=self.currentItem(): self.recurseExpand(item))
        menu.addAction("Collapse All", self.collapseAll)
        menu.addAction("Uncollapse All", self.expandAll)
        menu.addSeparator()
        menu.addAction('Rename Page...', self.renamePage)
        menu.addAction("Delete Page", self.delPageWrapper)
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
        pagePath = os.path.join(self.notePath, self.itemToPage(item)).replace(os.sep, '/')
        if not newPageName:
            dialog = LineEditDialog(pagePath, self)
            if dialog.exec_():
                newPageName = dialog.editor.text()
        if newPageName:
            if hasattr(item, 'text'):
                pagePath = os.path.join(self.notePath,
                                        pagePath + '/').replace(os.sep, '/')
            if not QDir(pagePath).exists():
                QDir(self.notePath).mkdir(pagePath)
            fileName = pagePath + newPageName + self.settings.fileExt
            fh = QFile(fileName)
            fh.open(QIODevice.WriteOnly)
            savestream = QTextStream(fh)
            savestream << '# ' + newPageName + '\n'
            savestream << 'Created ' + str(datetime.date.today()) + '\n\n'
            fh.close()
            QTreeWidgetItem(item, [newPageName])
            newItem = self.pageToItem(pagePath + newPageName)
            self.sortItems(0, Qt.AscendingOrder)
            self.setCurrentItem(newItem)
            if hasattr(item, 'text'):
                self.expandItem(item)

            # create attachment folder if not exist
            attDir = self.itemToAttachmentDir(newItem)
            if not QDir(attDir).exists():
                QDir().mkpath(attDir)

            # TODO improvement needed, can be reused somehow
            fileobj = open(fileName, 'r')
            content = fileobj.read()
            fileobj.close()
            self.ix = open_dir(self.settings.indexdir)
            #writer = self.ix.writer()
            writer = AsyncWriter(self.ix)
            writer.add_document(path=pagePath+newPageName, content=content)
            writer.commit()
            #self.ix.close()

    def dropEvent(self, event):
        """ A note is related to four parts:
            note file, note folder containing child note, parent note folder, attachment folder.
        When drag/drop, should take care of:
        1. rename note file ("rename" is just another way of saying "move")
        2. rename note folder
        3. if parent note has no more child, remove parent note folder
        4. rename attachment folder
        """

        # construct file/folder names before and after drag/drop
        sourceItem = self.currentItem()
        sourcePage = self.itemToPage(sourceItem)
        oldAttDir = self.itemToAttachmentDir(sourceItem)
        targetItem = self.itemAt(event.pos())
        targetPage = self.itemToPage(targetItem)
        oldFile = self.itemToFile(sourceItem)
        newFile = os.path.join(targetPage,
            sourceItem.text(0) + self.settings.fileExt)
        oldDir = sourcePage
        newDir = os.path.join(targetPage, sourceItem.text(0))

        if QFile.exists(newFile):
            QMessageBox.warning(self, 'Error',
                                'File already exists: %s' % newFile)
            return

        # rename file/folder, remove parent note folder if necessary
        if targetPage != '':
            QDir(self.notePath).mkpath(targetPage)
        QDir(self.notePath).rename(oldFile, newFile)
        if sourceItem.childCount() != 0:
            QDir(self.notePath).rename(oldDir, newDir)
        if sourceItem.parent() is not None:
            parentItem = sourceItem.parent()
            parentPage = self.itemToPage(parentItem)
            if parentItem.childCount() == 1:
                QDir(self.notePath).rmdir(parentPage)

        # pass the event to default implementation
        QTreeWidget.dropEvent(self, event)
        self.sortItems(0, Qt.AscendingOrder)
        if hasattr(targetItem, 'text'):
            self.expandItem(targetItem)

        # if attachment folder exists, rename it
        if QDir().exists(oldAttDir):
            # make sure target folder exists
            QDir().mkpath(self.itemToAttachmentDir(targetItem))

            newAttDir = self.itemToAttachmentDir(sourceItem)
            QDir().rename(oldAttDir, newAttDir)
            self.parent.updateAttachmentView()

    def renamePage(self):
        item = self.currentItem()
        oldAttDir = self.itemToAttachmentDir(item)
        parent = item.parent()
        parentPage = self.itemToPage(parent)
        parentPath = os.path.join(self.notePath, parentPage)
        dialog = LineEditDialog(parentPath, self)
        dialog.setText(item.text(0))
        if dialog.exec_():
            newPageName = dialog.editor.text()
            # if hasattr(item, 'text'):       # if item is not QTreeWidget
            if parentPage != '':
                parentPage = parentPage + '/'
            oldFile = self.itemToFile(item)
            newFile = parentPage + newPageName + self.settings.fileExt
            QDir(self.notePath).rename(oldFile, newFile)
            if item.childCount() != 0:
                oldDir = parentPage + item.text(0)
                newDir = parentPage + newPageName
                QDir(self.notePath).rename(oldDir, newDir)
            item.setText(0, newPageName)
            self.sortItems(0, Qt.AscendingOrder)

            # if attachment folder exists, rename it
            if QDir().exists(oldAttDir):
                newAttDir = self.itemToAttachmentDir(item)
                QDir().rename(oldAttDir, newAttDir)
                self.parent.updateAttachmentView()

    def pageExists(self, noteFullName):
        return QFile.exists(self.pageToFile(noteFullName))

    def delPageWrapper(self):
        item = self.currentItem()
        self.delPage(item)

    def delPage(self, item):

        index = item.childCount()
        while index > 0:
            index = index - 1
            self.dirname = item.child(index).text(0)
            self.delPage(item.child(index))

        # remove attachment folder
        attDir = self.itemToAttachmentDir(item)
        for info in QDir(attDir).entryInfoList():
            QDir().remove(info.absoluteFilePath())
        QDir().rmdir(attDir)

        pagePath = self.itemToPage(item)
        self.ix = open_dir(self.settings.indexdir)
        query = QueryParser('path', self.ix.schema).parse(pagePath)
        #writer = self.ix.writer()
        writer = AsyncWriter(self.ix)
        n = writer.delete_by_query(query)
        # n = writer.delete_by_term('path', pagePath)
        writer.commit()
        #self.ix.close()
        b = QDir(self.notePath).remove(self.pageToFile(pagePath))
        parent = item.parent()
        parentPage = self.itemToPage(parent)
        if parent is not None:
            index = parent.indexOfChild(item)
            parent.takeChild(index)
            if parent.childCount() == 0:  # if no child, dir not needed
                QDir(self.notePath).rmdir(parentPage)
        else:
            index = self.indexOfTopLevelItem(item)
            self.takeTopLevelItem(index)
        QDir(self.notePath).rmdir(pagePath)

    def sizeHint(self):
        return QSize(200, 0)

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

class TocTree(QTreeWidget):

    def __init__(self, parent=None):
        super(TocTree, self).__init__(parent)

    def sizeHint(self):
        return QSize(200, 0)
