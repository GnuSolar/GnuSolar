#!/usr/bin/python
# -*- coding: utf-8 -*-

# Parts of the place where the system stands
# (doc/file_format_v3/file_format.md, section 4): the grid connection, the
# design temperatures, and the snapshots of the master data the site relied
# on, municipality and grid operator. The place itself, with its address and
# coordinates, is the PvSite (model/PvSite.py).

import os
import sqlite3
import datetime
from datetime import date

from model.ModelNode import ModelNode
from model.Contact import Address, Contact
from model import values

EARTHING_SYSTEMS = ("tn_s", "tn_c", "tn_c_s", "tt", "it")


# value of a plugin namespace: obj.ext[namespace][key]
def getExt(obj, namespace, key, default=None):
    value = ((obj.ext or {}).get(namespace) or {}).get(key)
    return default if value is None else value


# Set a value of a plugin namespace. Empty namespaces are removed.
def setExt(obj, namespace, key, value, version=1):
    if obj.ext is None:
        obj.ext = {}
    ns = obj.ext.setdefault(namespace, {"v": version})
    if value is None or value == {} or value == []:
        ns.pop(key, None)
    else:
        ns[key] = value
    if not [k for k in ns if k != "v"]:
        del obj.ext[namespace]


# values of file version 2 which have no field in version 3: ext.gnusolar.v2
def getV2(obj, key, default=None):
    value = (getExt(obj, "gnusolar", "v2") or {}).get(key)
    return default if value is None else value


def setV2(obj, key, value):
    v2 = dict(getExt(obj, "gnusolar", "v2") or {})
    if value is None or value == "":
        v2.pop(key, None)
    else:
        v2[key] = value
    setExt(obj, "gnusolar", "v2", v2)


# The connection to the grid
class Supply(ModelNode):

    _types = {"phases": "int", "voltage": "number", "frequency": "number", "mainFuse": "number"}

    def __init__(self, top=None):
        self._top = top
        self.phases = None
        self.voltage = None             # V between the phases
        self.frequency = None           # Hz
        self.earthingSystem = None      # see EARTHING_SYSTEMS
        self.mainFuse = None            # rating of the house connection fuse, A


class DesignTemperature(ModelNode):

    _types = {"minAmbient": "number", "maxCell": "number"}

    def __init__(self, top=None):
        self._top = top
        self.minAmbient = None
        self.maxCell = None


# Municipality, (politische) Gemeinde: a copy of the master data
class Municipality(ModelNode):

    _types = {"taken": "date", "id": "int", "ext": "json"}

    def __init__(self, top=None):
        self._top = top
        self.taken = None           # date of the copy
        self.id = None              # row in the master data
        self.countryCode = None
        self.stateCode = None
        self.districtCode = None
        self.code = None            # official number of the municipality, BFS-Nr.
        self.name = None
        self.mainContact = Contact(top)
        self.buildingContact = Contact(top)
        self.website = None
        self.ext = {}

    # form for the solar notice or building permit, in the master data
    @property
    def fkFormBuilding(self):
        return getExt(self, "ch", "buildingFormId")

    @fkFormBuilding.setter
    def fkFormBuilding(self, value):
        setExt(self, "ch", "buildingFormId", value)

    def reloadFromDb(self):
        self.fromCode(self.code)

    def fromCode(self, code):
        from Config import Config
        self.code = code

        con = sqlite3.connect(Config.getMasterDbPath())
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT * FROM municipality WHERE code=?"
        res = cur.execute(sql, [code])
        db_row = res.fetchone()

        if db_row:
            self.taken = values.today()
            self.id = db_row["id"]
            self.countryCode = db_row["country_code"]
            self.stateCode = db_row["state_code"]
            self.districtCode = db_row["district_code"]
            self.code = str(db_row["code"])
            self.name = db_row["name"]
            self.fkFormBuilding = db_row["fk_form_building"]
            self.website = db_row["website"]
            self.buildingContact.fromMunicipalityType(self.id, "mun_build")
            self.mainContact.fromMunicipalityType(self.id, "mun_main")

    def getBuildingContact(self):
        contact = Contact()
        contact.fromMunicipalityType(self.id, "mun_build")
        return contact

    def createBuildingForm(self):
        from selenium import webdriver
        from Config import Config, config
        model = self._top

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
            return "Form not found id=" + str(self.fkFormBuilding)

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

        try:
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
        finally:
            # remove temporary attributes, so they dont get serialized
            for key in ("todayIso", "turnOnIso", "fillform_url", "fillform_data"):
                self.__dict__.pop(key, None)

    # Fill the Gebäudeversicherung Zürich form into gvzPath.
    # Returns an error text, or None.
    def createGvzDocumentation(self, gvzPath):
        import fillpdf
        from Config import Config, config
        model = self._top       # used by the form script

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

        try:
            exec(s)

            fillpdf.single_form_fill(form_file, self.fillpdf_data, gvzPath)
        finally:
            # remove temporary attributes, so they dont get serialized
            for key in ("todayIso", "turnOnIso", "fillpdf_data"):
                self.__dict__.pop(key, None)


