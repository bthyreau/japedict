#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import PyQt4.uic
import codecs, sys, mmap, random, re, os, glob, sha, time
from romaji import roma, kana


possible_fonts = ["Bitstream Cyberbit", "Droid Sans Japanese", u"EPSON 丸ゴシック体Ｍ", u"EPSON 太明朝体Ｂ", u"EPSON 行書体Ｍ", u"EPSON 教科書体Ｍ"]
# This is a list of fontname used randomly for display (not included in the repo, harvested from the web...)
#Additionally, a font named "KanjiStrokeOrders" is used by default on the tooltip

sha_hash = lambda v : sha.sha(v.encode("utf-8")).hexdigest()[:8]

class srs_management(object):
    """
    voca : a linear list of edict-like entry
    srs_map : a fixed-entry-size table for word scheduling, first column is hash of entry (either direct or reverse)
    _dhashvoca_F: a dictionary linking hashcodes to voca entries (index in voca)
    """
    # Configuration of the vocabulary list (this is where japedict saves its entries,
    # and where Rika-chan should save them too, see relevant Rika-chan's configuration option in the Firefox addon dialog)  
    vocafile = "%s/Dropbox/japedict_edict_rikachan_list.txt" % os.environ['HOME']
    # A private file to store current SRS statistics.
    srs_stats_filename = "%s/Dropbox/displayer_srs_stats.txt" % os.environ['HOME']
    # Number of second to wait before querying again, per categories. (each word is promoted to next category on success)
    D_sr_delay = { "c0": 30, "c1" : 5*60,  "c2" : 30*60, "c3" : 2*60*60, "c4" : 24*60*60, "c5" : 5*24*60*60, "c6": 14*24*60*60, "c7": 2*31*24*60*60 }

    voca = []
    _dhashvoca_F = {}
    _dhashvoca_R = {}

    def reload_voca(self, max_words = -1):
        self.voca[:] = []
        for x in codecs.open(self.vocafile, encoding='utf-8').readlines():
            if "\t" in x: # format is either Edict or Rika-chan
                parsed = re.match('(?P<word>[^\t]+)\t((?P<sound>[^\t]+)\t)?(?P<text>.*$)', x, re.U).groupdict()
            else:
                parsed = re.match('(?P<word>[^\s]+)\s+(\[(?P<sound>[^\s]+)\]\s+)?(?P<text>/.*/$)', x, re.U).groupdict()
            self.voca.append([parsed['word'], parsed['sound'] or "", parsed['text']])
        self.voca.reverse()
       
        self.update_mmap_srs()
        self.map_srs_file()
        self.rehash_voca(maxw = max_words)
        self.lenvoca = len(self._dhashvoca_F)
        self.maxlenvoca = len( self.voca )
        
    def get_voca(self, idx):
        return self.voca[idx]
    
    def map_srs_file(self):
        # map the statfile
        self._srs_stat_fid = open(self.srs_stats_filename, "r+b")
        self.srs_map = mmap.mmap(self._srs_stat_fid.fileno(), 0)

    def rehash_voca(self, maxw = -1):
        self._dhashvoca_F.clear()
        self._dhashvoca_R.clear()
        for i, x in enumerate(self.voca):
            if len(self._dhashvoca_F) == maxw:
                break
            self._dhashvoca_F[sha.sha(x[0].encode("utf-8")).hexdigest()[:8]] = i
            self._dhashvoca_R[sha.sha(x[2].encode("utf-8")).hexdigest()[:8]] = i

    def update_mmap_srs(self):
        # check for new voca and create entries in statfile
        # should be done when voca is full, although harmless if voca is a subset
        hashfounds = set([x[:8] for x in open(self.srs_stats_filename).readlines()] if os.path.exists(self.srs_stats_filename) else [])
        newvoc = [x for x in self.voca if sha_hash(x[0]) not in hashfounds]
        with open(self.srs_stats_filename, "a") as f:
            for x in newvoc:
                # hash Forward/Backward NextScheduledTime Category(eg. c0: min, c1: 30min, c2: 1day, etc)
                f.write( "%s %s %011d %s\n" % (sha_hash(x[0]), "F", 0, "c0") )
                f.write( "%s %s %011d %s\n" % (sha_hash(x[2]), "R", 0, "c0") )

    def vocaIndex_fromsrs(self, direction, srs_entry):
        return (srs._dhashvoca_F if direction == "F" else srs._dhashvoca_R)[srs_entry[0]]

    def find_one_timeouted(self, is_forward = True):
        # pick a word randomly among the 20 earliest-scheduled entries
        current_time = int(time.time())
        candidates = []
        SRS_ENTRY_SIZE = self.srs_map.find("\n") + 1
        for i in range(len(self.srs_map) // SRS_ENTRY_SIZE):
            entry = self.srs_map[SRS_ENTRY_SIZE*i: SRS_ENTRY_SIZE*(i+1)]
            if entry[:8] not in (self._dhashvoca_F if is_forward else self._dhashvoca_R):
                continue
            if is_forward == (entry[9] == "F"):
                timestamp = int( entry[11:22] )
                if timestamp < current_time:
                    candidates.append( (i, entry.split()) )
                    if len(candidates) == 20:
                        break
        return ( random.choice(candidates) if candidates != [] else (-1, None) )

    def find_matching(self, text):
        char = random.choice(text)
        matching_allvoca = [sha_hash(v[0]) for v in self.voca if char in v[0]]
        
        if matching_allvoca == []:
            return -1, None
        
        srs_matching = []
        SRS_ENTRY_SIZE = self.srs_map.find("\n") + 1
        for i in range(len(self.srs_map) // SRS_ENTRY_SIZE):
            entry = self.srs_map[SRS_ENTRY_SIZE*i: SRS_ENTRY_SIZE*(i+1)]
            if entry[:8] in matching_allvoca:
                srs_matching.append( (entry[11:22], (i, entry)) ) # for sorting
        random.shuffle(srs_matching) # add variety among all those 000000000-timed entries...
        _, (idx, entry) = sorted(srs_matching, key=lambda x:x[0])[0] # pick the oldest to be seen
        return idx, entry.split()

    def check_answer_and_update(self, srs_idx, correct = 1, category = "c0"):
        if (correct == 2) and (category < max(self.D_sr_delay)): # upgrade twice if very easy
                category = "c%d" % (int(category[1:]) + 1)
                correct = 1

        if (correct == 1) and (category < max(self.D_sr_delay)):
                new_category = "c%d" % (int(category[1:]) + 1)
        elif correct == 0:
                new_category = category
        elif correct == -1:
                new_category = "c0"
        else:
                new_category = category

        next_timeout = int(time.time() +  self.D_sr_delay[new_category] )
        self.update_srs_entry(srs_idx, next_timeout, new_category)

        # print debug info:
        SRS_ENTRY_SIZE = self.srs_map.find("\n") + 1
        h = self.srs_map[SRS_ENTRY_SIZE*srs_idx :SRS_ENTRY_SIZE*srs_idx+8]
        dh = self._dhashvoca_F if h in self._dhashvoca_F else self._dhashvoca_R
        print "Entry ", self.voca[ dh[h] ][0], "(next timeout in", self.D_sr_delay[new_category], "s), from", category, "to", new_category

    def update_srs_entry(self, srs_idx, next_timeout, category = None):
        if os.fstat(self._srs_stat_fid.fileno()).st_ino != os.stat(self.srs_stats_filename).st_ino:
            print "srsmap inode change detected. Force reloading."
            self.reload_voca(self.lenvoca)
            return

        SRS_ENTRY_SIZE = self.srs_map.find("\n") + 1
        self.srs_map[SRS_ENTRY_SIZE*srs_idx + 11 :SRS_ENTRY_SIZE*srs_idx+ 22] = ("%011d" % next_timeout)
        if category:
            self.srs_map[SRS_ENTRY_SIZE*srs_idx + 23 :SRS_ENTRY_SIZE*srs_idx+ 25] = category

    def flush_srs_map(self):
        self.srs_map.flush()
        os.utime(self.srs_stats_filename, None) # wake dropbox




class displayer(QtGui.QWidget):
    displayed = 0
    txts = 0
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        execpath = os.path.dirname(sys.argv[0])
        uifile = os.path.join(execpath, 'displayersrsform.ui')
        self.ui = PyQt4.uic.loadUi(uifile, self)
        if not hasattr(self.label_1, "hasSelectedText"): # for older Qt
            self.label_1.hasSelectedText = lambda : False
        self.label_font = self.label_1.font()
        self.progress_timer = QtCore.QTimer()
        self.connect(self.progress_timer, QtCore.SIGNAL("timeout()"), self.on_progress_timeout)
        
        self.reload_voca_from_ui()
        self.curIndex = 0

    @QtCore.pyqtSignature("")
    def on_bReload_clicked(self):
        self.reload_voca_from_ui()

    def reload_voca_from_ui(self):
        maxwords = ( -1 if not self.checkBoxLimit.isChecked() else self.spinBoxLoadNum.value() )
        srs.reload_voca(maxwords)
        self.spinBoxLoadNum.setMaximum(srs.maxlenvoca)
        self.spinBoxLoadNum.setValue(srs.lenvoca)
        self.current_item_srs = (-1, None)

    def refresh(self, reverse):
        if self.displayed == (2 if reverse else 0):
            self.label_font.setFamily(random.choice(possible_fonts))

            # check previous answer and update srs map
            prev_srs_idx, prev_srs_entry = self.current_item_srs
            if prev_srs_entry != None:
                if self.progressBar.value() < 4000:
                    answer_correct = 2 # easy
                elif self.progressBar.value() < 9000:
                    answer_correct = 1
                elif self.progressBar.value() < 14900:
                    answer_correct = 0
                else:
                    answer_correct = -1
                srs.check_answer_and_update(prev_srs_idx, correct = answer_correct, category = prev_srs_entry[3])

            # pick a next question
            srs_idx, srs_entry = srs.find_one_timeouted(is_forward = not reverse)

            if self.label_1.hasSelectedText(): # instead, pick a question with same character
                srs_idx, srs_entry = srs.find_matching( unicode(self.label_1.selectedText()) )

            if srs_entry != None:
                self.curIndex = srs.vocaIndex_fromsrs(("F" if not reverse else "R"), srs_entry)
            else:
                print "OK, finished - looping"
            
            self.txts = srs.get_voca(self.curIndex)

            self.label_2.clear()
            self.label_3.clear()
            self.label_1.clear()

            self.progressBar.setValue(0)
            self.progress_timer.start(100)
            self.current_item_srs = (srs_idx, srs_entry)

        if self.displayed == 0:
            self.label_1.setText(self.txts[0])
            self.label_1.setFont(self.label_font)
            if self.txts[1] == "":
                self.label_2.setText(u" (%s)" % roma(self.txts[0]))
        if self.displayed == 1:
            if self.txts[1] != "":
                try:
                    v = u" (%s)" % roma(self.txts[1])
                except:
                    v = ""
                self.label_2.setText(self.txts[1] + v)
                if reverse:
                    self.progress_timer.stop()

            else:
                self.displayed = (1 if reverse else 2)
        if self.displayed == 2:
            self.label_3.setText(self.txts[2])
            if not reverse:
                self.progress_timer.stop()

        self.label_1.setToolTip(u'<span style="font-size:72pt;font-family:KanjiStrokeOrders">%s</span>' % self.txts[0])

    @QtCore.pyqtSignature("")
    def on_pushButton_clicked(self):
        self.refresh(self.checkBoxBackward.isChecked())
        self.displayed = (self.displayed + 1) % 3

    def on_checkBoxBackward_toggled(self, t):
        self.current_item_srs = (-1, None)

    def on_progress_timeout(self):
        v = self.progressBar.value() + 100
        if v <= 15000:
            self.progressBar.setValue(v)
        else:
            self.progress_timer.stop()
            srs.flush_srs_map() # kindof idle, good time to enforce flush

    @QtCore.pyqtSignature("")
    def on_pushButtonFail_clicked(self):
        srs.check_answer_and_update(self.current_item_srs[0], correct = -1)
        self.current_item_srs = (-1, None)

    @QtCore.pyqtSignature("")
    def on_pushButtonPass_clicked(self):
        srs.update_srs_entry(self.current_item_srs[0], time.time() + 60, category = None) # put this word out of the way for a while
        self.current_item_srs = (-1, None)

    @QtCore.pyqtSignature("")
    def on_pushButtonLater_clicked(self):
        srs.update_srs_entry(self.current_item_srs[0], time.time() + 7*86400, category = "c0") # reset this word category and put it away for one week
        self.current_item_srs = (-1, None)


srs = srs_management()
app = QtGui.QApplication(sys.argv)
w = displayer(None)
w.show()
sys.exit(app.exec_())
