from PyQt4.QtCore import QDir, QUrl
from PyQt4.QtWebKit import QWebView, QWebPage
import markdown

class MikiView(QWebView):

    def __init__(self, parent=None):
        super(MikiView, self).__init__(parent)
        self.settings().clearMemoryCaches()
        notebookPath = QDir.currentPath()
        self.settings().setUserStyleSheetUrl(QUrl.fromLocalFile(notebookPath + '/notes.css'))
        self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)

