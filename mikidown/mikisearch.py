"""
Search module

Search results are displayed in a QWebView widget.
"""

from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QCursor, QToolTip
from PyQt4.QtWebKit import QWebView, QWebPage


class MikiSearch(QWebView):

    def __init__(self, parent=None):
        super(MikiSearch, self).__init__(parent)
        self.settings().clearMemoryCaches()
        self.flag = False
        self.link = None
        self.setMouseTracking(True)
        self.page().linkHovered.connect(self.linkHovered)
        self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        #self.notesView.page().linkClicked.connect(self.linkClicked)

    def linkHovered(self, link, title, textContent):
        #self.setToolTip(link)
        if link:
            self.flag = True
            self.link = link
            QToolTip.showText(QCursor.pos(), self.link)
        else:
            self.flag = False

    def mouseMoveEvent(self, event):
        # ToFix: Tooltip disappear too soon.
        if self.flag:
            QToolTip.showText(QCursor.pos(), self.link)
        else:
            QToolTip.hideText()
        QWebView.mouseMoveEvent(self, event)

