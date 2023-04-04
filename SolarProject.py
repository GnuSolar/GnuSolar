#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
import os

sitepack = os.path.join(os.path.dirname(__file__), "site-packages")
sys.path.insert(0, sitepack)

import json
import codecs
import shutil

from relatorio.templates.opendocument import Template

from datetime import date
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QTableWidgetItem, QMessageBox, QFileDialog, QLineEdit, QPlainTextEdit, QComboBox
from PyQt5 import QtCore, QtGui, QtWidgets

from Ui.SolarProject import *
from Ui.Preferences import *

from model.PvProject import *

from Config import Config

# TODO: Where to put generally usefull functions?

import subprocess

if sys.platform == 'darwin':
    def openFolder(path):
        os.system("open \"" + path + "\"")
elif sys.platform == 'win32':
    def openFolder(path):
        os.system("explorer \"" + path + "\"")
else:   # Default Linux
    def openFolder(path):
        os.system("xdg-open \"" + path + "\"")

def openFolderIfExists(path):
    if not path or not os.path.exists(path):
        return

    openFolder(path)
    
def composeEmail(to, subject, body, attachments=[]):
    cmd = "thunderbird -compose \""
    cmd += "to='" + to + "',"
    cmd += "subject='" + subject + "',"
    cmd += "body='" + body + "',"
    for att in attachments:
        cmd += "attachment='" + att + "',"
    cmd += "\""
    
    os.system(cmd)

def templateCopyReplace(src, dest, model):
    basic = Template(source='', filepath=src)
    basic_generated = basic.generate(o=model).render()

    f = open(dest, 'wb')
    f.write(basic_generated.getvalue())
    f.close()
    
    
