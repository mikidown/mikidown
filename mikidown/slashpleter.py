from PyQt5 import QtWidgets

class SlashPleter(QtWidgets.QCompleter):
    def splitPath(self, path):
        return path.split('/')
    def pathFromIndex(self, idx):
        dataList=[]
        i=idx
        while i.isValid(): 
            dataList.append(self.model().data(i, self.completionRole()))
            i = i.parent()
        return '/'.join(dataList[::-1])
