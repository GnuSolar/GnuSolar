#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# Power Company, Power Supplier, EVU, EW, Elektrizitätsversorgunsunternehmen, Elektrizitätswerk, 

import json
import sqlite3

from model.Contact import *

class PowerCompany:
    
    def __init__(self):
        self.id = None
        self.vseId = None
        self.name = None
        self.address1 = None
        self.address2 = None
        self.zipCode = None
        self.city = None
        self.fkContactTag = None
        self.fkFormTag = None
        self.fkFormIa = None
        
        self.mainContact = Contact()        # Address of the Headquarters
        

    def fromId(self, id):
        self.id = id

        con = sqlite3.connect("data/masterdata.db")
        cur = con.cursor()
        sql = "SELECT * FROM power_company WHERE id=?"
        res = cur.execute(sql, [id])
        db_row = res.fetchone()

        if db_row:
            self.id = db_row[0]
            self.vseId = db_row[1]
            self.name = db_row[2]
            self.address1 = db_row[3]
            self.address2 = db_row[4]
            self.zipCode = db_row[5]
            self.city = db_row[6]
            self.fkContactTag = db_row[7]
            self.fkFormTag = db_row[8]
            self.fkFormIa = db_row[9]
