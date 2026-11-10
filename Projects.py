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
import time
import io
import signal

from datetime import date

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Ui.Projects import *

from model.PvProject import *
from model.compat import PlantView, ProgressView

from Config import Config
from ErrorHandler import *

# exit application when CTRL-C pressed in command line
signal.signal(signal.SIGINT, signal.SIG_DFL)

if sys.platform == 'darwin':
    def openFolder(path):
        os.system("open \"" + path + "\"")
elif sys.platform == 'win32':
    def openFolder(path):
        os.system("explorer \"" + path + "\"")
else:   # Default Linux
    def openFolder(path):
        os.system("xdg-open \"" + path + "\"")

def is_float(s):
    if s == None:
        return False
    try:
        float(s)
        return True
    except ValueError:
        return False

class Projects(QApplication):
    def __init__(self, *args):
        QApplication.__init__(self, *args)
        self.window = QMainWindow()

        self.ui = Ui_Projects()
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
        
        # resize window if its too large
        screen = QDesktopWidget().availableGeometry(self.window)
        screen_width = screen.width()
        screen_height = screen.height()
        window_width = self.window.width()
        window_height = self.window.height()
        if(window_width > screen_width):
            window_width = screen_width
        if(window_height > screen_height - 25):
            window_height = screen_height - 25
        self.window.resize(window_width, window_height)

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
        pvp_path, order_id = self.rowProject(row)
        pvp_folder = os.path.dirname(pvp_path)
        try:
            pv = PvProject(pvp_path)
            order = pv.byId("orders", order_id)
            if order is not None and os.path.isdir(pv.getOrderDir(order)):
                pvp_folder = pv.getOrderDir(order)
        except Exception:
            pass
        openFolder(pvp_folder)

    # path of the project file and id of the order of a table row
    def rowProject(self, row):
        item = self.ui.tableWidgetProjects.item(row, 0)
        return item.data(Qt.UserRole), item.data(Qt.UserRole + 1)

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
                                
                    # quotes over 1999 are for temporary workers
                    if quoteNumber > 1999:
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

        # the rows are new, filter them again
        if self.ui.filterFreeText.text():
            self.filterFreeTextChanged()
        else:
            self.filterStatusChanged()

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
        self.projectPaths = []
        if not os.path.exists(config.projectRoot):
            print("path not found: " + config.projectRoot)
            return

        for dirname, dirnames, filenames in os.walk(config.projectRoot):
            for filename in filenames:
                if filename == "plant.pvp":
                    self.projectPaths.append(os.path.join(dirname, filename))

            # Advanced usage:
            # editing the 'dirnames' list will stop os.walk() from recursing into there.
            if '.git' in dirnames:
                # don't go into any .git directories.
                dirnames.remove('.git')
        
        self.updateProjectEntries("Default")
        
        self.ui.tableWidgetProjects.resizeColumnsToContents()

    # Add a row for an order of a project. orderId is None if the project
    # could not be read.
    def addProjectEntry(self, pathPvp, name, orderId):
        rowN = self.ui.tableWidgetProjects.rowCount()
        self.ui.tableWidgetProjects.insertRow(rowN)

        item = QTableWidgetItem(name)
        item.setData(Qt.UserRole, pathPvp)
        item.setData(Qt.UserRole + 1, orderId)
        self.ui.tableWidgetProjects.setItem(rowN, 0, item)
        return rowN

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
                "Bauherr",
                "Inbetriebnahme",
                "Schlussrechnung",
                "Schlussrechnung bez",
                "Preis",
                "DC-Leistung",
                "CHF/kWp",
                "CHF/m2"
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
        # disable sorting while reloading, otherwise it will reorder the table
        # according to the sorted column
        self.ui.tableWidgetProjects.setSortingEnabled(False)

        # Set columns header
        self.ui.tableWidgetProjects.setRowCount(0)
        self.ui.tableWidgetProjects.setColumnCount(len(views[view]))
        self.ui.tableWidgetProjects.setHorizontalHeaderLabels(views[view])

        # one row for every order of every project
        for pathPvp in self.projectPaths:
            projectName = os.path.dirname(pathPvp).replace(config.projectRoot + os.sep, "")
            try:
                pv = PvProject(pathPvp)
                orders = list(pv.orders) or [pv.currentOrder]
            except:
                rowN = self.addProjectEntry(pathPvp, projectName, None)
                self.ui.tableWidgetProjects.setItem(rowN, 1, QTableWidgetItem("Decode Error"))
                for i in range(2, len(views[view])):
                    self.ui.tableWidgetProjects.setItem(rowN, i, QTableWidgetItem(""))
                continue

            for order in orders:
                name = projectName
                # the first order is the project itself, later ones get their title
                if order is not orders[0]:
                    name += " \u203a " + order.getCaption()
                rowN = self.addProjectEntry(pathPvp, name, order.id)
                self.updateProjectEntry(pv, order, rowN, view)
        
        self.ui.tableWidgetProjects.setSortingEnabled(True)


    def updateProjectEntry(self, pv, order, rowN, view="Default"):
        progress = ProgressView(pv, order)
        plant = PlantView(pv, order)

        cs = progress.constructionStart
        if progress.constructionFixed:
            cs = str(cs) + " fix" if cs else "fix"
           
        ownerName = pv.contacts.owner.getNameCity()
        kWp = 0
        if is_float(plant.totalCost) and is_float(plant.totalPowerDc):
            kWp = int(float(plant.totalCost)/float(plant.totalPowerDc))
        m2 = 0
        if is_float(plant.totalCost) and is_float(plant.totalArea):
            m2 = int(float(plant.totalCost)/float(plant.totalArea))

        views = {
            "Default" : {
                1 : progress.getState(),
                2 : progress.inquiryReceived,
                3 : progress.quote1Sent,
                4 : progress.orderReceived,
                5 : cs,
                6 : progress.launch,
                7 : ownerName
            },
            "Finance" : {
                1 : ownerName,
                2 : progress.launch,
                3 : progress.finalInvoiceSent,
                4 : progress.finalInvoiceReceived,
                5 : plant.totalCost,
                6 : plant.totalPowerDc,
                7 : kWp,
                8 : m2,
            },
            "Construction" : {
                1 : progress.getState(),
                2 : cs,
                3 : plant.totalPanelCount,
                4 : plant.totalPowerAc,
                5 : progress.launch,
                6 : progress.finalInvoiceSent,
                7 : progress.finalInvoiceReceived,
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
        self.projectPaths.append(pvp_path)
        
        self.projectOpenPath(pvp_path)

        # delete input fields
        self.ui.newProject_street.setText("")
        self.ui.newProject_streetNumber.setText("")
        self.ui.newProject_zipCode.setText("")
        self.ui.newProject_city.setText("")

        return

    def exportContacts(self):
        global config
        
        vCard = ""
        microsip_xml = "<?xml version=\"1.0\"?>\n<contacts>\n"
        projects_csv = "Plant,launch,totalPowerDc,totalArea,totalPanelCount,panelDesc,totalPowerAc,inverterDesc,totalCost\n"
        # loop over all Projects
        if not os.path.exists(config.projectRoot):
            print("path not found: " + config.projectRoot)
            return

        for dirname, dirnames, filenames in os.walk(config.projectRoot):
            for filename in filenames:
                if filename == "plant.pvp":
                    fn = os.path.join(dirname, filename)
                    try:
                        pv = PvProject(fn)
                    except Exception:
                        print("Decode Error: " + fn)
                        continue
                    name = pv.contacts.owner.getNameCity()
                    if name == "":
                        continue

                    phone = pv.contacts.owner.getPhoneClean()
                    phone2 = pv.contacts.owner.getPhone2Clean()
                    mobile = pv.contacts.owner.getMobileClean()
                    if phone:
                        microsip_xml += "<contact name=\""+name+"\" number=\""+phone+"\" firstname=\"\" lastname=\"\" phone=\"\" mobile=\"\" email=\"\" address=\"\" city=\"\" state=\"\" zip=\"\" comment=\"\" id=\"\" info=\"\" presence=\"0\" starred=\"0\" directory=\"0\"/>\n"
                    if phone2:
                        microsip_xml += "<contact name=\""+name+"\" number=\""+phone2+"\" firstname=\"\" lastname=\"\" phone=\"\" mobile=\"\" email=\"\" address=\"\" city=\"\" state=\"\" zip=\"\" comment=\"\" id=\"\" info=\"\" presence=\"0\" starred=\"0\" directory=\"0\"/>\n"
                    if mobile:
                        microsip_xml += "<contact name=\""+name+"\" number=\""+mobile+"\" firstname=\"\" lastname=\"\" phone=\"\" mobile=\"\" email=\"\" address=\"\" city=\"\" state=\"\" zip=\"\" comment=\"\" id=\"\" info=\"\" presence=\"0\" starred=\"0\" directory=\"0\"/>\n"
                                                                        
                    vCard += pv.contacts.owner.exportVCard()

                    # one line for every order
                    for order in pv.orders:
                        progress = ProgressView(pv, order)
                        plant = PlantView(pv, order)
                        projects_csv += name + ","
                        projects_csv += str(progress.launch) + ","
                        projects_csv += str(plant.totalPowerDc) + ","
                        projects_csv += str(plant.totalArea) + ","
                        projects_csv += str(plant.totalPanelCount) + ","
                        projects_csv += str(plant.panelDesc) + ","
                        projects_csv += str(plant.totalPowerAc) + ","
                        projects_csv += str(plant.inverterDesc) + ","
                        projects_csv += str(plant.totalCost) + "\n"
                    
        microsip_xml += "</contacts>"

        with open(config.projectRoot + os.sep + "Contacts_MicroSIP.xml", "w") as text_file:
            text_file.write(microsip_xml)

        with open(config.projectRoot + os.sep + "Contacts.vcf", "w") as text_file:
            text_file.write(vCard)

        with open(config.projectRoot + os.sep + "projects.csv", "w") as text_file:
            text_file.write(projects_csv)

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
            pathPvp, orderId = self.rowProject(i)
            try:
                pv = PvProject(pathPvp)
            except:
                print("Decode Error: " + pathPvp)
                continue
            order = pv.byId("orders", orderId)
            if order is None:
                continue
            progress = ProgressView(pv, order)
            if not progress.getState().startswith("5 -"):
                continue
            constructionSort = progress.getConstructionSort()
            
            projects.append({"sort":constructionSort, "path":pathPvp, "order":orderId})

        # sort the projects
        srt = sorted(projects, key=lambda x:x['sort'])

        # now loop over all sorted projects
        # starting with now, all week one system
        today = datetime.date.today()
        coming_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
        days = 0
        for item in srt:
            start = coming_monday + datetime.timedelta(days=days)
            # read the project again: two orders of one project must not
            # overwrite each other
            pv = PvProject(item['path'])
            progress = ProgressView(pv, pv.byId("orders", item['order']))
            if not progress.constructionFixed:
                progress.constructionStart = str(start)
                pv.save()
#            print("sort:" + item['sort'] + " start:" + str(start))
            days += 7
        
        # update the view
        self.projectViewChanged()
            

    def projectOpen(self, index):
        pvp_path, order_id = self.rowProject(index.row())
        self.projectOpenPath(pvp_path, order_id)


    def projectOpenPath(self, pvp_path, order_id=None):
        cmd = "python3 GnuSolar.py \"" + pvp_path + "\""
        if order_id:
            cmd += " \"" + order_id + "\""
        cmd += " &"
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

def main(args):
    global projects
    global config

    checkEnv()
        
    config.load()

    projects = Projects(args)
    projects.exec_()

if __name__ == "__main__":
    main(sys.argv)
    
