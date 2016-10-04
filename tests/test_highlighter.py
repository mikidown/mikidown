import sys
import unittest

from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QTextEdit, QApplication

from mikidown.highlighter import MikiHighlighter

app = QApplication(sys.argv)

TESTING_COLORS = [
    "#A40000".lower(),
    "#4E9A06".lower(),
    "#4E9A07".lower(),
    "#4E9A08".lower(),
    "#4E9A09".lower(),
    "#A40005".lower(),
    "#ff0037".lower(), #italic, not used
    "#888A85".lower(),
    "#888A86".lower(),
    "#F57900".lower(),
    "#F57901".lower(),
    "#204A87".lower(), #underline color, not used atm
    "#204A88".lower(),
    "#F57900".lower(),
    "#F57901".lower(),
    "#F5006E".lower(),
]

class HighlighterTest(unittest.TestCase):

    def setUp(self):
        self.editor = QTextEdit()
        self.highlighter = MikiHighlighter(
            parent=self.editor,
            color_settings=TESTING_COLORS,
        )

    def test_html_tag(self):
        self.check_highlight(
            '<div></div>',
            [
                (0, 11, TESTING_COLORS[0]),
            ]
        )

    def test_html_entity(self):
        self.check_highlight(
            '&amp;',
            [
                (0, 5, TESTING_COLORS[5]),
            ]
        )

    def test_html_comment(self):
        self.check_highlight(
            '<!-- hi -->',
            [
                (0, 11, TESTING_COLORS[6]),
            ]
        )

    def test_delete(self):
        self.check_highlight(
            '~~hi~~',
            [
                (0, 6, TESTING_COLORS[7]),
            ]
        )

    def test_insert(self):
        self.check_highlight(
            '__hi__',
            [
                # color for insert currently ignored
                #(0, 6, TESTING_COLORS[8]),
                (0, 6, "#000000"),
            ]
        )

    def test_strong(self):
        self.check_highlight(
            '**hi**',
            [
                (0, 6, TESTING_COLORS[9]),
            ]
        )

    def test_title_link(self):
        self.check_highlight(
            '[a](b)',
            [
                (0, 3, TESTING_COLORS[12]),
                # color for links ignored atm
                #(4, 1, TESTING_COLORS[11]),
                (4, 1, "#000000"),
            ]
        )

    def test_inline_links(self):
        self.check_highlight(
            '<https://ddg.gg>',
            [
                (0, 16, "#000000")
            ]
        )

        self.check_highlight(
            '<a@b.c>',
            [
                (0, 7, "#000000")
            ]
        )

    def test_headers(self):
        tests = [
            (
                '# hi',
                (0, 4, TESTING_COLORS[1]),
            ),
            (
                '## hi',
                (0, 5, TESTING_COLORS[2]),
            ),
            (
                '### hi',
                (0, 6, TESTING_COLORS[3]),
            ),
            (
                '#### hi',
                (0, 7, TESTING_COLORS[4]),
            ),
            (
                '##### hi',
                (0, 8, TESTING_COLORS[4]),
            ),
        ]

        for txt, exp in tests:
            self.check_highlight(txt, (exp,))

    def test_code_fence(self):
        self.check_highlight(
            '~~~ 1 + 2 ~~~',
            [
                (0, 13, TESTING_COLORS[14]),
            ]
        )

    def test_math_fence(self):
        self.check_highlight(
            '$$ 1 + 2 $$',
            [
                (0, 11, TESTING_COLORS[15]),
            ]
        )

    def check_highlight(self, test_text, expected):
        self.editor.setPlainText(test_text)

        doc = self.editor.document()
        block = doc.begin()

        # https://andrewwilkinson.wordpress.com/2011/02/16/unittesting-qsyntaxhighlighter/

        idx = 0

        while block.isValid():
            formats = block.layout().additionalFormats()
            for fmt in formats:
                color = fmt.format.foreground().color()
                self.assertEqual(
                    (
                        fmt.start,
                        fmt.length,
                        color.name(),
                    ),
                    expected[idx]
                )
                idx += 1

            block = block.next()

def main():
    unittest.main()

if __name__ == "__main__":
    main()
