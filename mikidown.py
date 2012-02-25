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

# Run mikidown
try:
	mikidown.main()
except KeyboardInterrupt:
	print >> sys.stderr, 'Interrupt'
	sys.exit(1)
else:
	sys.exit(0)
