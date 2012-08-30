from distutils.core import setup
setup(name='mikidown',
    version='0.1.4',
    scripts = ['mikidown/scripts/mikidown'],
    packages=['mikidown'],
    data_files=[('share/mikidown', ['README.mkd']), 
        ('share/mikidown', ['mikidown/notes.css']),
        ('share/pixmaps', ['mikidown.png']),
        ('share/applications', ['mikidown.desktop'])],
    requires = ['PyQt', 'markdown']
    )
