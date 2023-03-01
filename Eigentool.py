#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
import os
import json 
import codecs
import io
import traceback

from datetime import date

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Ui.MainWindow import *

from model.PvProject import *

from Config import Config


class Eigentool(QApplication):
    def __init__(self, *args):
        QApplication.__init__(self, *args)
        self.window = QMainWindow()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.window)
        
        self.fillTableProjects()
        self.fillLastNames()

        self.ui.action_Preferences.triggered.connect(self.openConfig)
        self.ui.createProject.clicked.connect(self.createProject)
        self.ui.tableWidgetProjects.doubleClicked.connect(self.projectOpen)

        self.ui.filterStatus.currentTextChanged.connect(self.filterStatusChanged)

        title = "Eigentool - " + Config.getAppVersion()
        self.window.setWindowTitle(title)
        
        self.window.show()

    # search some last file names in the project directory
    def fillLastNames(self):
        global config

        highestPictureName = ""
        highestPicturePath = ""
        highestPictureNumber = 0

        highestQuoteName = ""
        highestQuotePath = ""
        highestQuoteNumber = 0
        
        highestInvoiceName = ""
        highestInvoicePath = ""
        highestInvoiceNumber = 0

        
        # get all filenames into array
        
        # walk filenames and check for higher pattern
        for dirname, dirnames, filenames in os.walk(config.projectRoot):
            for filename in filenames:
                # a quote ?
                if filename.startswith("O20"):
                    arr = filename.split(".")
                    if len(arr) != 2:
                        continue
                    
                    arr2 = arr[0].split("-")
                    if len(arr2) != 3:
                        continue
                    
                    # appending anything with undersocres is valid
                    arr3 = arr2[2].split("_")
                    quoteNumberStr = arr3[0]
                    
                    if len(quoteNumberStr) != 4:
                        continue
                    
                    quoteNumber = 0
                    try:
                        quoteNumber = int(quoteNumberStr)
                    except Exception:
                        print("malformed quote filename: " + dirname + "/" + filename)
                                
                    # quotes over 1000 are for temporary workers
                    if quoteNumber > 1000:
                        continue
                        
                    if highestQuoteNumber > quoteNumber:
                        continue
                        
                    highestQuoteNumber = quoteNumber
                    highestQuoteName = filename
                    highestQuotePath = dirname + "/" + filename
                    
                    continue

                # an invoice
                if filename.startswith("R20"):
                    arr = filename.split(".")
                    if len(arr) != 2:
                        continue
                    
                    arr2 = arr[0].split("-")
                    if len(arr2) != 3:
                        continue
                    
                    # appending anything with underscores is valid
                    arr3 = arr2[2].split("_")
                    invoiceNumberStr = arr3[0]
                    
                    if len(invoiceNumberStr) != 4:
                        continue
                    
                    invoiceNumber = 0
                    try:
                        invoiceNumber = int(invoiceNumberStr)
                    except Exception:
                        print("malformed invoice filename: " + dirname + "/" + filename)
                                
                    # invoices over 5000 are for temporary workers
                    if invoiceNumber > 5000:
                        continue
                        
                    if highestInvoiceNumber > invoiceNumber:
                        continue
                        
                    highestInvoiceNumber = invoiceNumber
                    highestInvoiceName = filename
                    highestInvoicePath = dirname + "/" + filename
                    
                    continue
                    
                # a picture
                if filename.startswith("IMG_") or filename.startswith("img_"):
                    
                    #remove extension
                    arr = filename.split(".")
                    if len(arr) != 2:
                        continue
                    
                    arr2 = arr[0].split("_")
                    if len(arr2) != 3:
                        continue

                    if len(arr2[1]) != 8 or len(arr2[2]) != 6:
                        print("malformed picture filename: " + dirname + "/" + filename)
                        continue

                    pictureNumber = 0
                    try:
                        pictureNumber = int(arr2[1] + arr2[2])
                    except Exception:
                        print("malformed picture filename: " + dirname + "/" + filename)

                    if highestPictureNumber > pictureNumber:
                        continue
                        
                    highestPictureNumber = pictureNumber
                    highestPictureName = filename
                    highestPicturePath = dirname + "/" + filename
                    
                    continue
                    
        self.ui.lastPictureName.setText(highestPicturePath)
        self.ui.lastQuoteName.setText(highestQuotePath)
        self.ui.lastInvoiceName.setText(highestInvoicePath)
        
        config.nextQuoteNumber = highestQuoteNumber+1
        config.nextInvoiceNumber = highestInvoiceNumber+1
            
        config.write()
        
        self.ui.nextQuoteName.setText(config.getNextQuoteName())
        self.ui.nextInvoiceName.setText(config.getNextInvoiceName())
    
    def fillTableProjects(self, state=""):
        global config
        
        # recursive scan all folders
        if not os.path.exists(config.projectRoot):
            print("path not found: " + config.projectRoot)
            return

        for dirname, dirnames, filenames in os.walk(config.projectRoot):
            for filename in filenames:
                if filename == "plant.pvp":
                    fn = os.path.join(dirname, filename)
                    self.addProjectEntry(dirname, fn, state)

            # Advanced usage:
            # editing the 'dirnames' list will stop os.walk() from recursing into there.
            if '.git' in dirnames:
                # don't go into any .git directories.
                dirnames.remove('.git')
        
        self.ui.tableWidgetProjects.resizeColumnsToContents()

    def projectsShowAll(self):
        self.ui.tableWidgetProjects.setRowCount(0)
        self.fillTableProjects()

    def projectsShowActiv(self):
        self.ui.tableWidgetProjects.setRowCount(0)
        self.fillTableProjects("activ")

    def projectsShowArchived(self):
        self.ui.tableWidgetProjects.setRowCount(0)
        self.fillTableProjects("archived")

    def projectsInactiv(self):
        self.ui.tableWidgetProjects.setRowCount(0)
        self.fillTableProjects("inactiv")

    def filterStatusChanged(self):
        filterState = self.ui.filterStatus.currentText()
        rowN = self.ui.tableWidgetProjects.rowCount()
        for i in range(rowN):
            state = str(self.ui.tableWidgetProjects.item(i, 1).text())
            if filterState in state or filterState=="All":
                self.ui.tableWidgetProjects.showRow(i)
            else:
                self.ui.tableWidgetProjects.hideRow(i)
        
    def addProjectEntry(self, pathProject, pathPvp, state=""):
        global config

        try:
            pv = PvProject(pathPvp)
        except:
            print("Decode Error:" + pathPvp)
            return

        if state != "" and pv.progress.getState() != state:
            return
            
        rowN = self.ui.tableWidgetProjects.rowCount()
        self.ui.tableWidgetProjects.insertRow(rowN)

        projectName = pathProject
        projectName = projectName.replace(config.projectRoot + os.sep, "")
        
        ownerName = str(pv.owner.firstName) + " " + str(pv.owner.lastName) + " " + str(pv.owner.city)
        
        self.ui.tableWidgetProjects.setItem(rowN, 0, QTableWidgetItem(projectName))
        self.ui.tableWidgetProjects.setItem(rowN, 1, QTableWidgetItem(pv.progress.getState()))
        self.ui.tableWidgetProjects.setItem(rowN, 2, QTableWidgetItem(pv.progress.getToDo()))
        self.ui.tableWidgetProjects.setItem(rowN, 3, QTableWidgetItem(ownerName))
        self.ui.tableWidgetProjects.setItem(rowN, 4, QTableWidgetItem(pv.progress.inquiryReceived))
        self.ui.tableWidgetProjects.setItem(rowN, 5, QTableWidgetItem(pv.progress.quote1Sent))
        self.ui.tableWidgetProjects.setItem(rowN, 6, QTableWidgetItem(pv.progress.orderReceived))
        self.ui.tableWidgetProjects.setItem(rowN, 7, QTableWidgetItem(pv.progress.launch))

    def createProject(self):
        global config
        
        # First validate the input
        street = self.ui.newProject_street.text()
        streetNumber = self.ui.newProject_streetNumber.text()
        zipCode = self.ui.newProject_zipCode.text()
        city = self.ui.newProject_city.text()
        if not street or not streetNumber or not zipCode or not city:
            QtWidgets.QMessageBox.warning(None, 'Fehlerhafte Eingabe', 'Mindestens ein Feld ist leer')
            return

        # TODO: check if city/street valid Path names
        # create city Folder
        address = street + " " + streetNumber
        pvp_dir = config.projectRoot + os.sep + city + os.sep + address
        
        if not os.path.isdir(pvp_dir):
            os.makedirs(pvp_dir)
        
        pvp_path = pvp_dir + os.sep + "plant.pvp"

        if os.path.exists(pvp_path):
            QtWidgets.QMessageBox.warning(None, 'Projekt existiert bereits', 'Projekt\n' + pvp_dir + "\nexistiert bereits")
            return

        # create Project
        pv = PvProject()
        pv.initFromAddress(street, streetNumber, zipCode, city)
        pv.saveAs(pvp_path)
        
        self.projectOpenPath(pvp_path)

        return

    def projectOpen(self, index):
        global config

        project_name = self.ui.tableWidgetProjects.item(index.row(), 0).text()
        pvp_path = config.projectRoot + os.sep + project_name + os.sep + "plant.pvp"
        self.projectOpenPath(pvp_path)


    def projectOpenPath(self, pvp_path):
        cmd = "python3 SolarProject.py \"" + pvp_path + "\" &"
        print (cmd)

        os.system(cmd)

            
    def openConfig(self):
        global config
        
        config.show()
        

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


