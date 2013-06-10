#!/usr/bin/env python

import glob
import os
import sys
import unittest
from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QApplication, QIcon

import mikidown
from mikidown.mikiwindow import MikiWindow
from mikidown.mikibook import Mikibook
from mikidown.config import Setting

app = QApplication(sys.argv)
# app.exec_()


class Monolithic(unittest.TestCase):
    window = None
    def step0(self):
        print("\nStep 0: create notebook")
        gconf = os.path.join(os.getcwd(), "test.conf")
        gsettings = QSettings(gconf, QSettings.NativeFormat)
        path = os.path.join(os.getcwd(), "test_notebook")
        Mikibook.add("test", path)
        settings = Setting([["test", path]])
        Monolithic.window = MikiWindow(settings)
        Monolithic.window.show()

    def step1(self):
        print("\nStep 1: newPage")
        Monolithic.window.notesTree.newPage('1')

    def step2(self):
        print("\nStep 2: delPage")
        item = Monolithic.window.notesTree.pagePathToItem('1')
        Monolithic.window.notesTree.delPage(item)

    def step3(self):
        print("\nLast step: clean up")
        for i in glob.glob("test_notebook/.indexdir/*"):
            os.remove(i)
        os.rmdir("test_notebook/.indexdir")
        os.remove("test_notebook/notes.css")
        # os.remove("test_notebook/notebook.conf")
        os.rmdir("test_notebook")

    def steps(self):
        for name in sorted(dir(self)):
            if name.startswith("step"):
                yield name, getattr(self, name)

    def test_steps(self):
        for name, step in self.steps():
            try:
                step()
            except Exception as e:
                self.fail("{} failed ({}: {})".format(step, type(e), e))


def main():
    unittest.main()

if __name__ == '__main__':
    main()
