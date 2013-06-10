#!/bin/sh
cd ..
wget http://sourceforge.net/projects/pyqt/files/sip/sip-4.14.6/sip-4.14.6.tar.gz
tar -xvf sip-4.14.6.tar.gz
cd sip-4.14.6
python configure.py
make
sudo make install
cd ..
wget http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.10.1/PyQt-x11-gpl-4.10.1.tar.gz
tar -xvf PyQt-x11-gpl-4.10.1.tar.gz
cd PyQt-x11-gpl-4.10.1
python configure.py --confirm-license
make
sudo make install
cd ../mikidown