def excepthook(excType, excValue, tracebackobj):
    """
    Global function to catch unhandled exceptions.
    
    @param excType exception type
    @param excValue exception value
    @param tracebackobj traceback object
    """
    separator = '-' * 80
    timeString = time.strftime("%Y-%m-%d_%H%M%S")
    logFile = "error_" +timeString + ".log"
    notice = \
        """An unhandled exception occurred. Please report the problem\n"""\
        """using the error reporting dialog or via email to <%s>.\n"""\
        """A log has been written to "%s".\n\nError information:\n""" % \
        ("info@eigenstrom.ch", logFile)
    versionInfo="0.0.1"
    
    
    tbinfofile = io.StringIO()
    traceback.print_tb(tracebackobj, None, tbinfofile)
    tbinfofile.seek(0)
    tbinfo = tbinfofile.read()
    errmsg = '%s: \n%s\n' % (str(excType), str(excValue))
    for key, value in excValue.__dict__.items():
        errmsg += str(key) + ":" + str(value) + "\n"
        
    sections = [separator, timeString, separator, errmsg, separator, tbinfo]
    msg = '\n'.join(sections)
    try:
        f = open(logFile, "w")
        f.write(msg)
        f.write(versionInfo)
        f.close()
    except IOError:
        pass
    msg2 = str(notice)+str(msg)+str(versionInfo)
    QtWidgets.QMessageBox.critical(None, 'Eigentool Unhandled Exception', msg2)
    exit(1)

sys.excepthook = excepthook

def main(args):
    global eigentool
    global config

    checkEnv()
        
    config = Config()
    config.load()

    eigentool = Eigentool(args)
    eigentool.exec_()

if __name__ == "__main__":
    main(sys.argv)
    