class SolarProject(QApplication):
    def __init__(self, *args):
        global config
        
        QApplication.__init__(self, *args)
        self.window = QMainWindow()

        self.ui = Ui_PvProject()
        self.ui.setupUi(self.window)

        self.ui.action_New.triggered.connect(self.action_new)
        self.ui.action_Open.triggered.connect(self.action_open)
        self.ui.action_Save.triggered.connect(self.action_save)
        self.ui.action_Save_As.triggered.connect(self.action_saveAs)
        self.ui.action_Quit.triggered.connect(self.action_quit)
        self.ui.action_Preferences.triggered.connect(self.action_preferences)

        self.ui.openProjectFolder.clicked.connect(self.action_openProjectFolder)
        self.ui.copyClientAddressFromBuilding.clicked.connect(self.action_copyClientAddressFromBuilding)
        self.ui.updateFromAddress.clicked.connect(self.action_updateFromAddress)
        self.ui.createQuote.clicked.connect(self.action_createQuote)
        self.ui.createPartialInvoice.clicked.connect(self.action_createPartialInvoice)
        self.ui.createFinalInvoice.clicked.connect(self.action_createFinalInvoice)
        self.ui.createDocumentation.clicked.connect(self.action_createDocumentation)
        self.ui.createMundpp.clicked.connect(self.action_createMundpp)
        self.ui.createTag.clicked.connect(self.action_createTag)
        self.ui.createBuildingForm.clicked.connect(self.action_createBuildingForm)
        self.ui.composeBuildingEmail.clicked.connect(self.action_composeBuildingEmail)
        self.ui.composeTagEmail.clicked.connect(self.action_composeTagEmail)
        self.ui.composeEmailOwner.clicked.connect(self.action_composeEmailOwner)

        self.ui.pb_finalInvoiceSent.clicked.connect(self.action_finalInvoiceSent)
        self.ui.pb_orderRejected.clicked.connect(self.action_orderRejected)
        self.ui.pb_archived.clicked.connect(self.action_archived)
       
        # Arguments:
        #   First argument: Path to the Pv-Project File
        self.path = ""          # path = "" means new project
        self.model = PvProject()       # the PvProject Model
        self.model.config = config
        self.unsavedChanges = False

        if len(args[0]) >= 2:
            self.openFile(args[0][1])

        # connect all pvp_ fields with action_Change
        for key, value in self.ui.__dict__.items():
            if not key.startswith("pvp_"):
                continue
            el = self.ui.__dict__[key]

            if isinstance(el, QLineEdit):
                el.textChanged.connect(self.action_changed)
            elif isinstance(el, QPlainTextEdit):
                el.textChanged.connect(self.action_changed)
            elif isinstance(el, QComboBox):
                el.currentIndexChanged.connect(self.action_changed)
            else:
                raise Exception(type(el) + " not implemented")

        self.unsavedChanges = False
        self.updateWindowTitle()
        
        self.window.show()

    def action_new(self):
        QtWidgets.QMessageBox.information(None, 'Not implemented', 'Not implemented')

    def action_open(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self.window, "QFileDialog.getOpenFileName()", "", "Photovoltaic Project (*.pvp)", options=options)
        
        self.openFile(fileName)

    def action_save(self):
        self.saveFile()

    def action_saveAs(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self.window, "QFileDialog.getSaveFileName()", "", "Photovoltaic Project (*.pvp)", options=options)

        self.path = fileName
        self.saveFile()

    def action_quit(self):
        exit()

    def action_openProjectFolder(self):
        if self.path == "":
            return
        folder = os.path.dirname(self.path)
        openFolderIfExists(folder)

    def action_copyClientAddressFromBuilding(self):
        self.updateModel()
        self.model.owner.street       = self.model.building.street
        self.model.owner.streetNumber = self.model.building.streetNumber
        self.model.owner.zip          = self.model.building.zip
        self.model.owner.city         = self.model.building.city
        self.updateUi()

    def action_updateFromAddress(self):
        self.updateModel()
        ret = self.model.updateFromAddress()
        self.updateUi()
        if isinstance(ret, str):
            QtWidgets.QMessageBox.warning(None, 'UpdatefromAddress Error', 'Meldung = ' + ret)
        

    def action_finalInvoiceSent(self):
        now = date.today()
        self.model.progress.finalInvoiceSent = now.isoformat()
        self.updateUi()

    def action_orderRejected(self):
        now = date.today()
        self.model.progress.orderRejected = now.isoformat()
        self.updateUi()

    def action_archived(self):
        now = date.today()
        self.model.progress.archived = now.isoformat()
        self.updateUi()

    def action_changed(self):
        if self.unsavedChanges:
            return
        self.unsavedChanges = True
        self.updateWindowTitle()

    def action_preferences(self):
        global config
        
        config.show()

    def createFromTemplate(self, templateType):
        templates = {
            "partial_invoice" : {
                "in_path"  : "fin" + os.sep + "partial_invoice.odt",
                "out_dir"  : "fin",
                "out_file" : config.getNextInvoiceName() + ".odt"
            },
            "final_invoice" : {
                "in_path"  : "fin" + os.sep + "final_invoice.odt",
                "out_dir"  : "fin",
                "out_file" : config.getNextInvoiceName() + ".odt"
            },
            "quote" : {
                "in_path"  : "off" + os.sep + "quote.odt",
                "out_dir"  : "off",
                "out_file" : config.getNextQuoteName() + ".odt"
            },
            "documentation" : {
                "in_path"  : "doc" + os.sep + "documentation.odt",
                "out_dir"  : "doc",
                "out_file" : "Dokumentation.odt"
            },
            "mundpp" : {
                "in_path"  : "evu" + os.sep + "MP_PV_Final_20190301_de.ods",
                "out_dir"  : "evu",
                "out_file" : "MP_PV.ods"
            }
        }

        ret = Config.getDataPath() + os.sep + "ch" + os.sep + "templates"

        template = templates[templateType]
        
        templatePath = ""
        defaultPath = Config.getDataPath() + os.sep + "ch" + os.sep + "templates" + os.sep + template["in_path"]
        localPath = config.templatePath + os.sep + template["in_path"]
        # first search template in  "local", config path
        if os.path.exists(localPath):
            templatePath = localPath

        # then default
        elif os.path.exists(defaultPath):
            templatePath = defaultPath
        else:
            QtWidgets.QMessageBox.warning(None, templateType + ' Vorlage nicht gefunden', 'def Pfad = ' + defaultPath)
            return
        
        projectDir = os.path.dirname(self.path)
        if not os.path.isdir(projectDir):
            QtWidgets.QMessageBox.warning(None, templateType + ' erstellen', 'Pfad nicht gefunden\n' + self.path)
            return

        outDir =  projectDir + os.sep + template["out_dir"]
        outPath = outDir + os.sep + template["out_file"]
        if not os.path.isdir(outDir):
            os.makedirs(outDir)

        self.model._invoiceName = config.getNextInvoiceName()
        self.model._quoteName = config.getNextQuoteName()
        today = date.today()
        self.model._todayIso = today.isoformat()
        templateCopyReplace(templatePath, outPath, self.model)
        del self.model._invoiceName
        del self.model._quoteName
        del self.model._todayIso
        
        return outPath

    def action_createQuote(self):
        global config
        
        quotePath = self.createFromTemplate("quote")
        
        config.nextQuoteNumber = config.nextQuoteNumber + 1
        config.write()

        openFolderIfExists(quotePath)

    # Create Partial Invoice
    def action_createPartialInvoice(self):
        global config

        invoicePath = self.createFromTemplate("partial_invoice")
        
        config.nextInvoiceNumber = config.nextInvoiceNumber + 1
        config.write()

        openFolderIfExists(invoicePath)

    # Create Final Invoice
    def action_createFinalInvoice(self):
        global config

        invoicePath = self.createFromTemplate("final_invoice")
        
        config.nextInvoiceNumber = config.nextInvoiceNumber + 1
        config.write()

        openFolderIfExists(invoicePath)

    # Create Documentation
    def action_createDocumentation(self):
        documentationPath = self.createFromTemplate("documentation")
        openFolderIfExists(documentationPath)

    # Create M+PP
    def action_createMundpp(self):
        documentationPath = self.createFromTemplate("mundpp")
        openFolderIfExists(documentationPath)

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
        self.updateUi()

    # Erzeuge Solarmeldung
    def action_createBuildingForm(self):
        ret = self.model.municipality.createBuildingForm(self.model)
        if isinstance(ret, str):
            QtWidgets.QMessageBox.information(None, 'Error Creating TAG', ret)
            return

    # Sende Solarmeldung
    def action_composeBuildingEmail(self):
        global config
        
        to = self.model.municipality.buildingContact.email
        b = self.model.building
        subject = "Solarmeldung PV-Anlage " + b.street + " " + b.streetNumber + " in " + b.city
        body = "Guten Tag\n\nIm Anhang finden Sie die Solarmeldung für eine PV-Anlage in " + b.city + " sowie die zusätzlich benötigten Unterlagen.\n"
        body += "\nmit freundlichen Grüssen\n\n" + config.installer_firstName + " " + config.installer_lastName
        att = [""]
        composeEmail(to, subject, body, att)

    # Sende Tag
    def action_composeTagEmail(self):
        global config
        
        to = self.model.powerCompany.tagContact.email
        b = self.model.building
        subject = "TAG PV-Anlage " + b.street + " " + b.streetNumber + " in " + b.city
        body = "Guten Tag\n\nIm Anhang finden Sie das Anschlussgesuch für eine PV-Anlage in " + b.city + " sowie die zusätzlich benötigten Unterlagen.\n"
        body += "\nmit freundlichen Grüssen\n\n" + config.installer_firstName + " " + config.installer_lastName
        att = [""]
        composeEmail(to, subject, body, att)

    # Sende Tag
    def action_composeEmailOwner(self):
        global config
        
        to = self.model.owner.email
        composeEmail(to, "", "")


    # open a Project with a path
    def openFile(self, pvpPath):
        if not pvpPath:
            return
            
        # check if path exists
        if not os.path.exists(pvpPath):
            print("File not found: '" + pvpPath + "'")
            return
        
        # valid pvp Project?
        self.path = pvpPath
        self.model.open(pvpPath)
        self.updateUi();    
        self.updateWindowTitle()
    
    def saveFile(self):
        self.updateModel()
        self.model.saveAs(self.path)
        self.unsavedChanges = False
        self.updateWindowTitle()
        
    def updateWindowTitle(self):
        title = "Photovoltaic Project - " + Config.getAppVersion()
        if self.path != "":
            arr = os.path.split(self.path)
            file = arr[1]
            path = arr[0]
            title = file + " - " + path + " - " + title
        else:
            title = "untitled - " + title
        if self.unsavedChanges:
            title = "*" + title
        self.window.setWindowTitle(title)

    # Updates the User Interface from the Model
    # Iterates through all widgets and searches for pvp_* named Widgets
    def updateUi(self):

        for key, value in self.ui.__dict__.items():
            if not key.startswith("pvp_"):
                continue
            
            attrs = key.split("_")
            attrs.pop(0)

            modelEl = self.model
            for attr in attrs:
                modelEl = modelEl.__dict__[attr]
            uiEl = self.ui.__dict__[key]
            
            if isinstance(uiEl, QLineEdit):
                uiEl.setText(modelEl)
            elif isinstance(uiEl, QPlainTextEdit):
                uiEl.setPlainText(modelEl)
            elif isinstance(uiEl, QComboBox):
                uiEl.setCurrentText(modelEl)
            else:
                raise Exception(str(type(uiEl)) + " not implemented")
            
    # Updates the Data Model from the User Interface
    # Iterates through all widgets and searches for pvp_* named Widgets
    def updateModel(self):
        for key, value in self.ui.__dict__.items():
            if not key.startswith("pvp_"):
                continue
            
            attrs = key.split("_")
            attrs.pop(0)
            last = attrs.pop()
            
            modelEl = self.model
            for attr in attrs:
                modelEl = modelEl.__dict__[attr]
            uiEl = self.ui.__dict__[key]

            if isinstance(uiEl, QLineEdit):
                modelEl.__dict__[last] = uiEl.text()
            elif isinstance(uiEl, QPlainTextEdit):
                modelEl.__dict__[last] = uiEl.toPlainText()
            elif isinstance(uiEl, QComboBox):
                modelEl.__dict__[last] = uiEl.currentText()
            else:
                raise Exception(str(type(uiEl)) + " not implemented")

def checkEnv():
    PY2 = sys.version_info[0] == 2
    # If we are on python 3 we will verify that the environment is
    # sane at this point of reject further execution to avoid a
    # broken script.
    if not PY2:
        try:
            import locale
            fs_enc = codecs.lookup(locale.getpreferredencoding()).name
        except Exception:
           fs_enc = 'ascii'
        if fs_enc == 'ascii':
            raise RuntimeError('Eigentool will abort further execution '
                               'because Python 3 was configured to use '
                               'ASCII as encoding for the environment. '
                               'Either switch to Python 2 or consult '
                               'http://bugs.python.org/issue13643 '
                               'for mitigation steps.')


def main(args):
    global solarproject
    global config

    checkEnv()

    config = Config()
    config.load()

    solarproject = SolarProject(args)
    solarproject.exec_()

if __name__ == "__main__":
    main(sys.argv)
    
