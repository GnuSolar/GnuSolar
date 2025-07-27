#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
import locale
import codecs

from Ui.AddressBook import *

from Config import *

class AddressBook(QApplication):
    def __init__(self, *args):
        QApplication.__init__(self, *args)
        self.window = QMainWindow()

        self.ui = Ui_AddressBook()
        self.ui.setupUi(self.window)

        self.ui.action_Quit.triggered.connect(self.action_quit)

        self.window.show()

    def action_quit(self):
        exit()


def checkEnv():
    PY2 = sys.version_info[0] == 2
    # If we are on python 3 we will verify that the environment is
    # sane at this point of reject further execution to avoid a
    # broken script.
    if not PY2:
        try:
            fs_enc = codecs.lookup(locale.getpreferredencoding()).name
        except Exception:
           fs_enc = 'ascii'
        if fs_enc == 'ascii':
            raise RuntimeError('GnuSolar will abort further execution '
                               'because Python 3 was configured to use '
                               'ASCII as encoding for the environment. '
                               'Either switch to Python 2 or consult '
                               'http://bugs.python.org/issue13643 '
                               'for mitigation steps.')

if __name__ == "__main__":
    checkEnv()
    config.load()
    app = AddressBook(sys.argv)
    app.exec_()
    
