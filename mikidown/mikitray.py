"""
Mikidown tray icon module.
"""

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets



from collections import OrderedDict

class MikiTray(QtWidgets.QSystemTrayIcon):
    """MikiTray is the little icon on the "systemtray", and like a simple
       background app to show or launch a markdown book
    """
    DEFAULT_TIMEOUT = 4000

    def __init__(self, icon):
        super(MikiTray, self).__init__()

        ## set icon for systray and make it visible
        self.setIcon(icon)
        self.setVisible(True)

        ## Create the systray menu and dropdown
        self.menu = QtWidgets.QMenu()

        ## initialize its "pointers" to open windows
        self.registered_windows = OrderedDict([])

        ## The the Menu for le systray backend staff
        self.setContextMenu(self.menu)


        self.menu.addAction("Quit", self.on_quit)

        ## Fire up a welcome message after windows start a few secs later
        QtCore.QTimer.singleShot(1000, self.on_after)
        self.activated.connect(self.on_sys_tray_activated )



    def registerWindow(self, window):
        """create a handle to a qWidget/window in the mix"""
        if window not in self.registered_windows:
            action = self.menu.addAction(window.settings.notebookName)
            action.triggered.connect(window.toggleShow)
            self.registered_windows[window] = action
            window.tray = self

    def unregisterWindow(self, window):
        """removes a handle to a qWidget/window in the mix"""
        action = self.registered_windows.get(window, None)
        if action is not None:
            self.menu.removeAction(action)
            window.tray = None
            ## Does this kill in Qt also asks @pedromorgan
            del self.registered_windows[window]


    def on_quit(self):
        ## how dow we kill ?
        ## todo list definate
        print("quit")

    def on_after(self):
        self.showMessage("Welcome", ".. to mikidown", QtWidgets.QSystemTrayIcon.Information, self.DEFAULT_TIMEOUT)


    def on_sys_tray_activated(self, reason):
        pass
