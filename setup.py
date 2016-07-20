from distutils import log
from distutils.core import setup
from distutils.command.build import build
from distutils.command.sdist import sdist
from distutils.command.install_scripts import install_scripts


import glob
import os
import sys
from subprocess import check_call

from mikidown.config import __version__

# http://sourceforge.net/p/retext/git/ci/master/tree/setup.py
def build_translations():
    print('running build_translations')
    error = None
    try:
        check_call(('lrelease-qt5', 'mikidown.pro'))
    except Exception as e:
        error = e
    if error:
        print('Failed to build translations:', error) 

class miki_sdist(sdist):
    def run(self):
        build_translations()
        sdist.run(self)

class miki_build(build):
    def run(self):
        # Check the python version
        try:
            version_info = sys.version_info
            assert version_info > (3, 0)
        except:
            print('ERROR: mikidown needs python >= 3.0', file=sys.stderr)
            sys.exit(1)
        build.run(self)
        if not glob.glob(os.path.join('locale', '*.qm')):
            build_translations()

class miki_install_scripts(install_scripts):
    def run(self):
        import shutil
        install_scripts.run(self)
        for file in self.get_outputs():
            log.info('renaming %s to %s', file, file[:-3])
            shutil.move(file, file[:-3])

setup(
    name='mikidown',
    version=__version__,
    license = 'MIT',
    description = 'A note taking application, featuring markdown syntax',
    author = 'rnons',
    author_email = 'remotenonsense@gmail.com',
    maintainer='ShadowKyogre',
    maintainer_email='shadowkyogre.public@gmail.com',
    url = 'https://github.com/rnons/mikidown',
    scripts=['mikidown.py'],
    packages=['mikidown'],
    data_files=[('share/mikidown', ['README.mkd']), 
                ('share/mikidown', ['mikidown/notebook.css']), 
                ('share/mikidown', ['Changelog.md']), 
                ('share/mikidown/css', glob.glob("mikidown/css/*")), 
                ('share/icons/hicolor/scalable/apps', ['mikidown/icons/mikidown.svg']), 
                ('share/applications', ['mikidown.desktop']),
                ('share/mikidown/locale', glob.glob(os.path.join('locale', '*.qm'))),
                ],
    requires=['PyQt5', 'markdown', 'whoosh'],
    install_requires=['Markdown >= 2.3.1', 'Whoosh >= 2.5.2'],
    cmdclass={
        'sdist': miki_sdist,
        'build': miki_build,
        'install_scripts': miki_install_scripts
    },

    classifiers=[
        "Topic :: Text Editors :: Documentation",
        "Development Status :: 3 - Alpha",
        "Environment :: X11 Applications",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3"
    ]
)
