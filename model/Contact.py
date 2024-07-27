#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# A Contact is a way to contact a person. Postal address is mostly needed for bureaucratic stuff.


import sqlite3

from Config import *
from GnuSolar import *

class Contact:

    def __init__(self):
        # class members
        self.role = None
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
        con = sqlite3.connect(config.getMasterDbPath())
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
        con = sqlite3.connect(config.getMasterDbPath())
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
        lastName = self.lastName
        if not self.lastName:
            lastName = ""
        firstName = self.firstName
        if not self.firstName:
            firstName = ""
        city = self.city
        if not self.city:
            city = ""
        company = self.company
        if not self.company:
            company = ""
        ret = company + " " + lastName + " " + firstName + " " + city
        ret = ret.strip()
        return ret
       
    def getPhoneClean(self):
        return self.cleanPhoneNumber(self.phone)     

    def getPhone2Clean(self):
        return self.cleanPhoneNumber(self.phone2)     

    def getMobileClean(self):
        return self.cleanPhoneNumber(self.mobile)     

    def cleanPhoneNumber(self, number):
        if not number:
            return ""
        number = number.replace("/", "")
        number = number.replace(" ", "")
        number = number.replace("+41", "0")
        number = number.strip()
        return number
    
    def exportVCard(self):
        ret = ""
        ret += "BEGIN:VCARD\n"
        ret += "VERSION:3.0\n"
        ret += "FN:"+self.getNameCity()+"\n"
        ret += "N:"+self.getNameCity()+";;;;\n"
        ret += "ORG:Solar;Owner\n"
        if self.email:
            ret += "EMAIL:"+self.email+"\n"
        if self.email2:
            ret += "EMAIL:"+self.email2+"\n"
        if self.phone:
            ret += "TEL;TYPE=voice:"+self.phone+"\n"
        if self.phone2:
            ret += "TEL;TYPE=voice:"+self.phone2+"\n"
        if self.mobile:
            ret += "TEL;TYPE=voice:"+self.mobile+"\n"
        ret += "END:VCARD\n"
 
        return ret

    def initUi(self, ui):
        ui.composeEmail.clicked.connect(self.action_composeEmail)
        ui.callPhone.clicked.connect(self.action_callPhone)
        ui.callPhone2.clicked.connect(self.action_callPhone2)
        ui.callMobile.clicked.connect(self.action_callMobile)

    def action_callPhone(self):
        callSip(self.phone)

    def action_callPhone2(self):
        callSip(self.phone2)

    def action_callMobile(self):
        callSip(self.mobile)

    def action_composeEmail(self):
        composeEmail(config.installer_email, self.email , "", "")

    def getRoleName(self):
        roles = {
            None: "None",
            "owner": "Bauherr",
            "installer_ac": "Elektriker AC",
            "mun_building": "Baubehörde",
            "mun_main": "Haupt",
            "pow_main": "Haupt",
            "pow_tag": "TAG's",
        }
        return roles[self.role]

    def getTreeCaption(self):
        ret = "Kontakt (" + self.getRoleName() + ")"
        return ret
        
