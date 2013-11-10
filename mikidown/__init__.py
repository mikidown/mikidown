import argparse
import os
import re
import sys

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QApplication, QIcon

import mikidown.mikidown_rc
from .config import *
from .generator import Generator
from .mikitray import MikiTray
from .mikiwindow import MikiWindow
from .mikibook import Mikibook
from .sandbox import Sandbox

sys.path.append(os.path.dirname(__file__))


def main():

    parser = argparse.ArgumentParser(description='A note taking application, featuring markdown syntax')
    subparsers = parser.add_subparsers(dest='command')
    parser_generate = subparsers.add_parser('generate', help='generate a static html site from notebook')
    parser_generate = subparsers.add_parser('sandbox', help='get a feel of mikidown, all notes will be lost when exit')
    args = parser.parse_args()

    if args.command == 'generate':
        generator = Generator(os.getcwd())
        generator.generate()
        sys.exit(0)
    elif args.command == 'sandbox':
        app = QApplication(sys.argv)
        sandbox = Sandbox()
        sandbox.newPage()
        sandbox.setText()
        sandbox.pageLink()
        sandbox.delPage()
        sandbox.window.readmeHelp()
        print("Start manual testing in sandbox")
        app.aboutToQuit.connect(sandbox.cleanUp)
        sys.exit(app.exec_())


    # Instantiate a QApplication first.
    # Otherwise, Mikibook.create() won't function.
    app = QApplication(sys.argv)

    # Read notebookList, open the first notebook.
    notebooks = Mikibook.read()
    if len(notebooks) == 0:
        Mikibook.create()
        notebooks = Mikibook.read()

    if len(notebooks) != 0:
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
