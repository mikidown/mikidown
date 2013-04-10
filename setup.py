from distutils.core import setup
import glob

setup(name = 'mikidown',
	  version = '0.1.6',
	  scripts = ['mikidown/scripts/mikidown'],
	  packages = ['mikidown'],
	  data_files = [ ('share/mikidown', ['README.mkd'])
                   , ('share/mikidown', ['mikidown/notes.css'])
                   , ('share/mikidown/css', glob.glob("mikidown/css/*"))
                   , ('share/icons/hicolor/scalable/apps', ['mikidown.svg'])
                   , ('share/applications', ['mikidown.desktop'])
                   ],
	  requires = ['PyQt', 'markdown']
	  )
