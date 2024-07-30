#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# A collection of Contacts with a role

from model.PvProject import *
from model.Contact import *
from Config import *

class Contacts:

    def __init__(self, top):
        # role => contact dict
        self._top = top
        self._owner = Contact(top)             # owner of the photovoltaic system, is mandatory
        self._owner.role = "owner"
        self._installer_ac = Contact(top)      # mandatory
        self._installer_ac.role = "installer_ac"

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
            "add": "Kontakt hinzuf�gen",
        }
        return ret
    
    def treeAction(self, action):
        actionKey = action.actionKey
        print(actionKey)

    def initUi(self, ui):
        pass

    # for jsonpickle to ignore
    def __getstate__(self):
        state = self.__dict__.copy()
        del state['_top']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
