"""
Search module

Search results are displayed in a QWebView widget.
"""

from PyQt4.QtCore import QSize, QUrl
from PyQt4.QtGui import QCursor, QToolTip
from PyQt4.QtWebKit import QWebView, QWebPage


class MikiSearch(QWebView):

    def __init__(self, parent=None):
        super(MikiSearch, self).__init__(parent)
        self.parent = parent

        self.settings().clearMemoryCaches()
        self.flag = False
        self.link = None
        self.setMouseTracking(True)
        self.page().linkHovered.connect(self.linkHovered)
        self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.page().linkClicked.connect(self.linkClicked)

    def linkClicked(self, qurl):
        """ Overload function.
            Click link to open the note.
        """
        path = qurl.toString()
        item = self.parent.notesTree.pageToItem(path)
        if item:
            self.parent.notesTree.setCurrentItem(item)

    def linkHovered(self, link, title, textContent):
        """ Overload function.
            Show tooltip when hovered.
        # ToFix: tooltip disappear too soon.
        """
        #self.setToolTip(link)
        if link:
            self.flag = True
            self.link = link
            QToolTip.showText(QCursor.pos(), self.link)
        else:
            self.flag = False

    def mouseMoveEvent(self, event):
        if self.flag:
            QToolTip.showText(QCursor.pos(), self.link)
        else:
            QToolTip.hideText()
        QWebView.mouseMoveEvent(self, event)

    def sizeHint(self):
        return QSize(200, 0)
