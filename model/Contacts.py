#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# A collection of Contacts with a role

from model.PvProject import *
from model.Contact import *
from Config import *
from GnuSolar import *

class Contacts:

    def __init__(self, top):
        # role => contact dict
        self._top = top
        self._owner = Contact(top)             # owner of the photovoltaic system, is mandatory
        self._owner.role = "owner"
        self._installer_ac = Contact(top)      # mandatory
        self._installer_ac.role = "installer_ac"
        self.contacts = {
            "owner" : self._owner,
            "installer_ac" : self._installer_ac,
        }

    # getter / setter for owner
    # owner is always set
    @property
    def owner(self):
        return self._owner
        
    @owner.setter
    def owner(self, value):
        self._owner = value

    # getter / setter for installer_ac
    @property
    def installer_ac(self):
        return self._installer_ac
        
    @installer_ac.setter
    def installer_ac(self, value):
        self._installer_ac = value

    # tree hooks
    def getTreeCaption(self):
        return "Kontakte"

    def getTreeContextMenu(self):
        ret = {
            "contact_add": "Kontakt hinzufügen",
        }
        return ret
    
    def treeAction(self, action, ui_parent):
        actionKey = action.actionKey
        if actionKey == "contact_add":
            role = "test"
            c = Contact(self._top)
            c.role = role
            self.contacts[role] = c
            # update the ui
            caption = c.getTreeCaption()
            item = QTreeWidgetItem(None, [caption])
            item.pvpObj = c
            ui_parent.addChild(item)
        

    def initUi(self, ui):
        pass

    # for jsonpickle to ignore
    def __getstate__(self):
        state = self.__dict__.copy()
        del state['_top']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
