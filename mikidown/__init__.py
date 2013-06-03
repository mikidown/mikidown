import os
import re
import sys

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QApplication, QIcon

from mikidown.config import *
from mikidown.mikitray import MikiTray
from mikidown.mikiwindow import MikiWindow
from mikidown.mikibook import NotebookList

sys.path.append(os.path.dirname(__file__))


def main():

    # Instantiate a QApplication first.
    # Otherwise, NotebookList.create() won't function.
    app = QApplication(sys.argv)

    # ~/.config/mikidown/mikidown.conf
    global_settings = QSettings('mikidown', 'mikidown')
    
    # Read notebookList, open the first notebook.
    notebooks = readListFromSettings(global_settings, 'notebookList')
    if len(notebooks) == 0:
        NotebookList.create(global_settings)
        notebooks = readListFromSettings(global_settings, 'notebookList')

    settings = Setting(notebookPath = notebooks[0][1],
                       notebookName = notebooks[0][0])
    # Initialize application and main window.
    icon = QIcon("/usr/share/icons/hicolor/scalable/apps/mikidown.svg")
    app.setWindowIcon(icon)
    window = MikiWindow(settings)
    window.show()
    window.restore()        # Restore after window show.
    tray = MikiTray(icon, window)
    tray.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