# Grid operator, power company, EVU, EW, Elektrizitätsversorgungsunternehmen:
# a copy of the master data
class GridOperator(ModelNode):

    _types = {"taken": "date", "id": "int", "ext": "json"}

    def __init__(self, top=None):
        self._top = top
        self.taken = None           # date of the copy
        self.id = None              # row in the master data
        self.name = None
        self.address = Address(top)

        self.mainContact = Contact(top)             # Address of the Headquarters
        self.connectionContact = Contact(top)       # who handles connection requests
        self.ext = {}

    # ---- names of file version 2 -------------------------------------------

    @property
    def tagContact(self):
        return self.connectionContact

    @property
    def vseId(self):
        return getExt(self, "ch", "vseId")

    @vseId.setter
    def vseId(self, value):
        setExt(self, "ch", "vseId", value)

    @property
    def fkFormTag(self):
        return getExt(self, "ch", "tagFormId")

    @fkFormTag.setter
    def fkFormTag(self, value):
        setExt(self, "ch", "tagFormId", value)

    @property
    def fkFormIa(self):
        return getExt(self, "ch", "iaFormId")

    @fkFormIa.setter
    def fkFormIa(self, value):
        setExt(self, "ch", "iaFormId", value)

    @property
    def address1(self):
        return self.address.address1 or ""

    @property
    def address2(self):
        return self.address.address2 or ""

    @property
    def zipCode(self):
        return self.address.zip or ""

    @property
    def city(self):
        return self.address.city or ""

    # ---- master data ------------------------------------------------------

    def reloadFromDb(self):
        self.fromId(self.id)

    def fromId(self, id):
        from Config import Config
        self.id = id

        con = sqlite3.connect(Config.getMasterDbPath())
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT * FROM power_company WHERE id=?"
        res = cur.execute(sql, [id])
        db_row = res.fetchone()

        if db_row:
            self.taken = values.today()
            self.id = db_row["id"]
            self.vseId = db_row["vse_id"]
            self.name = db_row["name"]
            self.address.address1 = db_row["address1"] or None
            self.address.address2 = db_row["address2"] or None
            self.address.zip = str(db_row["zip_code"]) if db_row["zip_code"] else None
            self.address.city = db_row["city"] or None
            self.fkFormTag = db_row["fk_form_tag"]
            self.fkFormIa = db_row["fk_form_ia"]
            if db_row["fk_contact_tag"]:
                self.connectionContact.fromId(db_row["fk_contact_tag"])

    def getTagForm(self):
        from Config import Config
        if not self.fkFormTag:
            return None

        con = sqlite3.connect(Config.getMasterDbPath())
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT * FROM form WHERE id=?"
        res = cur.execute(sql, [self.fkFormTag])
        return res.fetchone()

    def createTag(self, model, tagPath):
        import fillpdf
        import fillxlsx
        from Config import Config, config

        # get the FormTag
        if not self.fkFormTag:
            return "No fkFormTag powerCompany.id=" + str(self.id)

        db_row = self.getTagForm()
        if not db_row:
            return "Form not found id=" + str(self.fkFormTag)

        form_type = db_row["type"]
        form_handler = db_row["handler"]
        form_file = Config.getDataPath() + os.sep + db_row["file"]
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

        try:
            if form_handler == "xlsx_replace":
                self.fillxlsx_sheet = None
                self.fillxlsx_signature = {}
                exec(s)

                # sign the form with the image of the signature
                images = {}
                signature = config.installer_signature
                if signature:
                    if not os.path.exists(signature):
                        return "Signature not found: '" + signature + "'"
                    for cells, scale in self.fillxlsx_signature.items():
                        images[cells] = (signature, scale)

                fillxlsx.single_form_fill(form_file, self.fillxlsx_data, tagPath, self.fillxlsx_sheet, images)
            else:
                exec(s)
                fillpdf.single_form_fill(form_file, self.fillpdf_data, tagPath)
        finally:
            # remove temporary attributes, so they dont get serialized
            for key in ("todayIso", "turnOnIso", "fillxlsx_sheet", "fillxlsx_data", "fillxlsx_signature",
                        "fillpdf_data"):
                self.__dict__.pop(key, None)

