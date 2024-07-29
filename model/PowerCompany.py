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

from Config import *
from GnuSolar import *

class PowerCompany:
    
    def __init__(self):
        self.id = None
        self.vseId = None
        self.name = None
        self.address1 = None
        self.address2 = None
        self.zipCode = None
        self.city = None

        self.mainContact = Contact()        # Address of the Headquarters
        self.mainContact.role = "pow_main"

        self.tagContact = Contact()
        self.tagContact.role = "pow_tag"

        self.fkContactTag = None
        self.fkFormTag = None
        self.fkFormIa = None
        
    def reloadFromDb(self):
        self.fromId(self.id)

    def fromId(self, id):
        self.id = id

        con = sqlite3.connect(Config.getMasterDbPath())
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT * FROM power_company WHERE id=?"
        res = cur.execute(sql, [id])
        db_row = res.fetchone()

        if db_row:
            self.id = db_row["id"]
            self.vseId = db_row["vse_id"]
            self.name = db_row["name"]
            self.address1 = db_row["address1"]
            self.address2 = db_row["address2"]
            self.zipCode = db_row["zip_code"]
            self.city = db_row["city"]
            self.fkContactTag = db_row["fk_contact_tag"]
            self.fkFormTag = db_row["fk_form_tag"]
            self.fkFormIa = db_row["fk_form_ia"]
            self.tagContact.fromId(self.fkContactTag)

    def getTagContact(self):
        if not self.fkContactTag:
            return "No Tag Contact in Masterdata"
        
        contact = Contact()
        contact.fromId(self.fkContactTag)
        return contact

    def createTag(self, model, tagPath):
        # get the FormTag
        if not self.fkFormTag:
            return "No fkFormTag powerCompany.id=" + str(self.id)
            
        con = sqlite3.connect(Config.getMasterDbPath())
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT * FROM form WHERE id=?"
        res = cur.execute(sql, [self.fkFormTag])
        db_row = res.fetchone()

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

        exec(s)
        
        fillpdf.single_form_fill(form_file, self.fillpdf_data, tagPath)

        # remove temporary attributes, so they dont get serialized
        del self.turnOnIso
        del self.todayIso
        del self.fillpdf_data

    # Erzeuge Anschlussgesuch
    def action_createTag(self):
        global config
        
        # assemble the path
        today = date.today()
        tagName = "%04d-%02d-%02d_tag_fill.pdf" % (today.year, today.month, today.day)

        projectDir = os.path.dirname(self.path)
        tagDir =  projectDir + os.sep + "evu"
        tagPath = tagDir + os.sep + tagName
        if not os.path.isdir(tagDir):
            os.makedirs(tagDir)
        
        ret = self.model.powerCompany.createTag(self.model, tagPath)
        if isinstance(ret, str):
            QtWidgets.QMessageBox.information(None, 'Error Creating TAG', ret)
            return
            
        openFolderIfExists(tagPath)
        now = date.today()
        self.model.progress.tagSent = now.isoformat()
        GnuSolar.updateUi(self.ui, self.model, "pvp")

    # Sende Tag
    def action_composeTagEmail(self):
        global config
        
        to = self.model.powerCompany.tagContact.email
        b = self.model.building
        subject = "TAG PV-Anlage " + b.street + " " + b.streetNumber + " in " + b.city
        body = "Guten Tag\n\nIm Anhang finden Sie das Anschlussgesuch für eine PV-Anlage in " + b.city + " sowie die zusätzlich benötigten Unterlagen.\n"
        body += "\nmit freundlichen Grüssen\n\n" + config.installer_firstName + " " + config.installer_lastName
        att = [""]
        composeEmail(config.installer_email, to, subject, body, att)

    def getTreeCaption(self):
        return "Stromversorger"

    # Create M+PP
    def action_createMundpp(self):
        documentationPath = createFromTemplate("mundpp", self.path, self.model)
        openFolderIfExists(documentationPath)

    def initUi(self, ui):
        ui.createMundpp.clicked.connect(self.action_createMundpp)
        ui.createTag.clicked.connect(self.action_createTag)
        ui.composeTagEmail.clicked.connect(self.action_composeTagEmail)

