#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# Municipality, (politsche) Gemeinde

import sqlite3

from model.PowerCompany import *

class Municipality:
    
    def __init__(self):
        self.id = None
        self.countryCode = None
        self.stateCode = None
        self.districtCode = None
        self.code = None
        self.name = None
        self.fkContactBuilding = None
        self.fkPowerCompany = None
        self.fkFormBuilding = None

    def fromCode(self, code):
        self.code = code

        con = sqlite3.connect("data/masterdata.db")
        cur = con.cursor()
        sql = "SELECT * FROM municipality WHERE code=?"
        res = cur.execute(sql, [code])
        db_row = res.fetchone()

        if db_row:
            self.id = db_row[0]
            self.countryCode = db_row[1]
            self.stateCode = db_row[2]
            self.districtCode = db_row[3]
            self.code = db_row[4]
            self.name = db_row[5]
            self.fkContactBuilding = db_row[6]
            self.fkPowerCompany = db_row[7]
            self.fkFormBuilding = db_row[8]
