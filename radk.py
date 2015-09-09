#!/usr/bin/env python
import codecs
import sys
from PyQt4 import QtCore, QtGui
import os
import PyQt4.uic

radDict = {}
rad = None
miniList = [[] for x in range( 17 )]

execpath = os.path.dirname(sys.argv[0])

for line in codecs.open(os.path.join(execpath,"radkfile.utf8"), "r", encoding="utf8"):
	if line.startswith('#'):
		continue
	if line.startswith('$'):
		rad, stroke = line[2], int(line[4:])
		radDict[rad] = set()
		miniList[stroke - 1].append(rad)
	else:
		radDict[rad].update(line[:-1])

#print " ".join(radDict.keys())

class Radk(QtGui.QWidget):
	def __init__(self, parent=None):
		QtGui.QDialog.__init__(self, parent)

		uifile = os.path.join(execpath, 'radkForm.ui')
		self.ui = PyQt4.uic.loadUi(uifile, self)
	
		self.ui.tableWidget.horizontalHeader().hide()
		self.ui.tableWidget.verticalHeader().hide()
	
		i = 0
		for num, strokelist in enumerate(miniList):
			for elem in strokelist:
				widgetItem = QtGui.QTableWidgetItem(elem)
				widgetItem.setBackground( QtGui.QColor(240 - num*15, 250, 250-50*(num%2)) )
				self.ui.tableWidget.setItem(i / 20, i % 20, widgetItem)
				i += 1
		self.ui.tableWidget.resizeColumnsToContents()
		self.ui.tableWidget.resizeRowsToContents()
	
	def on_tableWidget_itemSelectionChanged(self):
		""" display every kanji matching all of the selected keys """
		l = [unicode(x.text()) for x in self.ui.tableWidget.selectedItems()]
		
		self.ui.textEdit.clear()
		if l == []:
			return
		# do the repeated interesect in reverse order
		i = radDict[l[-1]].copy()
		for x in l[-2::-1]:
			i.intersection_update(radDict[x])
		# print the kanjis sorted alphabetically (for those fluent in unicode :-)
		self.ui.textEdit.setPlainText(" ".join(sorted(i)))
	
	def on_lineEdit_textChanged(self):
		""" highlight all those keys whose the (or one of the) pasted kanji(s) match"""
		text = unicode(self.ui.lineEdit.text()).strip()
		keys = [key for key, val in radDict.items() if any([t in val for t in text])]
		for key in keys:
			itemW = self.ui.tableWidget.findItems(key, QtCore.Qt.MatchFixedString)[0]
			itemW.setSelected(True)

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	w = Radk()
	w.show()
	sys.exit(app.exec_())
