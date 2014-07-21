#!/usr/bin/env python3

import sys
import logging
import mikidown

# Check the python version
try:
    version_info = sys.version_info
    assert version_info > (3, 0)
except:
    print('ERROR: mikidown needs python >= 3.0', file=sys.stderr)
    sys.exit(1)

# Run mikidown
if __name__ == '__main__':
    try:
        mikidown.main()
    except KeyboardInterrupt:
        print('Interrupt', file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(0)
