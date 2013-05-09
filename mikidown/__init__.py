import os
import re
import sys

from PyQt4.QtGui import QApplication, QIcon

from mikidown.config import *
from mikidown.mikitray import MikiTray
from mikidown.mikiwindow import MikiWindow

sys.path.append(os.path.dirname(__file__))


def main():

    ''' Configuration. '''
    # Read notebooks info from global_settings
    global_settings = Default.global_settings
    notebooks = readListFromSettings(global_settings, 'notebookList')
    if len(notebooks) == 0:
        NotebookList.create(global_settings)
        notebooks = readListFromSettings(global_settings, 'notebookList')

    ''' Initialize application and main window. '''
    icon = QIcon("/usr/share/icons/hicolor/scalable/apps/mikidown.svg")
    app = QApplication(sys.argv)
    app.setWindowIcon(icon)
    window = MikiWindow(notebookPath=notebooks[0][1],
                        name=notebooks[0][0])
    window.show()
    tray = MikiTray(icon, window)
    tray.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
