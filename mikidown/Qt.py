# -*- coding: utf-8 -*-


# @pedro notes
# This script is inspired by PyQtGraph
# https://github.com/pyqtgraph/pyqtgraph/blob/develop/pyqtgraph/Qt.py
# and a future idea of loading either pyside or even android qt.py
# lets dream on..
#
# This pull the libs into a common name space
# 
# Constants and Enums etc..
# In c++ `Qt::AlignLeft` is just there 
# but in PyQt land its at `PyQt5.QtCore.Qt.AlignLeft` .. phew
# So this imports for shortcut.. ta snake

from PyQt5.QtCore import Qt

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtNetwork
from PyQt5 import QtWebKit
from PyQt5 import QtWebKitWidgets
from PyQt5 import QtPrintSupport
