# Mikidown Changelogs

## Version 0.3.0

- Notebook folder redesigned, see [#23]
        // notebook.conf attachments/ css/ notes/ _site/ //

- When attachment (image or document) is inserted, it is saved into **attachment/** folder
- Spell checking support with enchant, see [#24]
        new optional dependencies: [pyenchant]

- A simple static site generator incorporated

        mikidown generate
        mikidown preview


[#23]: https://github.com/rnons/mikidown/issues/23
[#24]: https://github.com/rnons/mikidown/issues/24
[pyenchant]: https://pypi.python.org/pypi/pyenchant
