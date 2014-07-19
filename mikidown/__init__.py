import argparse
import os
import re
import sys

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QApplication, QIcon, QMessageBox

import mikidown.mikidown_rc
from .config import Setting
from .generator import Generator
from .mikitray import MikiTray
from .mikiwindow import MikiWindow
from .mikibook import Mikibook
from .sandbox import Sandbox

sys.path.append(os.path.dirname(__file__))

# http://code.activestate.com/recipes/578453-python-single-instance-cross-platform/
def set_exit_handler(func):
    if os.name == "nt":
        try:
            import win32api
            win32api.SetConsoleCtrlHandler(func, True)
        except ImportError:
            version = ".".join(map(str, sys.version_info[:2]))
            raise Exception("pywin32 not installed for Python " + version)
    else:
        import signal
        signal.signal(signal.SIGTERM, func)

def main():

    parser = argparse.ArgumentParser(description='A note taking application, featuring markdown syntax')
    subparsers = parser.add_subparsers(dest='command')
    parser_generate = subparsers.add_parser('generate',
        help='generate a static html site from notebook')
    parser_preview = subparsers.add_parser('preview',
        help='automatically regenerate html site when notes modified')
    parser_preview.add_argument('-p', '--port', dest='port',
        type=int, help='port number')
    parser_sandbox = subparsers.add_parser('sandbox',
        help='for test purpose, all notes will be lost when exit')
    args = parser.parse_args()

    if args.command == 'generate':
        generator = Generator(os.getcwd())
        generator.generate()
        sys.exit(0)
    elif args.command == 'sandbox':
        app = QApplication(sys.argv)
        sandbox = Sandbox()
        app.aboutToQuit.connect(sandbox.cleanUp)
        sys.exit(app.exec_())
    elif args.command == 'preview':
        generator = Generator(os.getcwd())
        if args.port:
            generator.preview(args.port)
        else:
            generator.preview()


    # Instantiate a QApplication first.
    # Otherwise, Mikibook.create() won't function.
    app = QApplication(sys.argv)

    # Read notebookList, open the first notebook.
    notebooks = Mikibook.read()
    if len(notebooks) == 0:
        Mikibook.create()
        notebooks = Mikibook.read()

    if len(notebooks) != 0:
        if os.path.exists(Mikibook.lockpath):
            ret = QMessageBox.question(None, "mikidown - lock file exists", ("It looks like the lock file for "
                "mikidown already exists. Is mikidown currently running? "
                "Click no to remove the lock file before rerunning mikidown."), buttons=QMessageBox.Yes|QMessageBox.No)
            if ret == QMessageBox.Yes:
                os.remove(Mikibook.lockpath)
                sys.exit(0)
            else:
                sys.exit(1)
            exit_code = app.exec_()
        else:
            print("Applying single instance per user lock.")
            os.open(Mikibook.lockpath, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        settings = Setting(notebooks)
        # Initialize application and main window.
        icon = QIcon(":/icons/mikidown.svg")
        app.setWindowIcon(icon)
        window = MikiWindow(settings)
        window.show()
        window.restore()        # Restore after window show.
        tray = MikiTray(icon, window)
        tray.show()

        def cleanup(signum, frame):
            #we need to do this to remove the lock at the end
            app.closeAllWindows()

        set_exit_handler(cleanup)
        exit_code = app.exec_()

        print("Removing single instance per user lock.")
        if os.path.exists(Mikibook.lockpath):
            os.remove(Mikibook.lockpath)
        sys.exit(exit_code)

if __name__ == '__main__':
    main()
