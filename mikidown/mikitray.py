"""
Mikidown tray icon module.
"""

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QMenu, QSystemTrayIcon


class MikiTray(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super(MikiTray, self).__init__(parent)
        self.parent = parent
        self.setIcon(icon)
        self.setVisible(True)

        menu = QMenu()
        menu.addAction(parent.actions.get('quit'))
        self.setContextMenu(menu)
        self.activated.connect(self.toggleShow)

    def toggleShow(self, reason):
        """ Left click tray icon to toggle the display of MainWindow. 
        """
        if reason != QSystemTrayIcon.Trigger:
            return
        s = self.parent.windowState() 
        if self.parent.isVisible():
            if s == Qt.WindowMinimized:
                self.parent.showNormal()
                self.parent.show()
            else:
                self.parent.showMaximized
                self.parent.hide()
        else:
            self.parent.show()
