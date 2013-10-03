import os
import re
import sys

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QApplication, QIcon

import mikidown.mikidown_rc
from mikidown.config import *
from mikidown.mikitray import MikiTray
from mikidown.mikiwindow import MikiWindow
from mikidown.mikibook import Mikibook

sys.path.append(os.path.dirname(__file__))


def main():

    # Instantiate a QApplication first.
    # Otherwise, Mikibook.create() won't function.
    app = QApplication(sys.argv)

    # Read notebookList, open the first notebook.
    notebooks = Mikibook.read()
    if len(notebooks) == 0:
        Mikibook.create()
        notebooks = Mikibook.read()

    settings = Setting(notebooks)
    # Initialize application and main window.
    icon = QIcon(":/icons/mikidown.svg")
    app.setWindowIcon(icon)
    window = MikiWindow(settings)
    window.show()
    window.restore()        # Restore after window show.
    tray = MikiTray(icon, window)
    tray.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
