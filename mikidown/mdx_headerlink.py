"""
HeaderLink Extension for Python-Markdown
========================================

!!HeaderID extension must be enabled to use this!!

With HeaderId, #Header will become

    <h1 id="header">Header</h1>

With HeaderLink, #Header will become

    <h1 id="header">Header<a class="headerlink" href="#header">¶</a></h1>
"""

from markdown import Extension
from markdown.treeprocessors import Treeprocessor
from markdown.util import etree


class HeaderLinkTreeprocessor(Treeprocessor):
    """ Insert anchors to headers. """

    def run(self, doc):
        for elem in doc.getiterator():
            if elem.tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                if "id" in elem.attrib:
                    id = elem.get('id')
                    a = etree.SubElement(elem, "a")
                    a.set('class', 'headerlink')
                    a.set('href', '#' + id)
                    a.text = '¶'


class HeaderLinkExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        self.processor = HeaderLinkTreeprocessor()
        self.processor.md = md
        md.treeprocessors.add('headerlink', self.processor, '>headerid')


def makeExtension(configs=None):
    return HeaderLinkExtension(configs=configs)
