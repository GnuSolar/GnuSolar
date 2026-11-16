#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Dialog to choose a contact of the address book (model/ContactStore.py).
#
#   contactId = pickContact(parent, store)     # None when cancelled

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
                             QDialogButtonBox)


class ContactPicker(QDialog):
    def __init__(self, parent, store):
        QDialog.__init__(self, parent)
        self.store = store
        self.setWindowTitle("Kontakt aus dem Adressbuch")
        self.resize(400, 500)

        layout = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Suchen")
        self.search.setClearButtonEnabled(True)
        layout.addWidget(self.search)
        self.list = QListWidget()
        layout.addWidget(self.list)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(self.buttons)

        self.search.textChanged.connect(self.fill)
        self.list.itemDoubleClicked.connect(self.accept)
        self.list.currentItemChanged.connect(self.updateOk)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.fill()
        self.search.setFocus()

    def fill(self):
        self.list.clear()
        for contactId, text in self.store.list(self.search.text()):
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, contactId)
            self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)
        self.updateOk()

    def updateOk(self):
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(self.list.currentItem() is not None)

    def contactId(self):
        item = self.list.currentItem()
        return item.data(Qt.UserRole) if item else None


def pickContact(parent, store):
    dialog = ContactPicker(parent, store)
    if dialog.exec_() != QDialog.Accepted:
        return None
    return dialog.contactId()
