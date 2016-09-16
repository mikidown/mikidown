import unittest
import sys

from PyQt5.QtWidgets import QApplication, QTextEdit

import mikidown

from mikidown.findreplacedialog import FindReplaceDialog

app = QApplication(sys.argv)

class FindReplaceDialogTest(unittest.TestCase):
    def setUp(self):
        self.test_mkd = (
            '# A Sample Mini Diary\n'
            '## 2016-01-01\n\n'
            '* Here is a bulleted entry\n'
            '* And another\n'
            '* And yet another\n\n'
            '## 2016-02-01\n\n'
            '* Here is a bulleted entry\n'
            '* And another\n'
            '* And yet another\n\n'
        )
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.test_mkd)
        self.dialog = FindReplaceDialog(parent=self.text_edit)

    def test_find(self):
        # Text cursor positions are 1-based
        self.dialog.searchInput.setText("A Sample")
        self.dialog.find()

        doc_pos = self.text_edit.textCursor().position()

        self.assertEqual(doc_pos, 10)

    def test_replaceAll(self):
        self.dialog.searchInput.setText("2016")
        self.dialog.replaceInput.setText("2015")
        self.dialog.replaceAll()

        self.assertEqual(
            self.text_edit.toPlainText(),
            self.test_mkd.replace("2016", "2015")
        )

def main():
    unittest.main()

if __name__ == '__main__':
    main()
