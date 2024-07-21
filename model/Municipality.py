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
        self.mainContact = Contact()
        self.mainContact.role = "mun_main"
        self.buildingContact = Contact()
        self.buildingContact.role = "mun_building"
        self.fkPowerCompany = None
        self.fkFormBuilding = None
        self.website = None

    def reloadFromDb(self):
        self.fromCode(self.code)
        
    def fromCode(self, code):
        self.code = code

        con = sqlite3.connect(Config.getMasterDbPath())
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT * FROM municipality WHERE code=?"
        res = cur.execute(sql, [code])
        db_row = res.fetchone()

        if db_row:
            self.id = db_row["id"]
            self.countryCode = db_row["country_code"]
            self.stateCode = db_row["state_code"]
            self.districtCode = db_row["district_code"]
            self.code = db_row["code"]
            self.name = db_row["name"]
            self.fkPowerCompany = db_row["fk_power_company"]
            self.fkFormBuilding = db_row["fk_form_building"]
            self.website = db_row["website"]
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
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT * FROM form WHERE id=?"
        res = cur.execute(sql, [self.fkFormBuilding])
        db_row = res.fetchone()

        if not db_row:
            return "Form not found id=" + str(self.fkFormTag)
        
        form_type = db_row["type"]
        form_handler = db_row["handler"]
        var_file = Config.getDataPath() + os.sep + db_row["file"]
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
                try:
                    element.send_keys(v)
                except Exception:
                    print("Form element not sendable: by:" + by + " key:" + key)
                    continue

            if isinstance(v, bool) and v:
                try:
                    element.click()
                except Exception:
                    print("Form element not clickable: by:" + by + " key:" + key)
                    continue

        # remove temporary attributes, so they dont get serialized
        del self.todayIso
        del self.fillform_url
        del self.fillform_data
    
    def getTreeCaption(self):
        return "Gemeinde"

