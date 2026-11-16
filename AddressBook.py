#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The installer's own address book: contacts that exist apart from any project
# (electricians, roofers, architects, suppliers, ...), kept in the user
# database ~/.gnusolar/user.db (model/ContactStore.py).
#
# Changes in the form go into the contact at once and are written to the
# database when another contact is selected, the search changes, a contact is
# added or deleted, and when the window is closed.

import sys
import locale
import codecs

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QListWidgetItem, QMessageBox,
                             QLineEdit, QPlainTextEdit, QComboBox, QCheckBox)

from Ui.AddressBook import Ui_AddressBook
from Ui.Contact import Ui_Contact

from model.Contact import Contact
from model.ContactStore import ContactStore, FIELDS, label
from gui.binding import updateUi, updateModel
from gui.pages import createPage

from Config import Config, config
import ErrorHandler     # installs the dialog for unhandled exceptions


class AddressBook(QApplication):
    def __init__(self, *args):
        QApplication.__init__(self, *args)
        self.window = QMainWindow()

        self.ui = Ui_AddressBook()
        self.ui.setupUi(self.window)

        self.userDbPath = Config.getUserDbPath()
        print("Using User AddressBook: " + self.userDbPath)
        self.store = ContactStore(self.userDbPath)

        # the contact shown in the form; _id is None while none is selected
        self.contact = Contact()
        self.contact._id = None
        self.changed = False        # the form has changes not yet in the database
        self.filling = False        # the form is being filled from the contact

        # the contact form on the right
        widget = QWidget()
        self.contactUi = Ui_Contact()
        self.contactUi.setupUi(widget)
        self.ui.stackedWidget.addWidget(widget)
        self.ui.stackedWidget.setCurrentWidget(widget)
        self.contactPage = createPage(self.contactUi, self.contact, None)

        # every obj_ field updates the contact as it is edited
        for key, el in self.contactUi.__dict__.items():
            if not key.startswith("obj_"):
                continue
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

        self.ui.action_Quit.triggered.connect(self.quit)
        self.ui.newContact.clicked.connect(self.action_newContact)
        self.ui.deleteContact.clicked.connect(self.action_deleteContact)
        self.ui.search.textChanged.connect(self.action_search)
        self.ui.contactList.currentItemChanged.connect(self.action_listChanged)
        self.aboutToQuit.connect(self.action_aboutToQuit)

        self.fillContactList()
        self.showContact(None)
        self.window.show()

    # the list of contacts matching the search; selects contact selectId
    def fillContactList(self, selectId=None):
        l = self.ui.contactList
        l.blockSignals(True)
        l.clear()
        selected = None
        contacts = self.store.list(self.ui.search.text())
        for contactId, text in contacts:
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, contactId)
            l.addItem(item)
            if contactId == selectId:
                selected = item
        if selected:
            l.setCurrentItem(selected)
        l.blockSignals(False)
        self.ui.statusbar.showMessage(str(len(contacts)) + " Kontakte")
        return selected is not None

    # show the contact with this id in the form, None for an empty, disabled form
    def showContact(self, contactId):
        if contactId is None or not self.store.loadInto(self.contact, contactId):
            for field in FIELDS:
                setattr(self.contact, field, None)
            self.contact._id = None
        self.filling = True
        updateUi(self.contactUi, self.contact, "obj")
        self.filling = False
        self.changed = False
        enabled = self.contact._id is not None
        self.ui.stackedWidget.setEnabled(enabled)
        self.ui.deleteContact.setEnabled(enabled)

    # write the changes of the form to the database
    def saveContact(self):
        if self.contact._id is None or not self.changed:
            return
        self.store.save(self.contact)
        self.changed = False

    def action_attributeChanged(self):
        if self.filling or self.contact._id is None:
            return
        updateModel(self.contactUi, self.contact, "obj")
        self.changed = True
        item = self.ui.contactList.currentItem()
        if item:
            item.setText(label(self.contact))

    def action_listChanged(self, current, previous):
        self.saveContact()
        self.showContact(current.data(Qt.UserRole) if current else None)

    def action_search(self):
        self.saveContact()
        if not self.fillContactList(self.contact._id):
            self.showContact(None)

    def action_newContact(self):
        self.saveContact()
        new = Contact()
        new._id = None
        contactId = self.store.save(new)
        self.ui.search.blockSignals(True)
        self.ui.search.clear()
        self.ui.search.blockSignals(False)
        self.fillContactList(contactId)
        self.showContact(contactId)
        self.contactUi.obj_lastName.setFocus()

    def action_deleteContact(self):
        if self.contact._id is None:
            return
        name = label(self.contact)
        answer = QMessageBox.question(self.window, "Kontakt löschen",
                                      "Den Kontakt «" + name + "» löschen?")
        if answer != QMessageBox.Yes:
            return
        self.store.delete(self.contact._id)
        self.changed = False
        row = self.ui.contactList.currentRow()
        self.fillContactList()
        count = self.ui.contactList.count()
        if count:
            self.ui.contactList.setCurrentRow(min(row, count - 1))
        else:
            self.showContact(None)

    def action_aboutToQuit(self):
        self.saveContact()
        self.store.close()


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
