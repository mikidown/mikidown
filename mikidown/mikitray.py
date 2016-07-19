"""
Mikidown tray icon module.
"""

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets
"""
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QMenu, QSystemTrayIcon
"""

from collections import OrderedDict

class MikiTray(QtWidgets.QSystemTrayIcon):

    def __init__(self, icon):
        super(MikiTray, self).__init__()
        self.setIcon(icon)
        self.setVisible(True)
        self.menu = QtWidgets.QMenu()
        self.registered_windows = OrderedDict([])

        #menu.addAction(parent.actions.get('quit'))
        self.setContextMenu(self.menu)

    def registerWindow(self, window):
        if window not in self.registered_windows:
            action = self.menu.addAction(window.settings.notebookName)
            action.triggered.connect(window.toggleShow)
            self.registered_windows[window] = action
            window.tray = self

    def unregisterWindow(self, window):
        action = self.registered_windows.get(window, None)
        if action is not None:
            self.menu.removeAction(action)
            window.tray = None
            del self.registered_windows[window]
