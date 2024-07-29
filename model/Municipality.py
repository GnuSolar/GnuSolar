#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# Municipality, (politsche) Gemeinde

import sqlite3
from selenium import webdriver

from model.PvProject import *
from model.PowerCompany import *
from model.Contact import *

from Config import *
from GnuSolar import *

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

    def createBuildingForm(self):
        global model
        
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

    # Erzeuge Gebäudeversicherung Zürich Formular
    def action_createGvzDocumentation(self):
        global config

        projectDir = os.path.dirname(config.savePath)
        gvzDir =  projectDir + os.sep + "gov"
        gvzPath = gvzDir + os.sep + "01_gvz_dokumentation.pdf"
        if not os.path.isdir(gvzDir):
            os.makedirs(gvzDir)

        form_file = Config.getDataPath() + os.sep + "ch" + os.sep + "build" + os.sep + "gvz_documentation.pdf"
        if not os.path.exists(form_file):
            return "File not found: '" + form_file + "'"
        
        var_file = os.path.splitext(form_file)[0]+'.py'
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
        
        fillpdf.single_form_fill(form_file, self.fillpdf_data, gvzPath)

        # remove temporary attributes, so they dont get serialized
        del self.turnOnIso
        del self.todayIso
        del self.fillpdf_data

        openFolderIfExists(gvzPath)

    # Erzeuge Solarmeldung
    def action_createBuildingForm(self):
        ret = self.createBuildingForm()
        if isinstance(ret, str):
            QtWidgets.QMessageBox.information(None, 'Error Creating TAG', ret)
            return

    # Gemeinde Webseite öffnen
    def action_openMunicipalityWebsite(self):
        if not self.website:
            return
        openFolder(self.website)

    def initUi(self, ui):
        ui.openMunicipalityWebsite.clicked.connect(self.action_openMunicipalityWebsite)
        ui.createBuildingForm.clicked.connect(self.action_createBuildingForm)
        ui.createGvzDocumentation.clicked.connect(self.action_createGvzDocumentation)
