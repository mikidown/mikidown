#!/usr/bin/env python3

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
from mikidown.utils import allMDExtensions, JSCRIPT_TPL
import shutil

app = QApplication(sys.argv)
# app.exec_()


class Monolithic(unittest.TestCase):

    def step0(self):
        print("\nStep 0: create notebook")

        path = os.path.join(os.getcwd(), "test_notebook")
        Mikibook.initialise("test", path)
        self.settings = Setting([["test", path]])
        self.window = MikiWindow(self.settings)
        self.window.show()

    def step1(self):
        print("\nStep 1: newPage")

        self.window.notesTree.newPage('pageOne')
        self.window.notesTree.newSubpage('subpageOne')
        
        itemOne = self.window.notesTree.pageToItem('pageOne')
        self.window.notesTree.setCurrentItem(itemOne)
        self.window.notesTree.newPage('pageTwo')

    def step2(self):
        print("\nStep 2: setText")
        
        self.window.liveView(True)
        self.window.notesEdit.setText("# head1\n\n"
                                      "## head2\n"
                                      "[subpageOne](pageOne/subpageOne)")
        self.window.saveCurrentNote()
        self.window.notesView.updateView()

        #self.window.notesView.setVisible(True)
        elemCol = self.window.notesView.page(
        ).mainFrame().findAllElements("a")
        element = elemCol.at(2)
        print(self.window.notesView.page().mainFrame().toHtml())
        print(element.attribute("href"))
        element.evaluateJavaScript("var evObj = document.createEvent('MouseEvents');evObj.initEvent( 'click', true, true );this.dispatchEvent(evObj);")

        noteName = self.window.notesTree.currentItem().text(0)
        self.assertEqual(noteName, "subpageOne")

    def step3(self):
        print("\nStep 3: page link")
        
        self.window.notesEdit.setText("[head2](pageTwo#head2)")
        self.window.saveCurrentNote()
        self.window.notesView.updateView()

        element = self.window.notesView.page(
        ).mainFrame().findFirstElement("a")
        element.evaluateJavaScript("var evObj = document.createEvent('MouseEvents');evObj.initEvent( 'click', true, true );this.dispatchEvent(evObj);")

        noteName = self.window.notesTree.currentItem().text(0)
        self.assertEqual(noteName, "pageTwo")

    def step4(self):
        print("\nStep 4: delPage")

        # This will delete both pageOne and subpageOne
        item = self.window.notesTree.pageToItem('pageOne')
        self.window.notesTree.delPage(item)

        item = self.window.notesTree.pageToItem('pageTwo')
        self.window.notesTree.delPage(item)

    def step5(self):
        print("Step 5: extension detection check")
        print("    Checking available modules first...")
        exts = allMDExtensions()
        if 'asciimathml' in exts:
            print("    asciimathml should be enabled in defaults since we found it")
            self.assertTrue('asciimathml' in self.settings.extensions)
            print("    did we auto-attach the configured javascript too?")
            self.assertTrue(JSCRIPT_TPL.format(self.settings.mathjax)[:-1] in self.window.notesView.page().mainFrame().toHtml())
        else:
            print("    asciimathml should not be enabled in defaults since we found it")
            self.assertFalse('asciimathml' in self.settings.extensions)
            print("    did we not auto-attach the configured javascript too?")
            self.assertFalse(JSCRIPT_TPL.format(self.settings.mathjax)[:-1] in self.window.notesView.page().mainFrame().toHtml())
        #print(exts)

    def step6(self):
        print("\nLast step: clean up")
        shutil.rmtree("test_notebook")

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
