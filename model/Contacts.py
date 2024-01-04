#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# A collection of Contacts with a role

from model.Contact import *

class Contacts:

    def __init__(self):
        # role => contact dict
        self._owner = Contact()         # owner of the photovoltaic system, is mandatory


    # getter / setter for owner
    # owner is alway set
    @property
    def owner(self):
        return self._owner
        
    @owner.setter
    def owner(self, value):
        self._owner = value

