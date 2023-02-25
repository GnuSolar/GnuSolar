#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# A Contact is a way to contact a person. Postal address is mostly needed for bureaucratic stuff.

class Contact:

    def __init__(self):
        # class members
        self.company = None
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

    # get the first phone Number
    def getAnyPhone(self):
        if len(self.phone) > 0:
            return self.phone
        
        if len(self.phone2) > 0:
            return self.phone2
        
        if len(self.mobile) > 0:
            return self.mobile

        return "0800 800 800"       # default to swisscom main number
