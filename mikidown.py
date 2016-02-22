#!/usr/bin/env python3

from __future__ import print_function

import sys


# Run mikidown
if __name__ == '__main__':

    ## Check for Python3
    if not sys.version_info >= (3, 0, 0):
        sys.exit("ERROR: `mikidown` requires Python3")

    ## py3 is running, so import mikidown which would fail with py2
    import mikidown
    try:
        mikidown.main()
    except KeyboardInterrupt:
        print('Interrupt', file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(0)
