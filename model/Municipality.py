#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# Municipality, (politsche) Gemeinde

import sqlite3

from model.PowerCompany import *
from model.Contact import *
from selenium import webdriver

from Config import Config

class Municipality:
    
    def __init__(self):
        self.id = None
        self.countryCode = None
        self.stateCode = None
        self.districtCode = None
        self.code = None
        self.name = None
        self.buildingContact = Contact()
        self.mainContact = Contact()
        self.fkPowerCompany = None
        self.fkFormBuilding = None
        self.website = None

    def reloadFromDb(self):
        self.fromCode(self.code)
        
    def fromCode(self, code):
        self.code = code

        con = sqlite3.connect(Config.getMasterDbPath())
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
            self.fkPowerCompany = db_row[6]
            self.fkFormBuilding = db_row[7]
            self.website = db_row[8]
            self.buildingContact.fromMunicipalityType(self.id, "municipality_build")
            self.mainContact.fromMunicipalityType(self.id, "municipality_main")

    def getBuildingContact(self):
        contact = Contact()
        contact.fromMunicipalityType(self.id, "municipality_build")
        return contact

    def createBuildingForm(self, model):
        # get the FormTag
        if not self.fkFormBuilding:
            return "No fkFormBuilding municipality.id=" + str(self.id)
            
        con = sqlite3.connect(Config.getMasterDbPath())
        cur = con.cursor()
        sql = "SELECT * FROM form WHERE id=?"
        res = cur.execute(sql, [self.fkFormBuilding])
        db_row = res.fetchone()

        if not db_row:
            return "Form not found id=" + str(self.fkFormTag)
        
        form_type = db_row[1]
        form_handler = db_row[2]
        var_file = Config.getDataPath() + os.sep + db_row[3]
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

        browser = webdriver.Firefox()
        browser.get(self.fillform_url)
        for k,v in self.fillform_data.items():
            arr = k.split("::")
            by = arr[0]
            key = arr[1]
            try:
                element = browser.find_element(by, key)
            except Exception:
                print("Form element not found: by:" + by + " key:" + key)
                continue

            if isinstance(v, str):
                element.send_keys(v)

            if isinstance(v, bool) and v:
                element.click()

        # remove temporary attributes, so they dont get serialized
        del self.todayIso
        del self.fillform_url
        del self.fillform_data
        
