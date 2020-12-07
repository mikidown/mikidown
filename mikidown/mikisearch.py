"""
Search module

Search results are displayed in a QWebView widget.
"""
from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets


class MikiSearch(QtWebEngineWidgets.QWebEngineView):

    def __init__(self, parent=None):
        super(MikiSearch, self).__init__(parent)
        self.parent = parent

        # TODO self.settings().clearMemoryCaches()
        self.flag = False
        self.link = None
        self.setMouseTracking(True)

        # So cant do this on webengine.. ;-( nmeeds javascript
        # TODO webengine self.settings().setUserStyleSheetUrl(
        #                 QtCore.QUrl('file://'+self.parent.settings.searchcssfile))
        #print(QtCore.QUrl('file://'+self.parent.settings.searchcssfile))
        self.page().linkHovered.connect(self.linkHovered)
        # TODO webengine self.page().setLinkDelegationPolicy(QtWebEngineWidgets.QWebEnginePage.DelegateAllLinks)
        # TODO webengine self.page().linkClicked.connect(self.linkClicked)

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
            QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), self.link)
        else:
            self.flag = False

    def mouseMoveEvent(self, event):
        if self.flag:
            QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), self.link)
        else:
            QtWidgets.QToolTip.hideText()
        QtWebKitWidgets.QWebView.mouseMoveEvent(self, event)

    def sizeHint(self):
        return QtCore.QSize(200, 0)
