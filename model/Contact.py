#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# A Contact is a way to contact a person. Postal address is mostly needed for bureaucratic stuff.

import sqlite3

from Config import Config

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

    def fromId(self, contactId):
        con = sqlite3.connect(Config.getMasterDbPath())
        cur = con.cursor()
        sql = "SELECT * FROM contact WHERE id=?"
        res = cur.execute(sql, [contactId])
        db_row = res.fetchone()

        if db_row:
            self.company = db_row[4]
            self.firstName = db_row[5]
            self.email = db_row[6]
            self.email2 = db_row[7]
            self.phone = db_row[8]
            self.phone2 = db_row[9]
            self.street = db_row[10]
            self.zip = db_row[12]
            self.city = db_row[13]

    def fromMunicipalityType(self, munId, contactType):
        con = sqlite3.connect(Config.getMasterDbPath())
        cur = con.cursor()
        sql = "SELECT * FROM contact WHERE fk_municipality=? AND type=?"
        res = cur.execute(sql, [munId, contactType])
        db_row = res.fetchone()

        if db_row:
            self.company = db_row[4]
            self.firstName = db_row[5]
            self.email = db_row[6]
            self.email2 = db_row[7]
            self.phone = db_row[8]
            self.phone2 = db_row[9]
            self.street = db_row[10]
            self.zip = db_row[12]
            self.city = db_row[13]
        
        
    # get the first phone Number
    def getAnyPhone(self):
        if len(self.phone) > 0:
            return self.phone
        
        if len(self.phone2) > 0:
            return self.phone2
        
        if len(self.mobile) > 0:
            return self.mobile

        return "0800 800 800"       # default to swisscom main number :)
