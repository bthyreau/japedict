Those are some small programs that i designed to help with memorizing
japanese vocabulary. It includes a dictionary user interface and
a corresponding drill program, which can also get inputs from the
Rika-chan Firefox addons. User-data is intended to be saved on Dropbox.

That means, that unlike a general purpose tool like ANKI, the emphasis
here is set on reducing the overhead by focusing on a single workflow
which was helpful for me.

An example of workflow is
- From the dictionary, lookup or browse for a specific word of interest,
press "Enter" to append it on the user query list. 
or
- From a web page (in Firefox) or email (using Thunderbird), when the
Rika-chan plugin is activated, press "s" to append the highlighted word
to the query list [assuming proper path setup in Rika-chan options].

- running the drill SRS program will allow to train for the words in
the list, with a low-on-keypress UI. Simple SRS (Spaced-Repetition
Software) algorithm is used to order the queries. Different fonts are
used at random to avoid visual overfitting.

- data-files and SRS statistics are shared on Dropbox so that the tools
can be used from many computers.


Program Contents

japanesedict_dropbox.py
- japEdict is a straightforward user interface to the free EDICT
  dictionary, and additional kanji reading from the unicode spec.
  Input can contains regular expression (regex). Pressing Enter
  will add the first entry to the query list; lower entries need
  to be selected manually and the "save entry" button clicked.

  It embedds a copy of J.W. Breen's free edict dictionary
  http://www.edrdg.org/jmdict/edict.html

  It embedds a copy of Ed Halley's romaji.py to convert kana-romaji
  http://halley.cc/code/?python/romaji.py

  The program can also grep's from pre-made material (e.g. textbook)
  (try to search for "zankoku").

radk.py
  Allows to quickly split or merge kanji based on its key compound.

  Upper part allows to select one or many keys while the matching
  kanjis are displayed in lower part.
  Middle line input enable the opposite, highlighting keys matching
  the pasted input

  It embedds a copy of radkfile, op-cit, for the kanji compound

displayer_srs_dropbox.py
  A drill program with basic SRS features.
  The program will use the user-created vocabulary query list - the
  simple text file, usually feeded when japEdict or rika-chan appends
  new entry - and will display each words for drilling, selected
  according to time since the previous correct answer.

  Words are presented in 3 successive rows, for Kanji, Kana and
  Translation. Usual, the only necessary user action is to press "Next",
  before the time-progress bar run out, and statistics are collected
  based on that bar position. However, alternative "Fail"/"Pass" button
  are available to enforce behavior.

All tools are PyQt4 programs, and tested on both Linux and MacOSX.
The UI is easy to customize using qt4-designer on the .ui, in order
to optimize the UI to one's optimal preference.
