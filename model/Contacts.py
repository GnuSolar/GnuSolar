#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# A collection of Contacts with a role

from model.Contact import *

class Contacts:

    def __init__(self):
        # role => contact dict
        self._owner = Contact()             # owner of the photovoltaic system, is mandatory
        self._installer_ac = Contact()      # mandatory

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

    def getRoleName(self, role):
        roles = {
            "owner": "Bauherr",
            "installer_ac": "Elektriker AC",
        }

        return roles[role]
