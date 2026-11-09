#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# A collection of Contacts with a role

from model.ModelNode import ModelNode
from model.Contact import Contact

class Contacts(ModelNode):

    def __init__(self, top):
        # role => contact dict
        self._top = top
        owner = Contact(top)             # owner of the photovoltaic system, is mandatory
        owner.role = "owner"
        installer_ac = Contact(top)      # mandatory
        installer_ac.role = "installer_ac"
        self.contacts = {
            "owner" : owner,
            "installer_ac" : installer_ac,
        }

    # getter / setter for owner
    # owner is always set
    @property
    def owner(self):
        return self.contacts["owner"]
        
    @owner.setter
    def owner(self, value):
        self.contacts["owner"] = value

    # getter / setter for installer_ac
    @property
    def installer_ac(self):
        return self.contacts["installer_ac"]
        
    @installer_ac.setter
    def installer_ac(self, value):
        self.contacts["installer_ac"] = value

    # roles which must always exist
    MANDATORY = ("owner", "installer_ac")

    # add a new contact with role, None if the role exists already
    def addContact(self, role):
        if role in self.contacts:
            return None
        c = Contact(self._top)
        c.role = role
        self.contacts[role] = c
        return c

    def _roleOf(self, contact):
        for k, c in self.contacts.items():
            if c is contact:
                return k
        return None

    # a contact of this list which is not mandatory
    def canRemove(self, contact):
        role = self._roleOf(contact)
        return role is not None and role not in Contacts.MANDATORY

    def removeContact(self, contact):
        if not self.canRemove(contact):
            raise Exception("contact can not be removed: " + str(self._roleOf(contact)))
        del self.contacts[self._roleOf(contact)]
