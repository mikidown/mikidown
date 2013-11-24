import re

from PyQt4.QtGui import QSyntaxHighlighter, QColor, QFont, QTextCharFormat
from PyQt4.QtCore import Qt
from .mdx_strkundr import DEL_RE, INS_RE, STRONG_RE, EMPH_RE


class MikiHighlighter(QSyntaxHighlighter):

    WORDS = r'(?iu)[\w\']+'

    def __init__(self, parent=None):
        super(MikiHighlighter, self).__init__(parent)
        baseFontSize = 12
        NUM = 15
        self.patterns = []
        regexp = [0] * NUM
        font = [0]*NUM
        color = [0]*NUM
        # 0: html tags - <pre></pre>
        regexp[0] = '</?[^>]+>'
        font[0] = QFont("monospace", baseFontSize, -1)
        color[0] = QColor("#A40000")
        # 1: h1 - #
        regexp[1] = '^#[^#]+'
        color[1] = QColor("#4E9A06")
        font[1] = QFont("decorative", 2*baseFontSize, QFont.Bold)
        # 2: h2 - ##
        regexp[2] = '^##[^#]+'
        color[2] = QColor("#4E9A06")
        font[2] = QFont("serif", 5.0/3*baseFontSize, QFont.Bold)
        # 3: h3 - ###
        regexp[3] = '^###[^#]+'
        color[3] = QColor("#4E9A06")
        font[3] = QFont("serif", 4.0/3*baseFontSize, QFont.Bold)
        # 4: h4 and more - ####
        regexp[4] = '^####.+'
        color[4] = QColor("#4E9A06")
        font[4] = QFont("serif", baseFontSize, QFont.Bold)
        # 5: html symbols - &gt;
        regexp[5] = '&[^; ].+;'
        color[5] = QColor("#A40000")
        font[5] = QFont("monospace", baseFontSize, -1)
        # 6: html comments - <!-- -->
        regexp[6] = '<!--.+-->'
        color[6] = QColor("#888A85")
        font[6] = QFont(None, baseFontSize, -1)
        # 7: delete - ~~delete~~
        regexp[7] = DEL_RE
        color[7] = QColor("#888A85")
        font[7] = QFont(None, baseFontSize, -1)
        # 8: insert - __insert__
        regexp[8] = INS_RE
        font[8] = QFont(None, baseFontSize, -1)
        font[8].setUnderline(True)
        # 9: strong - **strong**
        regexp[9] = STRONG_RE
        color[9] = QColor("#F57900")
        font[9] = QFont(None, baseFontSize, QFont.Bold)
        # 10: emphasis - //emphasis//
        regexp[10] = EMPH_RE
        color[10] = QColor("#F57900")
        font[10] = QFont(None, baseFontSize, -1, True)
        # 11: links - (links) after [] or links after []:
        regexp[11] = r'(?<=(\]\())[^\(\)]*(?=\))'
        font[11] = QFont(None, baseFontSize, -1, True)
        font[11].setUnderline(True)
        #.setUnderlineColor("#204A87")
        # 12: link/image references - [] or ![]
        regexp[12] = r'!?\[[^\[\]]*\]'
        color[12] = QColor("#204A87")
        font[12] = QFont(None, baseFontSize, -1)
        # 13: blockquotes and lists -  > or - or *
        regexp[13] = r'(^>+)|(^- )|(^\* )'
        color[13] = QColor("#F57900")
        font[13] = QFont(None, baseFontSize, -1)
        # 14: fence - ``` or ~~~
        regexp[14] = '^(?:~{3,}|`{3,}).*$'
        color[14] = QColor("#F57900")
        font[14] = QFont(None, baseFontSize, QFont.Bold)
        for i in range(NUM):
            p = re.compile(regexp[i])
            f = QTextCharFormat()
            if font[i] != 0:
                f.setFont(font[i])
            if color[i] != 0:
                f.setForeground(color[i])
            self.patterns.append((p, f))
        self.speller = parent.speller

        fenced_font = QFont("monospace", baseFontSize, -1)
        self.fenced_block = re.compile("^(?:~{3,}|`{3,}).*$")
        self.fenced_format = QTextCharFormat()
        self.fenced_format.setFont(fenced_font)


    def highlightSpellcheck(self, text):
        for word_object in re.finditer(self.WORDS, str(text)):
            if not word_object.group():
                # don't bother with empty words
                continue
            if self.speller and not self.speller.check(word_object.group()):
                current_format = self.format(word_object.start())
                current_format.setUnderlineColor(Qt.red)
                current_format.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)
                self.setFormat(word_object.start(),
                    word_object.end() - word_object.start(), current_format)

    def highlightBlock(self, text):
        # highlight patterns
        for i in range(0, len(self.patterns)):
            p = self.patterns[i]
            for match in p[0].finditer(text):
                self.setFormat(
                    match.start(), match.end() - match.start(), p[1])

        # escape highlights in fenced_block
        m = self.fenced_block.match(text)
        self.setCurrentBlockState(0)
        if self.previousBlockState() != 1:
            if m:
                self.setCurrentBlockState(1)
        else:
            if m:
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(1)
                self.setFormat(0, len(text), self.fenced_format)
        self.highlightSpellcheck(text)

