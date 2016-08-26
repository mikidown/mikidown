import unittest
import sys

from PyQt5.QtWidgets import QApplication

import mikidown

from mikidown.mikitree import TocTree
from mikidown.utils import parseHeaders

app = QApplication(sys.argv)

def flattenTree(root, depth=0):
    yield depth, root
    for i in range(root.childCount()):
        child = root.child(i)
        yield from flattenTree(child, depth=depth+1)

class TOCTest(unittest.TestCase):
    def setUp(self):
        self.test_mkd = (
            '# Title\n'
            '## Subtitle\n'
            '### Subtitle 2\n'
            '# Title 2\n'
        )

    def test_parseHeaders(self):
        expected = [
            (1, ' Title', 0, 'title'),
            (2, ' Subtitle', 8, 'subtitle'),
            (3, ' Subtitle 2', 20, 'subtitle-2'),
            (1, ' Title 2', 35, 'title-2'),
        ]
        self.assertEqual(parseHeaders(self.test_mkd), expected)

    def test_updateToc(self):
        expected = [
            (1, ' Title', 0, 'title'),
            (2, ' Subtitle', 8, 'subtitle'),
            (3, ' Subtitle 2', 20, 'subtitle-2'),
            (1, ' Title 2', 35, 'title-2'),
        ]
        test_widget = TocTree()
        test_widget.updateToc('TOC Unit Test', expected)
        test_widget.show()

        root = test_widget.invisibleRootItem().child(0)
        tree_iter = flattenTree(root)
        next(tree_iter)

        results = [
           (
                # depth in tree
                lvl,
                # TOC friendly label
                item.text(0),
                # byte position in file
                int(item.text(1)),
                # anchor for render view
                item.text(2)
            )
            for (lvl, item) in tree_iter
        ]

        self.assertEqual(results, expected)

def main():
    unittest.main()

if __name__ == '__main__':
    main()
