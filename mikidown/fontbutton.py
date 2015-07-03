from PyQt4 import QtCore,QtGui

class QFontButton(QtGui.QWidget):

	fontChanged = QtCore.pyqtSignal('QFont')

	def __init__(self, font=None, parent=None):
		super().__init__(parent)

		layout=QtGui.QVBoxLayout(self)
		self.label=QtGui.QLabel("ABCdef123",self)
		#self.label.setAutoFillBackground(True)
		self.button=QtGui.QPushButton(self)
		self.button.clicked.connect(lambda x: self.adjustFont())
		layout.addWidget(self.label)
		layout.addWidget(self.button)

		if isinstance(font,QtGui.QFont):
			self.font=font
		else:
			self.font=QtGui.QFont()
	
	def adjustFont(self):
		self.font,_=QtGui.QFontDialog.getFont(self.font,self,"")

	def font(self):
		return self._font
	
	def setFont(self,font):
		if isinstance(font,QtGui.QFont): 
			self._font=font
			self.button.setText("{} {}".format(font.family(), font.pointSize()))
			self.label.setFont(font)
			self.fontChanged.emit(self.font)
		else:
			raise ValueError("That isn't a QFont!")
	
	font = QtCore.pyqtProperty('QFont',fget=font,fset=setFont)

