#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
import os
import json
import codecs
import shutil

from datetime import date
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QTableWidgetItem, QMessageBox, QFileDialog, QLineEdit, QPlainTextEdit
from PyQt5 import QtCore, QtGui, QtWidgets

from Ui.SolarProject import *
from Ui.Preferences import *

from model.PvProject import *

from Config import Config

# TODO: Where to put generally usefull functions?

import subprocess
import sys

if sys.platform == 'darwin':
    def openFolder(path):
        os.system("open \"" + path + "\"")
elif sys.platform == 'win32':
    def openFolder(path):
        os.system("explorer \"" + path + "\"")
else:   # Default Linux
    def openFolder(path):
        os.system("xdg-open \"" + path + "\"")

class SolarProject(QApplication):
    def __init__(self, *args):
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
        self.ui.copyClientAddressFromLocation.clicked.connect(self.action_copyClientAddressFromLocation)
        self.ui.updateFromAddress.clicked.connect(self.action_updateFromAddress)
        self.ui.createQuote.clicked.connect(self.action_createQuote)
        self.ui.createTag.clicked.connect(self.action_createTag)

        self.ui.pb_finalInvoiceSent.clicked.connect(self.action_finalInvoiceSent)
        self.ui.pb_orderRejected.clicked.connect(self.action_orderRejected)
        self.ui.pb_archived.clicked.connect(self.action_archived)
       
        # Arguments:
        #   First argument: Path to the Pv-Project File
        self.path = ""          # path = "" means new project
        self.model = PvProject()       # the PvProject Model
        self.unsavedChanges = False

        if len(args[0]) >= 2:
            self.openFile(args[0][1])

        # connect all pvp_ fields with action_Change
        for key, value in self.ui.__dict__.items():
            if not key.startswith("pvp_"):
                continue
            self.ui.__dict__[key].textChanged.connect(self.action_changed)

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
        openFolder(folder)

    def action_copyClientAddressFromLocation(self):
        self.updateModel()
        self.model.owner.street       = self.model.plantLocation.street
        self.model.owner.streetNumber = self.model.plantLocation.streetNumber
        self.model.owner.zip          = self.model.plantLocation.zip
        self.model.owner.city         = self.model.plantLocation.city
        self.updateUi()

    def action_updateFromAddress(self):
        self.updateModel()
        self.model.updateFromAddress()
        self.updateUi()

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

    def action_createQuote(self):
        global config
        
        quoteTemplatePath = config.templatePath + os.sep + "off" + os.sep + "template_quote.odt"
        if not os.path.exists(quoteTemplatePath):
            QtWidgets.QMessageBox.warning(None, 'Offerte Vorlage nicht gefunden', 'Pfad = ' + quoteTemplatePath)
            return
        
        nextQuoteName = config.getNextQuoteName() + ".odt"
        projectDir = os.path.dirname(self.path)
        if not os.path.isdir(projectDir):
            QtWidgets.QMessageBox.warning(None, 'Offerte erstellen', 'Pfad nicht gefunden\n' + self.path)
            return

        quoteDir =  projectDir + os.sep + "off"
        quotePath = quoteDir + os.sep + nextQuoteName
        if not os.path.isdir(quoteDir):
            os.makedirs(quoteDir)
            
        # copy the file
        shutil.copy(quoteTemplatePath, quotePath)
        
        config.nextQuoteNumber = config.nextQuoteNumber + 1
        config.write()

        openFolder(quotePath)

    # Erzeuge Anschlussgesuch
    def action_createTag(self):
        global config
        print("TODO: createTag")
        
        
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
        title = "Photovoltaic Project"
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

            el = self.model
            for attr in attrs:
                el = el.__dict__[attr]
            
            if isinstance(self.ui.__dict__[key], QLineEdit):
                self.ui.__dict__[key].setText(el)
            if isinstance(self.ui.__dict__[key], QPlainTextEdit):
                self.ui.__dict__[key].setPlainText(el)


        
    # Updates the Data Model from the User Interface
    # Iterates through all widgets and searches for pvp_* named Widgets
    def updateModel(self):
        for key, value in self.ui.__dict__.items():
            if not key.startswith("pvp_"):
                continue
            
            attrs = key.split("_")
            attrs.pop(0)
            last = attrs.pop()
            
            el = self.model
            for attr in attrs:
                el = el.__dict__[attr]
            
            if isinstance(self.ui.__dict__[key], QLineEdit):
                el.__dict__[last] = self.ui.__dict__[key].text()
            if isinstance(self.ui.__dict__[key], QPlainTextEdit):
                el.__dict__[last] = self.ui.__dict__[key].toPlainText()


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
    
