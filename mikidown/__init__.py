import argparse
import os
import re
import sys
import signal

sys.path.append(os.path.dirname(__file__) + "/../")
sys.path.append(os.path.dirname(__file__))


from PyQt5 import QtCore, QtGui, QtWidgets

#from Qt.QtCore import QSettings, QTranslator, QLocale
#from Qt.QtGui import QApplication, QIcon, QMessageBox

import mikidown.mikidown_rc

from .config import Setting
from .generator import Generator
from .mikitray import MikiTray
from .mikiwindow import MikiWindow
from .mikibook import Mikibook
from .sandbox import Sandbox
from .utils import confirmAction


# http://code.activestate.com/recipes/578453-python-single-instance-cross-platform/

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
        app = QtWidgets.QApplication(sys.argv)
        translator = QtCore.QTranslator()
        tpath = "locale/mikidown_{}.qm".format(QtCore.QLocale.system().name())
        full_tpath = os.path.join("/usr/share/mikidown", tpath).replace(os.sep, "/")
        if not os.path.exists(full_tpath):
            full_tpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), tpath).replace(os.sep,'/')
        translator.load(full_tpath)
        app.installTranslator(translator)
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
    app = QtWidgets.QApplication(sys.argv)
    translator = QtCore.QTranslator()
    tpath = "locale/mikidown_{}.qm".format(QtCore.QLocale.system().name())
    print(tpath)
    full_tpath = os.path.join("/usr/share/mikidown", tpath).replace(os.sep, "/")
    if not os.path.exists(full_tpath):
        full_tpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), tpath).replace(os.sep,'/')
    translator.load(full_tpath)
    app.installTranslator(translator)
    print(sys.argv)

    # Read notebookList, open the first notebook.
    notebooks = Mikibook.read()
    if not notebooks:
        Mikibook.create()
        notebooks = Mikibook.read()

    if notebooks:
        #"""
        if os.path.exists(Mikibook.lockpath) and args.command != 'index':
            ret = confirmAction(
                    "mikidown - lock file exists",
                    (
                        "It looks like the lock file for "
                        "mikidown already exists. Is mikidown currently running? "
                        "Click no to remove the lock file before rerunning mikidown."
                    )
                )
            if ret == QtWidgets.QMessageBox.Yes:
                sys.exit(1)
            else:
                os.remove(Mikibook.lockpath)
                sys.exit(0)
            exit_code = app.exec_()
        else:
            print("Applying single instance per user lock.")
            lock_fh = os.open(Mikibook.lockpath, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        #"""
        
        settings = Setting(notebooks)
        # Initialize application and main window.
        icon = QtGui.QIcon(":/icons/mikidown.svg")
        app.setWindowIcon(icon)

        tray = MikiTray(icon)
        tray.show()

        MikiWindow.postInit.append(tray.registerWindow)
        MikiWindow.postClose.append(tray.unregisterWindow)

        window = MikiWindow(settings)
        window.show()
        window.restore()        # Restore after window show.

        #"""
        def cleanup(signum, frame):
            #we need to do this to remove the lock at the end
            app.closeAllWindows()

        if args.command:
            signal.signal(signal.SIGTERM, cleanup)
        #"""
        exit_code = app.exec_()

        #"""
        print("Removing single instance per user lock.")
        if os.path.exists(Mikibook.lockpath) and args.command != 'index':
            os.close(lock_fh)
            os.remove(Mikibook.lockpath)
        #"""
        sys.exit(exit_code)

if __name__ == '__main__':
    main()
