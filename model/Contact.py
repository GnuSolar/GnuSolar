#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# A Contact is a way to contact a person. Postal address is mostly needed for bureaucratic stuff.

class Contact:

    def __init__(self):
        # class members
        
        self.title = None
        self.firstName = None
        self.lastName = None

        self.street = None
        self.streetNumber = None
        self.zip = None
        self.city = None

        self.email = None
        self.email2 = None
        self.phone = None
        self.phone2 = None
        self.mobile = None

