import os
import shutil
from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QApplication

from .mikiwindow import MikiWindow
from .mikibook import Mikibook
from .config import Setting


class Sandbox():

    def __init__(self):
        path = os.path.join(os.getcwd(), "test_notebook").replace(os.sep, '/')
        if os.path.exists(path):
            shutil.rmtree(path)
        Mikibook.initialise("test", path)
        settings = Setting([["test", path]])
        self.window = MikiWindow(settings)
        self.window.show()

        print("...Create notebook works")

        self.newPage()
        self.setText()
        self.pageLink()
        self.delPage()
        self.window.readmeHelp()
        print("Start manual testing in sandbox")

    def newPage(self):
        self.window.notesTree.newPage('pageOne')
        self.window.notesTree.newSubpage('subpageOne')

        itemOne = self.window.notesTree.pageToItem('pageOne')
        self.window.notesTree.setCurrentItem(itemOne)
        self.window.notesTree.newPage('pageTwo')

        print("...newPage works")

    def setText(self):
        self.window.liveView(True)
        self.window.notesEdit.setText("# head1\n\n"
                                      "## head2\n"
                                      "[subpageOne](pageOne/subpageOne)")
        self.window.notesEdit.document().setModified() #isn't flagged as modified if programatically changed
        self.window.saveCurrentNote()
        self.window.notesView.updateView()

        #self.window.notesView.setVisible(True)
        elemCol = self.window.notesView.page(
        ).mainFrame().findAllElements("a")
        element = elemCol.at(2)
        # see http://stackoverflow.com/questions/1219880/how-to-follow-a-link-in-qwebkit
        # for more info
        element.evaluateJavaScript("var evObj = document.createEvent('MouseEvents');evObj.initEvent( 'click', true, true );this.dispatchEvent(evObj);")

        noteName = self.window.notesTree.currentItem().text(0)

        assert(noteName == "subpageOne")
        print("...setText works")

    def pageLink(self):
        self.window.notesEdit.setText("[head2](pageTwo#head2)")
        self.window.notesEdit.document().setModified() #isn't flagged as modified if programatically changed
        self.window.saveCurrentNote()
        self.window.notesView.updateView()

        element = self.window.notesView.page(
        ).mainFrame().findFirstElement("a")
        element.evaluateJavaScript("var evObj = document.createEvent('MouseEvents');evObj.initEvent( 'click', true, true );this.dispatchEvent(evObj);")

        noteName = self.window.notesTree.currentItem().text(0)
        assert(noteName == "pageTwo")

        print("...pageLink works")

    def delPage(self):
        # This will delete both pageOne and subpageOne
        item = self.window.notesTree.pageToItem('pageOne')
        self.window.notesTree.delPage(item)

        item = self.window.notesTree.pageToItem('pageTwo')
        self.window.notesTree.delPage(item)

        print("...delPage works")

    def cleanUp(self):
        """ When quitting mikidown, the whooshProcess may take time to finish.
        Terminate whooshProcess to ensure shutil.rmtree success.
        """
        shutil.rmtree("test_notebook")
        print("...Cleaned up")
