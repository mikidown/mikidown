#!/usr/bin/env python

import glob
import os
import sys
import unittest
from PyQt4.QtGui import QApplication, QIcon

import mikidown
from mikidown.mikiwindow import MikiWindow

app = QApplication(sys.argv)
path = os.path.join(os.getcwd(),
                    "test_notebook")
if not os.path.isdir(path):
    os.makedirs(path)
window = MikiWindow(notebookPath=path,
                    name="test")
window.show()
# app.exec_()


class Monolithic(unittest.TestCase):

    def step1(self):
        """ test newPage """
        window.notesTree.newPage('1')

    def step2(self):
        """ test delPage """
        item = window.notesTree.pagePathToItem('1')
        window.notesTree.delPage(item)

    def step3(self):
        """ clean up """
        for i in glob.glob("test_notebook/.indexdir/*"):
            os.remove(i)
        os.rmdir("test_notebook/.indexdir")
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

    def btestQuit(self):
        self.assertTrue(window.close())


def main():
    unittest.main()

if __name__ == '__main__':
    main()
