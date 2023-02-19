#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# Power Company, Power Supplier, EVU, EW, Elektrizitätsversorgunsunternehmen, Elektrizitätswerk, 

import json
import sqlite3
import os

import fillpdf
import datetime

from datetime import date
from model.Contact import *

from Config import Config

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
        
    def reloadFromDb(self):
        self.fromId(self.id)

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

    def createTag(self, model, tagPath):
        # get the FormTag
        if not self.fkFormTag:
            return "No fkFormTag powerCompany.id=" + str(self.id)
            
        con = sqlite3.connect("data/masterdata.db")
        cur = con.cursor()
        sql = "SELECT * FROM form WHERE id=?"
        res = cur.execute(sql, [self.fkFormTag])
        db_row = res.fetchone()

        if not db_row:
            return "Form not found id=" + str(self.fkFormTag)
        
        form_type = db_row[1]
        form_handler = db_row[2]
        form_file = "data" + os.sep + db_row[3]
        if not os.path.exists(form_file):
            return "File not found: '" + form_file + "'"
        
        var_file = os.path.splitext(form_file)[0]+'.var'
        if not os.path.exists(var_file):
            return "File not found: '" + var_file + "'"

        today = date.today()
        self.todayIso = today.isoformat()
        three_months = datetime.timedelta(3*365/12)
        self.turnOnIso = (today + three_months).isoformat()

        f = open(var_file)
        s = f.read()
        f.close()

        exec(s)
        
        fillpdf.single_form_fill(form_file, self.fillpdf_data, tagPath)

        # remove temporary attributes, so they dont get serialized
        del self.turnOnIso
        del self.todayIso
        del self.fillpdf_data
        
        return True
