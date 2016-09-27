"""
AutoTextDirection Extension for Python-Markdown
========================================

With AutoTextDirection, #Header will become

    <h1 id="header" dir="auto">Header</h1>
"""

from markdown import Extension
from markdown.treeprocessors import Treeprocessor
from markdown.util import etree

import unicodedata as UD


class AutoTextDirectionTreeprocessor(Treeprocessor):
    """ Insert anchors to headers. """
    BLOCK_LVL_ELS={'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol'}
    def run(self, doc):
        for elem in doc.getiterator():
            if elem.tag in AutoTextDirectionTreeprocessor.BLOCK_LVL_ELS:
                # be sure to set the text properly to handle
                # http://dev.w3.org/html5/spec-preview/global-attributes.html#the-dir-attribute
                # if there are both ltr and rtl charas, force to ltr
                #print(elem.tag)
                if elem.text is not None:
                    #for child in elem.itertext():
                    #    print(child)
                    elem.set('dir', self._check_true_dir(elem.text))
                    #print("---", elem.tag, list(elem.iter()))
                else:
                    elem.set('dir', 'auto')
                #print("---")

    # http://stackoverflow.com/questions/17684990/python-testing-for-utf-8-character-in-string
    def _check_true_dir(self, text):
        is_rtl = False
        is_ltr = False
        quoted_text = False

        last_inline_html_char_pos = text.rfind(">")
        if last_inline_html_char_pos > -1:
            it_here = text[last_inline_html_char_pos+1:]
        else:
            it_here = text

        for ch in it_here:
            res = UD.bidirectional(ch)
            if ch == '"':
                quoted_text = not quoted_text
            elif not quoted_text and res in {'R', 'AL'}:
                is_rtl = True
            elif not quoted_text and res == 'L':
                is_ltr = True

        #print(text, it_here, is_rtl, is_ltr)

        if is_rtl:
            return 'rtl'
        elif is_ltr:
            return 'ltr'
        else:
            return 'auto'


class AutoTextDirectionExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        self.processor = AutoTextDirectionTreeprocessor()
        self.processor.md = md
        md.treeprocessors.add('autotextdir', self.processor, '_begin')


def makeExtension(configs=None):
    configs = configs or {}
    return AutoTextDirectionExtension(configs=configs)
