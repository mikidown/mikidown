#!/bin/sh

SIPVER="4.16.9"
PYQTVER="5.5.1"

cd ..
wget "https://sourceforge.net/projects/pyqt/files/sip/sip-${SIPVER}/sip-${SIPVER}.tar.gz"
tar -xvf "sip-${SIPVER}.tar.gz"
cd "sip-${SIPVER}"
python configure.py
make
sudo make install

cd ..
wget "https://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-${PYQTVER}/PyQt-gpl-${PYQTVER}.tar.gz"
tar -xvf "PyQt-gpl-${PYQTVER}.tar.gz"
cd "PyQt-gpl-${PYQTVER}"
python configure.py --confirm-license
make
sudo make install
cd ../mikidown
