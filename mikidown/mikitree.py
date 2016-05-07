"""

Naming convention:
    * item - the visual element in MikiTree
    * page - denoted by item hierarchy e.g. `foo/bar` is a subpage of `foo`
    * file - the actual file on disk
"""
import os
import datetime

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets
"""
from PyQt4.QtCore import Qt, QDir, QFile, QIODevice, QSize, QTextStream
from PyQt4.QtGui import (QAbstractItemView, QCursor, QMenu, QMessageBox, QTreeWidget, QTreeWidgetItem)
"""
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from whoosh.writing import AsyncWriter

from .config import Setting
from .utils import LineEditDialog, TTPL_COL_DATA, TTPL_COL_EXTRA_DATA
from . import mikitemplate


class MikiTree(QtWidgets.QTreeWidget):

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
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        # self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.customContextMenuRequested.connect(self.contextMenu)
        self.nvwCallback = lambda item: None
        self.nvwtCallback = lambda item: None

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

        # if page is empty return current item
        if page == '':
            return self.currentItem()

        # strip the beginning and ending '/' character
        if page[0] == '/':
            page = page[1:]
        if page[-1] == '/':
            page = page[:-1]

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
            if QtCore.QFile.exists(filepath):
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
        #path = os.path.join(self.settings.attachmentPath, page)
        path = self.settings.attachmentPath+"/"+page
        return path

    def currentPage(self):
        return self.itemToPage(self.currentItem())

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            return
        else:
            QtWidgets.QTreeWidget.mousePressEvent(self, event)

    def contextMenu(self, qpoint):
        """ contextMenu shown when right click the mouse """
        item = self.itemAt(qpoint)
        menu = QtWidgets.QMenu()
        if item is None or item.parent() is None:
            menu.addAction(self.tr("New Page..."), lambda: self.newPageCore(self, None))
        else:
            menu.addAction(self.tr("New Page..."), lambda: self.newPageCore(item.parent(), None))
        
        if item is None:
            menu.addAction(self.tr("New Subpage..."), lambda: self.newPageCore(self, None))
        else:
            menu.addAction(self.tr("New Subpage..."), lambda: self.newPageCore(item, None))

        if item is None or item.parent() is None:
            menu.addAction(self.tr("New page from template..."), lambda: self.newPageCore(self, None, useTemplate=True))
        else:
            menu.addAction(self.tr("New page from template..."), lambda: self.newPageCore(item.parent(), None, useTemplate=True))

        if item is None:
            menu.addAction(self.tr("New subpage from template..."), lambda: self.newPageCore(self, None, useTemplate=True))
        else:
            menu.addAction(self.tr("New subpage from template..."), lambda: self.newPageCore(item, None, useTemplate=True))
        menu.addAction(self.tr("View separately"), lambda: self.nvwCallback(item))
        menu.addAction(self.tr("View separately (plain text)"), lambda: self.nvwtCallback(item))
        menu.addSeparator()
        menu.addAction(self.tr("Collapse This Note Tree"),
                       lambda: self.recurseCollapse(item))
        menu.addAction(self.tr("Uncollapse This Note Tree"),
                       lambda: self.recurseExpand(item))
        menu.addAction(self.tr("Collapse All"), self.collapseAll)
        menu.addAction(self.tr("Uncollapse All"), self.expandAll)
        menu.addSeparator()
        menu.addAction(self.tr('Rename Page...'), lambda: self.renamePage(item))
        menu.addAction(self.tr("Delete Page"), lambda: self.delPage(item))
        menu.exec_(self.mapToGlobal(qpoint))

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

    def newPageCore(self, item, newPageName, useTemplate=False, templateTitle=None, templateBody=None):
        pagePath = os.path.join(self.notePath, self.itemToPage(item)).replace(os.sep, '/')
        if not newPageName:
            if useTemplate:
                dialog = mikitemplate.PickTemplateDialog(pagePath, self.settings, parent=self)
                if dialog.exec_():
                    curTitleIdx = dialog.titleTemplates.currentIndex()
                    curBodyIdx = dialog.bodyTemplates.currentIndex()
                    dtnow = datetime.datetime.now()
                    if curTitleIdx > -1:
                        titleItem = dialog.titleTemplates.model().item(curTitleIdx)
                        titleItemContent = titleItem.data(TTPL_COL_DATA)
                        titleItemType = titleItem.data(TTPL_COL_EXTRA_DATA)
                        titleParameter = dialog.titleTemplateParameter.text()
                        newPageName = mikitemplate.makeTemplateTitle(titleItemType, 
                            titleItemContent, dtnow=dtnow, userinput=titleParameter)
                    if curBodyIdx > -1:
                        bodyItemIdx = dialog.bodyTemplates.rootModelIndex().child(curBodyIdx, 0)
                        bodyFPath = dialog.bodyTemplates.model().filePath(bodyItemIdx)
                    else:
                        bodyFPath = None
            else:
                dialog = LineEditDialog(pagePath, self)
                if dialog.exec_():
                    newPageName = dialog.editor.text()

        prevparitem = None

        if newPageName:
            if hasattr(item, 'text'):
                pagePath = os.path.join(self.notePath,
                                        pagePath + '/').replace(os.sep, '/')
            if not QtCore.QDir(pagePath).exists():
                QtCore.QDir(self.notePath).mkdir(pagePath)

            if not QtCore.QDir(os.path.dirname(newPageName)).exists():
                curdirname = os.path.dirname(newPageName)
                needed_parents = []
                while curdirname != '':
                    needed_parents.append(curdirname)
                    curdirname = os.path.dirname(curdirname)

                #create the needed hierarchy in reverse order
                for i, needed_parent in enumerate(needed_parents[::-1]):
                    paritem = self.pageToItem(needed_parent)
                    if paritem is None:
                        if i == 0:
                            self.newPageCore(item, os.path.basename(needed_parent))
                        else:
                            self.newPageCore(prevparitem, os.path.basename(needed_parent))
                        QtCore.QDir(pagePath).mkdir(needed_parent)
                    elif not QtCore.QDir(os.path.join(self.notePath, needed_parent).replace(os.sep, '/')).exists():
                        QtCore.QDir(pagePath).mkdir(needed_parent)
                    if paritem is not None:
                        prevparitem = paritem
                    else:
                        prevparitem = self.pageToItem(needed_parent)

            fileName = pagePath + newPageName + self.settings.fileExt
            fh = QtCore.QFile(fileName)
            fh.open(QtCore.QIODevice.WriteOnly)

            savestream = QtCore.QTextStream(fh)
            if useTemplate and bodyFPath is not None:
                with open(bodyFPath, 'r', encoding='utf-8') as templatef:
                    savestream << mikitemplate.makeTemplateBody(
                        os.path.basename(newPageName), dtnow=dtnow, 
                        dt_in_body_txt=self.tr("Created {}"),
                        body=templatef.read())
            else:
                savestream << mikitemplate.makeDefaultBody(os.path.basename(newPageName), self.tr("Created {}"))
            fh.close()
            if prevparitem is not None:
                QtWidgets.QTreeWidgetItem(prevparitem, [os.path.basename(newPageName)])
            else:
                QtWidgets.QTreeWidgetItem(item, [os.path.basename(newPageName)])
            newItem = self.pageToItem(pagePath + newPageName)
            self.sortItems(0, Qt.AscendingOrder)
            self.setCurrentItem(newItem)
            if hasattr(item, 'text'):
                self.expandItem(item)

            # create attachment folder if not exist
            attDir = self.itemToAttachmentDir(newItem)
            if not QtCore.QDir(attDir).exists():
                QtCore.QDir().mkpath(attDir)

            # TODO improvement needed, can be reused somehow
            with open(fileName, 'r') as fileobj:
                content = fileobj.read()

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

        if QtCore.QFile.exists(newFile):
            QtWidgets.QMessageBox.warning(self, self.tr("Error"),
                                self.tr("File already exists: %s") % newFile)
            return

        # rename file/folder, remove parent note folder if necessary
        if targetPage != '':
            QtCore.QDir(self.notePath).mkpath(targetPage)
        QtCore.QDir(self.notePath).rename(oldFile, newFile)
        if sourceItem.childCount() != 0:
            QtCore.QDir(self.notePath).rename(oldDir, newDir)
        if sourceItem.parent() is not None:
            parentItem = sourceItem.parent()
            parentPage = self.itemToPage(parentItem)
            if parentItem.childCount() == 1:
                QtCore.QDir(self.notePath).rmdir(parentPage)

        # pass the event to default implementation
        QtWidgets.QTreeWidget.dropEvent(self, event)
        self.sortItems(0, Qt.AscendingOrder)
        if hasattr(targetItem, 'text'):
            self.expandItem(targetItem)

        # if attachment folder exists, rename it
        if QtCore.QDir().exists(oldAttDir):
            # make sure target folder exists
            QtCore.QDir().mkpath(self.itemToAttachmentDir(targetItem))

            newAttDir = self.itemToAttachmentDir(sourceItem)
            QtCore.QDir().rename(oldAttDir, newAttDir)
            self.parent.updateAttachmentView()

    def renamePage(self, item):
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
            QtCore.QDir(self.notePath).rename(oldFile, newFile)
            if item.childCount() != 0:
                oldDir = parentPage + item.text(0)
                newDir = parentPage + newPageName
                QtCore.QDir(self.notePath).rename(oldDir, newDir)
            item.setText(0, newPageName)
            self.sortItems(0, Qt.AscendingOrder)

            # if attachment folder exists, rename it
            if QtCore.QDir().exists(oldAttDir):
                newAttDir = self.itemToAttachmentDir(item)
                QtCore.QDir().rename(oldAttDir, newAttDir)
                self.parent.updateAttachmentView()

    def pageExists(self, noteFullName):
        return QtCore.QFile.exists(self.pageToFile(noteFullName))

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
        for info in QtCore.QDir(attDir).entryInfoList():
            QtCore.QDir().remove(info.absoluteFilePath())
        QtCore.QDir().rmdir(attDir)

        pagePath = self.itemToPage(item)
        self.ix = open_dir(self.settings.indexdir)
        query = QueryParser('path', self.ix.schema).parse(pagePath)
        #writer = self.ix.writer()
        writer = AsyncWriter(self.ix)
        n = writer.delete_by_query(query)
        # n = writer.delete_by_term('path', pagePath)
        writer.commit()
        #self.ix.close()
        b = QtCore.QDir(self.notePath).remove(self.pageToFile(pagePath))
        parent = item.parent()
        parentPage = self.itemToPage(parent)
        if parent is not None:
            index = parent.indexOfChild(item)
            parent.takeChild(index)
            if parent.childCount() == 0:  # if no child, dir not needed
                QtCore.QDir(self.notePath).rmdir(parentPage)
        else:
            index = self.indexOfTopLevelItem(item)
            self.takeTopLevelItem(index)
        QtCore.QDir(self.notePath).rmdir(pagePath)

    def sizeHint(self):
        return QtCore.QSize(200, 0)

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

class TocTree(QtWidgets.QTreeWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.header().close()

    def updateToc(self, root, entries):
        self.clear()
        item = QtWidgets.QTreeWidgetItem(self, [root, '0'])
        curLevel = 0
        for (level, h, p, a) in entries:
            val = [h, str(p), a]
            if level == curLevel:
                item = QtWidgets.QTreeWidgetItem(item.parent(), val)
            elif level < curLevel:
                item = QtWidgets.QTreeWidgetItem(item.parent().parent(), val)
                curLevel = level
            else:
                item = QtWidgets.QTreeWidgetItem(item, val)
                curLevel = level
        self.expandAll()

    def sizeHint(self):
        return QtCore.QSize(200, 0)
