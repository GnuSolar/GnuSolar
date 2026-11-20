#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# A Contact is a way to contact a person. Postal address is mostly needed for bureaucratic stuff.


from model.ModelNode import ModelNode
import sqlite3

from Config import *

# An address / contact all in one
# can be renamed after serializing is independet of the object sttructure

# how a person is addressed: the code saved, the text shown
FORMALITIES = (
    ("formal", "Sie"),
    ("informal", "Du"),
)

class Contact(ModelNode):

    def __init__(self, top=None):
        # class members
        self._top = top
        
        # Role is a string with the following format:
        # aaa_whatever
        # aaa = addon code

        self.role = None
        
        # Organizational
        self.company = None         # any Organization
        self.department = None
        
        # Personal
        self.title = None           # Anrede: Herr, Frau, Herr und Frau, Familie
        self.firstName = None
        self.middleName = None
        self.lastName = None
        self.nickName = None

        # how the person is addressed in letters, a code of FORMALITIES:
        # "formal" (Sie) or "informal" (Du). None counts as "formal".
        self.formality = "formal"

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
            self.fromDbRow(db_row)

    def fromMunicipalityType(self, munId, contactType):
        con = sqlite3.connect(Config.getMasterDbPath())
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT * FROM address WHERE fk_municipality=? AND role=?"
        res = cur.execute(sql, [munId, contactType])
        db_row = res.fetchone()

        if db_row:
            self.fromDbRow(db_row)
        
    def fromDbRow(self, db_row):
        self.company = db_row["company"]
        self.firstName = db_row["firstName"]
        self.lastName = db_row["lastName"]
        self.email = db_row["email"]
        self.email2 = db_row["email2"]
        self.phone = db_row["phone"]
        self.phone2 = db_row["phone2"]
        self.street = db_row["street"]
        self.streetNumber = db_row["streetNumber"]
        self.zip = db_row["zip"]
        self.city = db_row["city"]
        
    # True if the person is addressed informally (Du)
    @property
    def informal(self):
        return self.formality == "informal"

    # For the templates: the first text for Sie, the second for Du, e.g.
    # <o.owner.byFormality('Ihnen', 'Dir')>. Both forms are written out, so the
    # endings and verbs stay right.
    def byFormality(self, formal, informal):
        return informal if self.informal else formal

    # For the templates: the first line of a letter. Sie: "Guten Tag" with
    # the Anrede and the last name, "Guten Tag Herr Kraft". Du: "Hallo" with
    # the nick name or the first name, "Hallo Alois".
    @property
    def greeting(self):
        clean = lambda v: (v or "").strip()
        if self.informal:
            name = clean(self.nickName) or clean(self.firstName)
            return ("Hallo " + name) if name else "Hallo"
        title, last = clean(self.title), clean(self.lastName)
        if title and last:
            return "Guten Tag " + title + " " + last
        name = " ".join(n for n in (clean(self.firstName), last) if n)
        return ("Guten Tag " + name) if name else "Guten Tag"

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
        return roles.get(self.role, str(self.role))
