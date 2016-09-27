# Mikidown

Master build status: [![master Build Status](https://travis-ci.org/ShadowKyogre/mikidown.svg?branch=master)](https://travis-ci.org/ShadowKyogre/mikidown)
Develop build status: [![develop Build Status](https://travis-ci.org/ShadowKyogre/mikidown.svg?branch=develop)](https://travis-ci.org/ShadowKyogre/mikidown)

**Mikidown** is a note taking application with markdown.

> Mikidown was inspired by [Zim] and based on [ReText]. The logo is derived from [markdown-mark].

Install mikidown with
 
    python3-pip install mikidown

Run mikidown without installing

    git clone https://github.com/shadowkyogre/mikidown.git
    cd mikidown
    ./mikidown.py

## Features 

- Edit markdown with live preview
- Switch between Edit/View/LiveEdit mode
- All notes in one place, with multiple notebooks support
- Page cross-link
- Import from plain text files, export to HTML, PDF
- Customise your note style (by editing CSS file)
- Spell check

## Dependencies

- Python.3+
- PyQt.5+
- python-markdown
- python-whoosh
- python-html2text ( Optional for HTML to markdown conversion, otherwise, formatted text is pasted as HTML )
- python-asciimathml ( Optional for asciimathml support )
    - The default version of python-asciimathml doesn't support Python 3.
    Please use the one from this repo: <https://github.com/mtahmed/python-asciimathml>
- python-pyenchant ( Optional for spell checking )
- slickpicker ( Optional for better color picking for mikidown highlighting colors )

## Beautiful notes powered by markdown

In case you are unfamiliar with markdown, you can use 
this file (**Help->README**) as a simple reference to 
basic markdown syntax. However, 
Its suggested to look at the complete [Markdown Syntax].

### Markdown extension

All python-markdown [extensions] are supported. To enable/disable extension, edit the `notebook.conf` file in your notebook folder.

    # notebook_folder/notebook.conf
    extensions=nl2br, strkundr, codehilite, fenced_code, headerid, headerlink, footnotes

### Mikidown Specific Syntax

1.  page cross link
    - `[text](/parentNode/childNode/pageName)`
    - `[text](/parentNode/childNode/pageName#anchor)`


2.  absolute and relative image path 
    - `![text](file:///home/user/pic.png)` 
    - `![text](pic.png)`     # path relative to notebook folder
    - `Ctrl + I` or **Edit -> Insert Image** will bring up an **insert image** dialog.

3.  ins/del/bold/italics
    - `~~delete~~`  will yield <del>delete</del>
    - `__insert__` will yield <ins>insert</ins>
    - `**strong**` will yield <strong>strong</strong>
    - `//emphasis//` will yield <em>emphasis</em>

## Contributors

[ShadowKyogre] and [more](https://github.com/shadowkyogre/mikidown/graphs/contributors)

[Fork and help] are much appreciated.

- [markdown-mark]: https://github.com/dcurtis/markdown-mark
- [Zim]: http://zim-wiki.org/
- [ReText]: http://sourceforge.net/p/retext/
- [Markdown Syntax]: http://daringfireball.net/projects/markdown/syntax
- [Fork and help]: https://github.com/shadowkyogre/mikidown
- [ShadowKyogre]: https://github.com/ShadowKyogre
- [extensions]: http://pythonhosted.org/Markdown/extensions/index.html

Want to help? Further details are in the CONTRIBUTING.md file.
