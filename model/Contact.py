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
        
        # Bank account information
        self.accountOwner = None
        self.accountBank = None
        self.accountIban = None
        self.accountIid = None      # Institution Identifier (Switzerland)
        self.accountBic = None      # Business Identifier Code (Swift)

    def fromId(self, contactId):
        con = sqlite3.connect(Config.getMasterDbPath())
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT * FROM contact WHERE id=?"
        res = cur.execute(sql, [contactId])
        db_row = res.fetchone()

        if db_row:
            self.company = db_row["function"]
            self.firstName = db_row["name"]
            self.email = db_row["email"]
            self.email2 = db_row["email2"]
            self.phone = db_row["phone"]
            self.phone2 = db_row["phone2"]
            self.street = db_row["address1"]
            self.zip = db_row["zip_code"]
            self.city = db_row["city"]

    def fromMunicipalityType(self, munId, contactType):
        con = sqlite3.connect(Config.getMasterDbPath())
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT * FROM contact WHERE fk_municipality=? AND type=?"
        res = cur.execute(sql, [munId, contactType])
        db_row = res.fetchone()

        if db_row:
            self.company = db_row["function"]
            self.firstName = db_row["name"]
            self.email = db_row["email"]
            self.email2 = db_row["email2"]
            self.phone = db_row["phone"]
            self.phone2 = db_row["phone2"]
            self.street = db_row["address1"]
            self.zip = db_row["zip_code"]
            self.city = db_row["city"]
        
    # get the first phone Number
    def getAnyPhone(self):
        if len(self.phone) > 0:
            return self.phone
        
        if len(self.phone2) > 0:
            return self.phone2
        
        if len(self.mobile) > 0:
            return self.mobile

        return "0800 800 800"       # default to swisscom main number :)

    def getNameCity(self):
        ret = str(self.lastName) + " " + str(self.firstName) + " " + str(self.city)
        if self.company:
            ret = str(self.company) + " " + str(self.city) + " " + str(self.lastName) + " " + str(self.firstName)
        return ret
            
