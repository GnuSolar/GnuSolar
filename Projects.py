#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
import os

sitepack = os.path.join(os.path.dirname(__file__), "site-packages")
sys.path.insert(0, sitepack)

import json 
import codecs
import io
import traceback
import datetime

from datetime import date

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Ui.MainWindow import *

from model.PvProject import *

from Config import Config

if sys.platform == 'darwin':
    def openFolder(path):
        os.system("open \"" + path + "\"")
elif sys.platform == 'win32':
    def openFolder(path):
        os.system("explorer \"" + path + "\"")
else:   # Default Linux
    def openFolder(path):
        os.system("xdg-open \"" + path + "\"")

class Projects(QApplication):
    def __init__(self, *args):
        QApplication.__init__(self, *args)
        self.window = QMainWindow()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.window)
        
        self.fillTableProjects()
        self.fillLastNames()

        self.ui.action_Preferences.triggered.connect(self.openConfig)
        self.ui.createProject.clicked.connect(self.createProject)
        self.ui.exportContacts.clicked.connect(self.exportContacts)
        self.ui.reload.clicked.connect(self.projectViewChanged)         # TODO: reload from filesystem
        self.ui.constructionSort.clicked.connect(self.constructionSort)         # TODO: reload from filesystem
        self.ui.tableWidgetProjects.doubleClicked.connect(self.projectOpen)

        self.ui.filterStatus.currentTextChanged.connect(self.filterStatusChanged)
        self.ui.projectView.currentTextChanged.connect(self.projectViewChanged)
        self.ui.filterFreeText.textChanged.connect(self.filterFreeTextChanged)

        # Menu
        self.ui.tableWidgetProjects.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tableWidgetProjects.customContextMenuRequested.connect(self.rightMenu)

        title = "Pv Projects - " + Config.getAppVersion()
        self.window.setWindowTitle(title)
        
        self.window.show()

    def rightMenu(self, pos):
        if self.ui.tableWidgetProjects.selectionModel().selection().indexes():
            for i in self.ui.tableWidgetProjects.selectionModel().selection().indexes():
                row, column = i.row(), i.column()

            menu = QMenu()

            # Add menu options
            open_folder_option = menu.addAction('Open Folder')

            # Menu option events
            action = menu.exec_(self.ui.tableWidgetProjects.mapToGlobal(pos))
            if action == open_folder_option:
                self.openFolderMenu(row)

    def openFolderMenu(self, row):
        global config

        project_name = self.ui.tableWidgetProjects.item(row, 0).text()
        pvp_folder = config.projectRoot + os.sep + project_name
        openFolder(pvp_folder)

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
    
    def filterStatusChanged(self):
        # Reset free text changed
        self.ui.filterFreeText.textChanged.disconnect()
        self.ui.filterFreeText.setText("")
        self.ui.filterFreeText.textChanged.connect(self.filterFreeTextChanged)

        filterState = self.ui.filterStatus.currentText()
        rowN = self.ui.tableWidgetProjects.rowCount()
        for i in range(rowN):
            state = str(self.ui.tableWidgetProjects.item(i, 1).text())
            if filterState in state or filterState=="All":
                self.ui.tableWidgetProjects.showRow(i)
            else:
                self.ui.tableWidgetProjects.hideRow(i)

    def projectViewChanged(self):
        projectView = self.ui.projectView.currentText()
        self.updateProjectEntries(projectView)

    def filterFreeTextChanged(self):
        # Reset Filter Status
        self.ui.filterStatus.setCurrentIndex(0)
        
        searchText = self.ui.filterFreeText.text()
        rowN = self.ui.tableWidgetProjects.rowCount()
        colN = self.ui.tableWidgetProjects.columnCount()
        searchText = searchText.lower()
        for i in range(rowN):
            # Build a string representation of the line
            lineText = ""
            for j in range(colN):
                lineText = lineText + "/" + str(self.ui.tableWidgetProjects.item(i, j).text())
            lineText = lineText.lower()

            # Now search in it
            if searchText in lineText:
                self.ui.tableWidgetProjects.showRow(i)
            else:
                self.ui.tableWidgetProjects.hideRow(i)

    def fillTableProjects(self):
        global config
        
        # recursive scan all folders
        if not os.path.exists(config.projectRoot):
            print("path not found: " + config.projectRoot)
            return

        for dirname, dirnames, filenames in os.walk(config.projectRoot):
            for filename in filenames:
                if filename == "plant.pvp":
                    fn = os.path.join(dirname, filename)
                    self.addProjectEntry(dirname, fn)

            # Advanced usage:
            # editing the 'dirnames' list will stop os.walk() from recursing into there.
            if '.git' in dirnames:
                # don't go into any .git directories.
                dirnames.remove('.git')
        
        self.updateProjectEntries("Default")
        
        self.ui.tableWidgetProjects.resizeColumnsToContents()

    def addProjectEntry(self, pathProject, pathPvp):
        global config

        rowN = self.ui.tableWidgetProjects.rowCount()
        self.ui.tableWidgetProjects.insertRow(rowN)

        projectName = pathProject
        projectName = projectName.replace(config.projectRoot + os.sep, "")
        
        self.ui.tableWidgetProjects.setItem(rowN, 0, QTableWidgetItem(projectName))

    def updateProjectEntries(self, view="Default"):
        global config
        views = {
            "Default" : [
                "Projekt",
                "Status",
                "Anfrage",
                "offeriert",
                "Zusage",
                "Baustart",
                "Inbetriebnahme",
                "Bauherr"
            ],
            "Finance" : [
                "Projekt",
                "Status",
                "Baustart",
                "Akonto",
                "Akonto bez",
                "Inbetriebnahme",
                "Schlussrechnung",
                "Schlussrechnung bez",
                "Bauherr"
            ],
            "Construction" : [
                "Projekt",
                "Status",
                "Baustart",
                "Anz Module",
                "AC-Leistung",
                "Inbetriebnahme",
                "Schlussrechnung",
                "Schlussrechnung bez",
                "Bauherr"
            ]
            
        }
        # Set columns header
        self.ui.tableWidgetProjects.setColumnCount(len(views[view]))
        self.ui.tableWidgetProjects.setHorizontalHeaderLabels(views[view])

        # disable sorting while reloading, otherwise it will reorder the table
        # according to the sorted column
        self.ui.tableWidgetProjects.setSortingEnabled(False)

        rowN = self.ui.tableWidgetProjects.rowCount()
        for i in range(rowN):
            projectName = self.ui.tableWidgetProjects.item(i, 0).text()
            pathPvp = config.projectRoot + os.sep + projectName + os.sep + "plant.pvp"
            self.updateProjectEntry(pathPvp, i, view)
        
        self.ui.tableWidgetProjects.setSortingEnabled(True)


    def updateProjectEntry(self, pathPvp, rowN, view="Default"):
        try:
            pv = PvProject(pathPvp)
        except:
            self.ui.tableWidgetProjects.setItem(rowN, 1, QTableWidgetItem("Decode Error"))
            return
        
        cs = pv.progress.constructionStart
        if pv.progress.constructionFixed:
            cs += " fix"
           
        ownerName = pv.contacts.owner.getNameCity()
        views = {
            "Default" : {
                1 : pv.progress.getState(),
                2 : pv.progress.inquiryReceived,
                3 : pv.progress.quote1Sent,
                4 : pv.progress.orderReceived,
                5 : cs,
                6 : pv.progress.launch,
                7 : ownerName
            },
            "Finance" : {
                1 : pv.progress.getState(),
                2 : pv.progress.constructionStart,
                3 : pv.progress.partialInvoiceSent,
                4 : pv.progress.partialInvoiceReceived,
                5 : pv.progress.launch,
                6 : pv.progress.finalInvoiceSent,
                7 : pv.progress.finalInvoiceReceived,
                8 : ownerName
            },
            "Construction" : {
                1 : pv.progress.getState(),
                2 : cs,
                3 : pv.plant.totalPanelCount,
                4 : pv.plant.totalPowerAc,
                5 : pv.progress.launch,
                6 : pv.progress.finalInvoiceSent,
                7 : pv.progress.finalInvoiceReceived,
                8 : ownerName
            }
        
        }
        for i, val in views[view].items():
            val = str(val)      # dont crash if no string
            if val=="None":
                val = ""
            self.ui.tableWidgetProjects.setItem(rowN, i, QTableWidgetItem(val))
        
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

        # delete input fields
        self.ui.newProject_street.setText("")
        self.ui.newProject_streetNumber.setText("")
        self.ui.newProject_zipCode.setText("")
        self.ui.newProject_city.setText("")

        return

    def exportContacts(self):
        global config
        
        microsip_xml = "<?xml version=\"1.0\"?>\n<contacts>\n"
        # loop over all Projects
        if not os.path.exists(config.projectRoot):
            print("path not found: " + config.projectRoot)
            return

        for dirname, dirnames, filenames in os.walk(config.projectRoot):
            for filename in filenames:
                if filename == "plant.pvp":
                    fn = os.path.join(dirname, filename)
                    pv = PvProject(fn)
                    name = pv.contacts.owner.getNameCity()
                    if name == "":
                        continue

                    phone = pv.contacts.owner.getPhoneClean()
                    mobile = pv.contacts.owner.getMobileClean()

                    number = phone
                    if not number:
                        number = mobile
                                                                        
                    microsip_xml += "<contact name=\""+name+"\" number=\""+number+"\" firstname=\"\" lastname=\"\" phone=\""+phone+"\" mobile=\""+mobile+"\" email=\"\" address=\"\" city=\"\" state=\"\" zip=\"\" comment=\"\" id=\"\" info=\"\" presence=\"0\" starred=\"0\" directory=\"0\"/>\n"

        microsip_xml += "</contacts>"
        with open(config.projectRoot + os.sep + "MicroSIP_Contacts.xml", "w") as text_file:
            text_file.write(microsip_xml)

        return

    def constructionSort(self):
        global config
        
        qm = QMessageBox
        ret = qm.question(None, '', "Wirklich Bautermine neu vergeben?", qm.Yes | qm.No)

        if ret == qm.No:
            return

        print("constructionSort")
        # loop over all projects with state == building
        
        
        projects = []
        
        rowN = self.ui.tableWidgetProjects.rowCount()
        for i in range(rowN):
            projectName = self.ui.tableWidgetProjects.item(i, 0).text()
            pathPvp = config.projectRoot + os.sep + projectName + os.sep + "plant.pvp"
            try:
                pv = PvProject(pathPvp)
            except:
                print("Decode Error: " + pathPvp)
                continue
            if not pv.progress.getState().startswith("5 -"):
                continue
            constructionSort = pv.progress.getConstructionSort()
            
            projects.append({"sort":constructionSort, "pv":pv})

        # sort the projects
        srt = sorted(projects, key=lambda x:x['sort'])

        # now loop over all sorted projects
        # starting with now, all week one system
        today = datetime.date.today()
        coming_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
        days = 0
        for item in srt:
            start = coming_monday + datetime.timedelta(days=days)
            pv = item['pv']
            if not pv.progress.constructionFixed:
                pv.progress.constructionStart = str(start)
                pv.save()
#            print("sort:" + item['sort'] + " start:" + str(start))
            days += 7
        
        # update the view
        self.updateProjectEntries()
            

    def projectOpen(self, index):
        global config

        project_name = self.ui.tableWidgetProjects.item(index.row(), 0).text()
        pvp_path = config.projectRoot + os.sep + project_name + os.sep + "plant.pvp"
        self.projectOpenPath(pvp_path)


    def projectOpenPath(self, pvp_path):
        cmd = "python3 GnuSolar.py \"" + pvp_path + "\" &"
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
            raise RuntimeError('Pv Projects will abort further execution '
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
        ("bugs@gnusolar.org", logFile)
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
    QtWidgets.QMessageBox.critical(None, 'Projects Unhandled Exception', msg2)
    exit(1)

sys.excepthook = excepthook

def main(args):
    global projects
    global config

    checkEnv()
        
    config = Config()
    config.load()

    projects = Projects(args)
    projects.exec_()

if __name__ == "__main__":
    main(sys.argv)
    
