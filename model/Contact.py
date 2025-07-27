#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# A Contact is a way to contact a person. Postal address is mostly needed for bureaucratic stuff.


import sqlite3

from Config import *
from GnuSolar import *

# An address / contact all in one
# can be renamed after serializing is independet of the object sttructure

class Contact:

    def __init__(self, top):
        # class members
        self._top = top
        
        # Role is a string with the following format:
        # aaa_whatever
        # aaa = addon code
        # builtin roles: bin_owner, bin_invoice
        self.role = None
        
        # Organizational
        self.company = None         # any Organization
        self.department = None
        
        # Personal
        self.title = None
        self.firstName = None
        self.middleName = None
        self.lastName = None
        self.nickName = None

        # Locational
        self.floor = None
        self.room = None
        self.street = None
        self.streetNumber = None
        self.address1 = None
        self.address2 = None
        self.zip = None
        self.city = None
        self.country = None

        # Communicational
        self.email = None
        self.email2 = None
        self.phone = None
        self.phone2 = None
        self.mobile = None
        
        # Financial
        self.accountOwner = None
        self.accountBank = None
        self.accountIban = None
        self.accountIid = None      # Institution Identifier (Switzerland)
        self.accountBic = None      # Business Identifier Code (Swift)

    def fromId(self, contactId):
        con = sqlite3.connect(Config.getMasterDbPath())
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT * FROM address WHERE id=?"
        res = cur.execute(sql, [contactId])
        db_row = res.fetchone()

        if db_row:
            self.company = db_row["company"]
            self.firstName = db_row["firstName"]
            self.email = db_row["email"]
            self.email2 = db_row["email2"]
            self.phone = db_row["phone"]
            self.phone2 = db_row["phone2"]
            self.street = db_row["street"]
            self.streetNumber = db_row["streetNumber"]
            self.zip = db_row["zip"]
            self.city = db_row["city"]

    def fromMunicipalityType(self, munId, contactType):
        con = sqlite3.connect(Config.getMasterDbPath())
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT * FROM address WHERE fk_municipality=? AND role=?"
        res = cur.execute(sql, [munId, contactType])
        db_row = res.fetchone()

        if db_row:
            self.company = db_row["company"]
            self.firstName = db_row["firstName"]
            self.email = db_row["email"]
            self.email2 = db_row["email2"]
            self.phone = db_row["phone"]
            self.phone2 = db_row["phone2"]
            self.street = db_row["street"]
            self.streetNumber = db_row["streetNumber"]
            self.zip = db_row["zip"]
            self.city = db_row["city"]
        
    # get the first phone Number
    def getAnyPhone(self):
        if self.phone and len(self.phone) > 0:
            return self.phone
        
        if self.phone2 and len(self.phone2) > 0:
            return self.phone2
        
        if self.mobile and len(self.mobile) > 0:
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
        company = ""
        if hasattr(self, "company") and self.company:
            company = self.company
        ret = company + " " + lastName + " " + firstName + " " + city
        ret = ret.strip()
        return ret
    
    def getNameAddress(self):
        lastName = self.lastName
        if not self.lastName:
            lastName = ""
        firstName = self.firstName
        if not self.firstName:
            firstName = ""
        city = self.city
        company = ""
        if hasattr(self, "company") and self.company:
            company = self.company
        ret = company + " " + lastName + " " + firstName
        ret = ret.strip()
        if not ret:
            ret = "No Name"
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
            "test": "Test",
        }
        return roles[self.role]

    def getTreeCaption(self):
        ret = "Kontakt (" + self.getRoleName() + ")"
        return ret

    def getTreeContextMenu(self):
        ret = {
            "contact_delete": "Kontakt löschen",
        }
        return ret

    def treeAction(self, action, ui_parent):
        actionKey = action.actionKey
        if actionKey == "contact_delete":
            # remove from ui
            contacts = ui_parent.parent().pvpObj
            ui_parent.parent().removeChild(ui_parent)

            # remove from model
            for k, c in contacts.contacts.items():
                if c == self:
                    del contacts.contacts[k]
                    return
            raise Exception("key not found: " + str(k))
         
    # for jsonpickle to ignore
    def __getstate__(self):
        state = self.__dict__.copy()
        if "_top" in state:         # it should always exists? Whatever
            del state['_top']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

