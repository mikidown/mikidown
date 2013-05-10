#!/usr/bin/env python

import glob
import os
import sys
import unittest
from PyQt4.QtGui import QApplication, QIcon

import mikidown
from mikidown.mikiwindow import MikiWindow

def init():
    app = QApplication(sys.argv)
    window = MikiWindow(notebookPath="test_notebook",
                        name="test")
    window.show()
    sys.exit(app.exec_())

class InitTests(unittest.TestCase):

    def testInit(self):
        self.assertTrue(init)

    def tearDown(self):
        for i in glob.glob("test_notebook/.indexdir/*"):
            os.remove(i)
        os.rmdir("test_notebook/.indexdir")
        os.remove("test_notebook/notebook.conf")
        os.rmdir("test_notebook")


def main():
    unittest.main()

if __name__ == '__main__':
    main()
