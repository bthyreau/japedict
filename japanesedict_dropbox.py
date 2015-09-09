#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os, time, codecs, gzip
from PyQt4 import QtCore, QtGui
import PyQt4.uic

from romaji import roma

# Kanji # Unicode info from http://www.unicode.org/Public/UNIDATA/Unihan.zip
# grep -v "^#" Unihan_Readings.txt | grep "kJapanese\|kDefinition"  > sub_Unihan_Readings.txt
D_unichar = {}
for line in gzip.open("./sub_Unihan_Readings.txt.gz"):
    t = line[:-1].split("\t")
    try:
        code = unichr(int(t[0][2:], 16)) # "U+7FD2" to \u7fd2
    except ValueError: # don't crash on narrow python builds
        pass
    D_unichar.setdefault(code, []).append( (t[1][9:], t[2]) )

class JapaneseDict(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        execpath = os.path.dirname(sys.argv[0])
        uifile = os.path.join(execpath, 'japanesedictform.ui')
        self.ui = PyQt4.uic.loadUi(uifile, self)
        self.pen = QtGui.QBrush(QtGui.QColor("lightGray"))
        self.penUnicode = QtGui.QBrush(QtGui.QColor("lightBlue"))
        self.smallfont = self.listWidget.font()
        self.smallfont.setPointSize(12)
    
    def on_lineEdit1_textChanged(self):
        req = unicode(self.lineEdit1.text())
        self.lineEditK.setText(roma(req))
        if len(req) == 0:
            return
        latin1 = codecs.utf_8_encode(req)[0]
        self.listWidget.clear()
        v = os.popen("grep '" + latin1 + "' edict.utf8").readlines()
        for entry in [codecs.utf_8_decode(line[:-1])[0] for line in v[:150]]:
            if '['+req+']' in entry or entry.startswith(req + " "):
                # exact match => move to top and color in gray
                self.listWidget.insertItem(0, entry)
                self.listWidget.item(0).setBackground(self.pen)
            else:
                self.listWidget.addItem(entry)
        if len(req) == 1 and req in D_unichar:
            infos_unicode = D_unichar[req]
            entry = "\n".join(["%s: %s" % x for x in (sorted(infos_unicode, reverse=True))])[4:]
            self.listWidget.insertItem(0, entry)
            self.listWidget.item(0).setBackground(self.penUnicode)
            self.listWidget.item(0).setFont(self.smallfont)
        self.stackedWidget.setCurrentIndex(0)
        if req.lower() == "samuel":
            QtGui.QMessageBox.information(None, "Spoiled!", u"Dans cette série, il meurt à la fin", "TA GUEULE")
    
    def on_lineEdit1_returnPressed(self):
        if self.listWidget.count() != 0:
            self.saveline(unicode(self.listWidget.item(0).text()))
    
    def saveline(self, line):
        if "\n" in line:
            return
        self.lineEdit_2.setText("Saving to dropbox")
        QtCore.QTimer.singleShot(700, self.lineEdit_2.clear)
        codecs.open(os.environ['HOME'] + "/Dropbox/japedict_edict_rikachan_list.txt", 'a', encoding='utf-8').write(line + '\n')
    
    @QtCore.pyqtSignature("")
    def on_BStdout_clicked(self):
        text = unicode(self.lineEdit_2.text())
        if text:
            self.saveline(text)
    
    @QtCore.pyqtSignature("")
    def on_BSong_clicked(self):
        req = unicode(self.lineEdit1.text()).encode('utf-8')
        if len(req) == 0:
            return
        if not ('a' < req[0] < 'z'):
            req = unicode(self.lineEditK.text()).encode('utf-8')
        v = os.popen("zgrep -C 1 '" + req + "' toyuncat.gz").read().replace(req, '<b><span style=" color:#00007f;">%s</span></b>'%req)
        v=[[i.split('\t') for i in x.strip().split('\n')] for x in v.replace('\n\n','\n--\n').split('--\n') if x]
        self.textBrowser.clear()
        for song in v[:100]:
            self.textBrowser.insertHtml("<i>%s :</t><br/>\n" % song[0][0])
            self.textBrowser.insertHtml("<p><tt> %s</tt></p>" % "<br/>\n".join( [".  %s" % (x[1] if len(x) > 1 else "") for x in song]))
            self.textBrowser.insertHtml("<br/>\n<br/>\n")
        if len(v) > 100:
            self.textBrowser.insertHtml("...and %d more" % (len(v) - 100))
        if len(v):
            self.stackedWidget.setCurrentIndex(1)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    w = JapaneseDict()
    w.show()
    sys.exit(app.exec_())
