#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import os
import subprocess
import json 
import re
import pathlib

from datetime import date

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Ui.Preferences import *

class Config():
    def __init__(self):
        self.configPath = ""            # the Path of this file
        self.projectRoot = ""
        self.templatePath = ""          # Vorlage Verzeichnis
        
        self.nextQuoteNumber = 0
        self.nextInvoiceNumber = 0
        
        # Installer info
        self.installer_company = ""
        self.installer_firstName = ""
        self.installer_lastName = ""
        self.installer_street = ""
        self.installer_streetNumber = ""
        self.installer_zip = ""
        self.installer_city = ""
        self.installer_phone = ""
        self.installer_email = ""
        self.installer_vat = ""
        self.installer_bankName = ""
        self.installer_bankIban = ""
        self.installer_bankIid = ""
        self.installer_bankBic = ""

    def write(self):
        f = open(self.configPath, "w")
        s = json.dumps(self.__dict__, indent=4, sort_keys=True)
        f.write(s)
        f.close()

    def load(self):
        from os.path import expanduser
        home = expanduser("~")
        configDir = home + os.sep + ".gnusolar"
        self.configPath = configDir + os.sep + "config.json"
        print("Config File: " + self.configPath)

        if not os.path.exists(configDir):
            os.makedirs(configDir)
        
        # create default config file
        if not os.path.exists(self.configPath):
            self.write()

        f = open(self.configPath, "r")
        ret = json.load(f)
        f.close()
        
        self._copyOver(self, ret)
        #self.__dict__ = ret.copy()

    def show(self):
        self.window = QDialog()
        self.ui = Ui_Preferences()
        self.ui.setupUi(self.window)
        
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.configAccepted)
        self.ui.projectRoot.setText(self.projectRoot)
        self.ui.templatePath.setText(self.templatePath)
        self.ui.nextQuoteNumber.setText(str(self.nextQuoteNumber))
        self.ui.nextInvoiceNumber.setText(str(self.nextInvoiceNumber))

        self.ui.installer_company.setText(self.installer_company)
        self.ui.installer_firstName.setText(self.installer_firstName)
        self.ui.installer_lastName.setText(self.installer_lastName)
        self.ui.installer_street.setText(self.installer_street)
        self.ui.installer_streetNumber.setText(self.installer_streetNumber)
        self.ui.installer_zip.setText(self.installer_zip)
        self.ui.installer_city.setText(self.installer_city)
        self.ui.installer_phone.setText(self.installer_phone)
        self.ui.installer_email.setText(self.installer_email)

        self.ui.installer_vat.setText(self.installer_vat)
        self.ui.installer_bankName.setText(self.installer_bankName)
        self.ui.installer_bankIban.setText(self.installer_bankIban)
        self.ui.installer_bankIid.setText(self.installer_bankIid)
        self.ui.installer_bankBic.setText(self.installer_bankBic)

        self.window.show()
        
    def configAccepted(self):
        self.projectRoot = self.ui.projectRoot.text()
        self.templatePath = self.ui.templatePath.text()
        self.nextQuoteNumber = int(self.ui.nextQuoteNumber.text())
        self.nextInvoiceNumber = int(self.ui.nextInvoiceNumber.text())

        self.installer_company = self.ui.installer_company.text()
        self.installer_firstName = self.ui.installer_firstName.text()
        self.installer_lastName = self.ui.installer_lastName.text()
        self.installer_street = self.ui.installer_street.text()
        self.installer_streetNumber = self.ui.installer_streetNumber.text()
        self.installer_zip = self.ui.installer_zip.text()
        self.installer_city = self.ui.installer_city.text()
        self.installer_phone = self.ui.installer_phone.text()
        self.installer_email = self.ui.installer_email.text()

        self.installer_vat = self.ui.installer_vat.text()
        self.installer_bankName = self.ui.installer_bankName.text()
        self.installer_bankIban = self.ui.installer_bankIban.text()
        self.installer_bankIid = self.ui.installer_bankIid.text()
        self.installer_bankBic = self.ui.installer_bankBic.text()
        
        del self.ui
        del self.window

        self.write()

    def getNextInvoiceName(self):
        today = date.today()
        nextName = "R%04d-%02d-%04d" % (today.year, today.month, self.nextInvoiceNumber)
        return nextName

    def getNextQuoteName(self):
        today = date.today()
        nextName = "O%04d-%02d-%04d" % (today.year, today.month, self.nextQuoteNumber)
        return nextName

    def _copyOver(self, src, dest):
        for key, value in src.__dict__.items():

            if not key in dest:
                continue
                
            if hasattr(value, "__dict__") and isinstance(value.__dict__, dict):
                self._copyOver(src.__dict__[key], dest[key])
            else:
                src.__dict__[key] = dest[key]

    def looseDateToIso(date_in):
        month_names = {
            "Januar"  : "01",
            "Februar" : "02",
            "März"    : "03",
            "April"   : "04",
            "Mai"     : "05" ,
            "Juni"    : "06" ,
            "Juli"    : "07" ,
            "August"  : "08" ,
            "September" : "09" ,
            "Setpember" : "09" ,
            "Oktober" : "10" ,
            "November" : "11" ,
            "Dezember" : "12",
            "Jan" : "01",
            "Feb" : "02",
            "Mar" : "03",
            "Mrz" : "03",
            "Apr" : "04",
            "Mai" : "05",
            "Jun" : "06",
            "Jul" : "07",
            "Aug" : "08",
            "Sep" : "09",
            "Okt" : "10",
            "Nov" : "11",
            "Dez" : "12"
        }
        date_in = date_in.strip()
        #print(date_in)

        # check already iso
        pat = re.compile('\d\d\d\d-\d\d-\d\d', re.DOTALL)
        m = pat.match(date_in)
        if m:
            return date_in

        # dd.mm.yyyy
        pat = re.compile('(\d\d)\.\W?(\d\d)\.\W?(\d\d\d\d)', re.DOTALL)
        m = pat.match(date_in)
        if m:
            date_out = m.group(3) + "-" + m.group(2) + "-" + m.group(1)
            #print(date_out)
            return date_out


        # dd.mm.yy
        pat = re.compile('(\d\d)\.\W?(\d\d)\.\W?(\d\d)', re.DOTALL)
        m = pat.match(date_in)
        if m:
            date_out = "20" + m.group(3) + "-" + m.group(2) + "-" + m.group(1)
            #print(date_out)
            return date_out

        pat = re.compile('(\d{1,2})\.?\W?(\w*)\.?\W?(\d\d\d\d)', re.DOTALL)
        m = pat.match(date_in)
        if m:
            monthname = m.group(2)
            month = month_names[monthname]
            day = m.group(1)
            if len(day) == 1:
                day = "0" + day
            date_out = m.group(3) + "-" + month + "-" + day
            
            #print(date_out)
            return date_out

        pat = re.compile('\W?(\w*)\.?\W?(\d\d\d\d)', re.DOTALL)
        m = pat.match(date_in)
        if m:
            monthname = m.group(1)
            month = month_names[monthname]
            date_out = m.group(2) + "-" + month + "-01"
            return date_out

        # unkown date format
        return ""

    # convert the pdf to plain text
    def pdfToText(file_name):
        # check for pdftotext command
        pdftotext = False
        charset = "utf-8"
        if os.name == "posix":
            # search for pdftotext under linux
            pdftotext = subprocess.check_output(["which", "pdftotext"], stderr=subprocess.STDOUT).decode("utf-8")
            pdftotext = pdftotext.strip()

        if os.name == "nt":
            charset = "cp1252"
            # search for pdftotext under windows
            paths = (
                "C:\\Program Files\\Xpdf\\bin32\\pdftotext.exe",
                "C:\\Program Files\\Xpdf\\bin64\\pdftotext.exe",
            )
            for pdftotext in paths:
                if os.path.isfile(pdftotext):
                    break
                    
        if pdftotext == False:
            raise Exception("Platform '" + os.name + "' not supported")
        
        if not os.path.isfile(pdftotext):
            raise Exception("This programm requires the 'pdftotext' command\nOn Windows install the Xpdf program")

        if not os.path.isfile(file_name):
            raise Exception("File not found: '" + file_name + "'")

        # convert the pdf to plain text
        cmd = "\"" + pdftotext + "\" \"" + file_name + "\" - -layout -nopgbrk"
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(charset)

    def getDataPath():
        path = str(pathlib.Path(__file__).parent.absolute()) + os.sep + "data"
        return path

    def getMasterDbPath():
        path = Config.getDataPath() + os.sep + "masterdata.db"
        return path

    def getAppVersion():
        return "git_2023-07-01"
        
    # returns the directory where all templates are stored
    def getTemplateDir(self):
        if os.path.isdir(self.templatePath):
            return self.templatePath
        ret = Config.getDataPath() + os.sep + "ch" + os.sep + "templates"
        return ret
