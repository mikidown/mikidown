#!/usr/bin/env python

import os
import sys
import logging
import mikidown
from mikidown.config import *

# Check the python version
try:
	version_info = sys.version_info
	assert version_info > (3, 0)
except:
	print >> sys.stderr, 'ERROR: mikidown needs python >= 3.0'
	sys.exit(1)

#global XDG_CONFIG_HOME
# Check config file
if 'XDG_CONFIG_HOME' in os.environ:
	XDG_CONFIG_HOME = os.environ['XDG_CONFIG_HOME']
else:
	XDG_CONFIG_HOME = '~/.config'

config_dir = XDG_CONFIG_HOME + '/mikidown/'
#print(XDG_CONFIG_HOME)
print(config_dir)
if not os.path.isdir(config_dir):
	os.makedirs(config_dir)

config_file = config_dir + 'notesbook.list'
#if not os.path.isfile(config_file):
#	NotebookList.create()

#if not config_file.exists():
#yield XDG_CONFIG_HOME.subdir(('mikidown'))

# Run mikidown
try:
	mikidown.main()
except KeyboardInterrupt:
	print >> sys.stderr, 'Interrupt'
	sys.exit(1)
else:
	sys.exit(0)
