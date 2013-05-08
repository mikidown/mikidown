"""
Mikidown tray icon module.
"""

from PyQt4.QtGui import QSystemTrayIcon


class MikiTray(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super(MikiTray, self).__init__(parent)
        self.setIcon(icon)
        self.setVisible(True)
