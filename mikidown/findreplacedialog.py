from PyQt4.QtCore import *
from PyQt4.QtGui import *
import re

class FindReplaceDialog(QDialog):
  def __init__(self, parent = None):
    super(FindReplaceDialog, self).__init__(parent)
    grid = QGridLayout(self)
    
    self.searchInput = QLineEdit(self)
    self.replaceInput = QLineEdit(self)
    
    self.matchCase = QCheckBox(self.tr('Match case'), self)
    self.wholeWords = QCheckBox(self.tr('Whole words'), self)
    self.reCheck = QCheckBox(self.tr('Regex'), self)

    self.nextButton = QPushButton(self.tr("Next"),self)
    self.prevButton = QPushButton(self.tr("Previous"),self)
    self.replaceButton = QPushButton(self.tr("Replace"),self)
    self.replaceAllButton = QPushButton(self.tr("Replace All"),self)
    
    self.nextButton.clicked.connect(self.find)
    self.prevButton.clicked.connect(lambda: self.find(back = True))
    self.replaceButton.clicked.connect(self.replace)
    self.replaceAllButton.clicked.connect(self.replaceAll)
    self.searchInput.returnPressed.connect(self.find)
    self.replaceInput.returnPressed.connect(self.replace)
    
    grid.addWidget(QLabel(self.tr("Search")),0,0)
    grid.addWidget(QLabel(self.tr("    Options")),1,0)
    grid.addWidget(QLabel(self.tr("Replace")),2,0)
    
    grid.addWidget(self.searchInput,0,1)
    grid.addWidget(self.nextButton,0,2)
    grid.addWidget(self.prevButton,0,3)
    
    grid.addWidget(self.matchCase,1,1)
    grid.addWidget(self.wholeWords,1,2)
    grid.addWidget(self.reCheck,1,3)
    
    grid.addWidget(self.replaceInput,2,1)
    grid.addWidget(self.replaceButton,2,2)
    grid.addWidget(self.replaceAllButton,2,3)
  
  def replace(self,autofind = True):
    if autofind:
      self.find()
    contents = self.parent().textCursor().selectedText()

    if self.reCheck.isChecked():
      search_term = self.searchInput.text()
    else:
      search_term = re.escape(self.searchInput.text())

    replace_term = self.replaceInput.text()
    flags = 0
    if not self.matchCase.isChecked():
      flags = re.IGNORECASE
    if self.wholeWords.isChecked():
      search_term = r'\b{}\b'.format(search_term)

    contents = re.sub(search_term,replace_term,contents,flags=flags)
    self.parent().textCursor().insertText(contents)
  
  def replaceAll(self):
    self.parent().selectAll()
    self.replace(autofind = False)
  
  def find(self, back = False):
    flags = 0x0000
    if self.reCheck.isChecked():
      search_term = QRegExp(self.searchInput.text())
    else:
      search_term = self.searchInput.text()
    if self.matchCase.isChecked():
      flags |= QTextDocument.FindCaseSensitively
    elif self.reCheck.isChecked():
        search_term.setCaseSensitivity(Qt.CaseInsensitive)
    if self.wholeWords.isChecked():
      flags |= QTextDocument.FindWholeWords
    if back:
      flags |= QTextDocument.FindBackward
    start_here = self.parent().textCursor()
    if flags:
      cursor = self.parent().document().find(search_term, start_here, options = flags)
    else:
      cursor = self.parent().document().find(search_term, start_here)
    self.parent().setTextCursor(cursor)
