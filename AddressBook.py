#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
import locale
import codecs

import sqlite3

from Ui.AddressBook import *

from model.Contact import *
from gui.pages import createPage
from gui.forms import Form

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
        
        self.showContact()

        self.fillContactList()

    def action_quit(self):
        exit()
        
    def action_newContact(self):
        print("TODO: newContact")
        return

    def action_attributeChanged(self, form, field):
        self.attributeChanged = True
        return

    # show the page of the contact in the detail window
    def showContact(self):
        while self.ui.stackedWidget.count():
            widget = self.ui.stackedWidget.widget(0)
            self.ui.stackedWidget.removeWidget(widget)
            widget.deleteLater()
        self.contactPage = createPage(self.contact, None)
        self.contactForm = Form(self.contact, onChange=self.action_attributeChanged,
                                fieldActions=self.contactPage.fieldActions)
        self.ui.stackedWidget.addWidget(self.contactForm.widget)
        self.ui.stackedWidget.setCurrentWidget(self.contactForm.widget)

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
        self.showContact()
        

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
    
