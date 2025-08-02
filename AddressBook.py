#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
import locale
import codecs

import sqlite3

from Ui.AddressBook import *
from Ui.Contact import *

from model.Contact import *

from Config import *
from ErrorHandler import *

class AddressBook(QApplication):
    def __init__(self, *args):
        QApplication.__init__(self, *args)
        self.window = QMainWindow()

        self.attributeChanged = False
        self.ui = Ui_AddressBook()
        self.ui.setupUi(self.window)

        self.ui.action_Quit.triggered.connect(self.action_quit)
        self.ui.newContact.clicked.connect(self.action_newContact)

        self.window.show()
        
        self.userDbPath = Config.getUserDbPath()
        print("Using User AddressBook: " + self.userDbPath)

        self.contact = Contact()
        
        # load the ui into the detail window
        widget = QWidget()
        ui = Ui_Contact()
        ui.setupUi(widget)
        self.ui.stackedWidget.addWidget(widget)
        self.ui.stackedWidget.setCurrentWidget(widget)

        # hook for ui initializiation
        self.contact.initUi(ui)
        
        # connect all obj_ fields with attributeChanged
        # updates the model on the fly from the ui
        for key, value in ui.__dict__.items():
            if key.startswith("obj_"):
                el = getattr(ui, key)

                if isinstance(el, QLineEdit):
                    el.textChanged.connect(self.action_attributeChanged)
                elif isinstance(el, QPlainTextEdit):
                    el.textChanged.connect(self.action_attributeChanged)
                elif isinstance(el, QComboBox):
                    el.currentIndexChanged.connect(self.action_attributeChanged)
                elif isinstance(el, QCheckBox):
                    el.toggled.connect(self.action_attributeChanged)
                else:
                    raise Exception(str(type(el)) + " not implemented")

        
        self.fillContactList()

    def action_quit(self):
        exit()
        
    def action_newContact(self):
        print("TODO: newContact")
        return

    def action_attributeChanged(self):
        self.attributeChanged = True
        return

    def fillContactList(self):
        con = sqlite3.connect(self.userDbPath)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        count = 0

        l = self.ui.contactList

        sql = "SELECT * FROM address"
        res = cur.execute(sql)
        for row in cur:
            firstName = row["firstName"]
            lastName = row["lastName"]

            count += 1
            
        print("Read " + str(count) + " contacts")
        
        return True

    def action_listClicked(self, item):
        # fill it with the attributes of the object
        GnuSolar.updateUi(ui, obj, "obj")
        

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
    
