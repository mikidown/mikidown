import re

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets, QtWebKitWidgets
"""
from PyQt4.QtCore import QDir, QPoint, QTimer, QUrl
from PyQt4.QtGui import QDesktopServices
from PyQt4.QtWebKit import QWebView, QWebPage
"""
import markdown

class MikiView(QtWebKitWidgets.QWebView):

    def __init__(self, parent=None):
        super(MikiView, self).__init__(parent)
        self.parent = parent

        self.settings().clearMemoryCaches()
        self.notePath = parent.settings.notePath
        self.settings().setUserStyleSheetUrl(
            QtCore.QUrl('file://'+self.parent.settings.cssfile))
        print(QtCore.QUrl('file://'+self.parent.settings.cssfile))
        self.page().setLinkDelegationPolicy(QtWebKitWidgets.QWebPage.DelegateAllLinks)

        self.page().linkClicked.connect(self.linkClicked)
        self.page().linkHovered.connect(self.linkHovered)
        self.page().mainFrame(
        ).contentsSizeChanged.connect(self.contentsSizeChanged)

        self.scrollPosition = QtCore.QPoint(0, 0)

    def linkClicked(self, qurl):
        '''three kinds of link:
            external uri: http/https
            page ref link:
            toc anchor link: #
        '''
        name = qurl.toString()
        http = re.compile('https?://')
        if http.match(name):                        # external uri
            QtGui.QDesktopServices.openUrl(qurl)
            return

        self.load(qurl)
        name = name.replace('file://', '')
        name = name.replace(self.notePath, '').split('#')

        if name[0] == '/' and self.notePath in qurl.toString():
            #allow intersection links on same note to work
            item = self.parent.notesTree.currentItem()
        elif name[0] == '/':
            # it's pretty safe to do this since no matter the circumstances,
            # one wouldn't want to link to the root of their system
            return
        else:
            item = self.parent.notesTree.pageToItem(name[0])

        if not item or item == self.parent.notesTree.currentItem():
            return
        else:
            self.parent.notesTree.setCurrentItem(item)
            if len(name) > 1:
                link = "file://" + self.notePath + "/#" + name[1]
                self.load(QtCore.QUrl(link))
            viewFrame = self.page().mainFrame()
            self.scrollPosition = viewFrame.scrollPosition()

    def linkHovered(self, link, title, textContent):
        '''show link in status bar
            ref link shown as: /parent/child/pageName
            toc link shown as: /parent/child/pageName#anchor (ToFix)
        '''
        # TODO: link to page by: /parent/child/pageName#anchor
        if link == '':                              # not hovered
            self.parent.statusBar.showMessage(self.parent.notesTree.currentPage())
        else:                                       # beautify link
            link = link.replace('file://', '')
            link = link.replace(self.notePath, '')
            self.parent.statusBar.showMessage(link)

    def contentsSizeChanged(self, newSize):
        '''scroll notesView while editing (adding new lines)
           Whithout this, every `updateView` will result in scroll to top.
        '''
        if self.scrollPosition == QtCore.QPoint(0, 0):
            return
        viewFrame = self.page().mainFrame()
        newY = self.scrollPosition.y(
        ) + newSize.height() - self.contentsSize.height()
        self.scrollPosition.setY(newY)
        viewFrame.setScrollPosition(self.scrollPosition)

    def updateView(self):
        # url_notebook = 'file://' + os.path.join(self.notePath, '/')
        viewFrame = self.page().mainFrame()
        # Store scrollPosition before update notesView
        self.scrollPosition = viewFrame.scrollPosition()
        self.contentsSize = viewFrame.contentsSize()
        url_notebook = 'file://' + self.notePath + '/'
        self.setHtml(self.parent.notesEdit.toHtml(), QtCore.QUrl(url_notebook))
        # Restore previous scrollPosition
        viewFrame.setScrollPosition(self.scrollPosition)

    def updateLiveView(self):
        if self.parent.actions.get('split').isChecked():
            QtCore.QTimer.singleShot(1000, self.updateView)

