from distutils.core import setup
setup(name='mikidown',
	  version='0.1.0',
	  scripts = ['mikidown/scripts/mikidown'],
	  packages=['mikidown'],
	  data_files=[('share/mikidown', ['README.mkd']), 
		  		  ('share/mikidown', ['mikidown/notes.css'])],
	  requires = ['PyQt', 'markdown']
	  )
