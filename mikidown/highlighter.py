from mikidown import *
import re

class MikiHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(MikiHighlighter, self).__init__(parent)
        baseFontSize = 10
        NUM = 14
        self.patterns = []
        regexp = [0] * NUM
        font = [0]*NUM
        color = [0]*NUM
        # 0: html tags - <pre></pre>
        regexp[0] = '</?[0-z]+>'
        font[0] = QFont(None, baseFontSize, QFont.Bold)
        color[0] = QColor("#4E9A06")
        # 1: h1 - #
        regexp[1] = '^#[^#]+'
        color[1] = QColor("#4E9A06")
        font[1] = QFont(None, 5.0/3*baseFontSize, QFont.Bold)
        # 2: h2 - ##
        regexp[2] = '^##[^#]+'
        color[2] = QColor("#729FCF")
        font[2] = QFont(None, 1.5*baseFontSize, QFont.Bold)
        # 3: h3 - ###
        regexp[3] = '^###[^#]+'
        color[3] = QColor("#729FCF")
        font[3] = QFont(None, 4.0/3*baseFontSize, QFont.Bold)
        # 4: h4 and more - ####
        regexp[4] = '^####.+'
        color[4] = QColor("#729FCF")
        font[4] = QFont(None, baseFontSize, QFont.Bold)
        # 5: html symbols - &gt;
        regexp[5] = '&[^; ].+;'
        color[5] = QColor("#4E9A06")
        font[5] = QFont(None, baseFontSize, QFont.Bold)
        # 6: html comments - <!-- -->
        regexp[6] = '<!--.+-->'
        color[6] = QColor("#888A85")
        font[6] = QFont(None, baseFontSize, -1)
        # 7: delete - ~~delete~~
        regexp[7] = '~~[^~~]*~~'
        color[7] = QColor("#888A85")
        font[7] = QFont(None, baseFontSize, -1)
        # 8: insert - __insert__
        regexp[8] = '__[^__]*__'
        font[8] = QFont(None, baseFontSize, -1)
        font[8].setUnderline(True)
        # 9: strong - **strong**
        regexp[9] = '\*\*[^**]*\*\*'
        color[9] = QColor("#F57900")
        font[9] = QFont(None, baseFontSize, QFont.Bold)
        # 10: emphasis - //emphasis//
        regexp[10] = r'//[^//\(\)]*//'
        color[10] = QColor("#F57900")
        font[10] = QFont(None, baseFontSize, -1, True)
        # 11: links - (links) after [] or links after []:
        regexp[11] = r'(?<=(\]\())[^\(\)]*(?=\))'
        font[11] = QFont(None, baseFontSize, -1, True)
        font[11].setUnderline(True)
        # 12: link/image references - [] or ![]
        regexp[12] = r'!?\[[^\[\]]*\]'
        color[12] = QColor("#CD5C5C")
        font[12] = QFont(None, baseFontSize, -1)
        # 13: blockquotes and lists -  > or - or *
        regexp[13] = r'(^>+)|(^- )|(^\* )'
        color[13] = QColor("#F57900")
        font[13] = QFont(None, baseFontSize, -1)
        for i in range(NUM):
            p = re.compile(regexp[i])
            f = QTextCharFormat()
            if font[i] != 0:
                f.setFont(font[i])
            if color[i] != 0:
                f.setForeground(color[i])
            self.patterns.append((p, f))
    
    def highlightBlock(self, text):
        for i in range(0,len(self.patterns)):
            p = self.patterns[i]
            for match in p[0].finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), p[1])
