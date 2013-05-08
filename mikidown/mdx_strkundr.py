import markdown

DEL_RE = r'(~~)(.*?)~~'
INS_RE = r'(__)(.*?)__'
STRONG_RE = r'(\*\*)(.*?)\*\*'
EMPH_RE = r'(//)(.*?)//'

# http://achinghead.com/python-markdown-changing-bold-italics.html


class StrkUndrExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        del_tag = markdown.inlinepatterns.SimpleTagPattern(DEL_RE, 'del')
        md.inlinePatterns.add('del', del_tag, '>not_strong')
        ins_tag = markdown.inlinepatterns.SimpleTagPattern(INS_RE, 'ins')
        md.inlinePatterns.add('ins', ins_tag, '>del')
        strong_tag = markdown.inlinepatterns.SimpleTagPattern(
            STRONG_RE, 'strong')
        md.inlinePatterns['strong'] = strong_tag
        emph_tag = markdown.inlinepatterns.SimpleTagPattern(EMPH_RE, 'em')
        md.inlinePatterns['emphasis'] = emph_tag
        del md.inlinePatterns['strong_em']
        del md.inlinePatterns['emphasis2']


def makeExtension(configs=None):
    return StrkUndrExtension(configs=configs)
