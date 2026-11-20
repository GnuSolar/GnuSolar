#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The detail pages of the project window, one per model class.
#
# A page connects the buttons of its generated form (Ui/*.py) and handles
# them: it asks for what is missing, shows messages, opens folders, and calls
# the model, documents and services for the actual work. The model itself
# knows nothing about the window.
#
#   page = createPage(ui, obj, app)
#
# ui is the generated form, obj the model object shown (Building, Contact, ...),
# app the GnuSolar application (None in the address book).

import os
import sys
import json
import subprocess
import tempfile
import urllib.request
from datetime import date

import requests
from PyQt5 import QtCore, QtWidgets

import documents.templates
from documents import DocumentError
from gui.binding import updateUi, setChoices, comboValue
from Config import Config, config
from gui.contactPicker import pickContact
from model.ContactStore import ContactStore, copyFields, label as contactLabel
from Usefull import openFolder, openFolderIfExists, composeEmail, callSip

from model.PvProject import PvProject, PROJECT_TYPES, nextExtensionDir
from model.Contacts import Contacts
from model.Contact import Contact, FORMALITIES
from model.Building import Building
from model.Municipality import Municipality
from model.PowerCompany import PowerCompany
from model.Progress import Progress
from model.Plant import Plant


class Page:
    def __init__(self, ui, obj, app):
        self.ui = ui
        self.obj = obj
        self.app = app
        self.project = obj if isinstance(obj, PvProject) else getattr(obj, "_top", None)
        self.connect()

    # connect the buttons of the form
    def connect(self):
        pass

    # Create a document from a template, show problems, open the new file
    def createDocument(self, templateType):
        try:
            path = documents.templates.createFromTemplate(templateType, self.project._savePath, self.project, config)
        except DocumentError as e:
            QtWidgets.QMessageBox.warning(None, e.title, str(e))
            return None
        openFolderIfExists(path)
        return path


class PvProjectPage(Page):
    def connect(self):
        ui = self.ui
        ui.openProjectFolder.clicked.connect(self.action_openProjectFolder)
        ui.createQuote.clicked.connect(self.action_createQuote)
        ui.createPartialInvoice.clicked.connect(self.action_createPartialInvoice)
        ui.createFinalInvoice.clicked.connect(self.action_createFinalInvoice)
        ui.createSmallInvoice.clicked.connect(self.action_createSmallInvoice)
        ui.createQrBill.clicked.connect(self.action_createQrBill)
        ui.createDocumentation.clicked.connect(self.action_createDocumentation)
        ui.chooseBase.clicked.connect(self.action_chooseBase)
        ui.openBase.clicked.connect(self.action_openBase)
        ui.clearBase.clicked.connect(self.action_clearBase)
        ui.createExtension.clicked.connect(self.action_createExtension)
        setChoices(ui.obj_type, PROJECT_TYPES)
        # the templates depend on the type, also on one just chosen
        ui.obj_type.currentIndexChanged.connect(lambda index: self.showTemplates(comboValue(ui.obj_type)))
        self.showTemplates(self.obj.type)

    # the template each button makes its document from, with its full path in
    # the tooltip of the line and of the button
    TEMPLATE_BUTTONS = {
        "quote": "createQuote",
        "partial_invoice": "createPartialInvoice",
        "final_invoice": "createFinalInvoice",
        "small_invoice": "createSmallInvoice",
        "documentation": "createDocumentation",
    }

    def showTemplates(self, projectType):
        for templateType, button in self.TEMPLATE_BUTTONS.items():
            path = documents.templates.templateFor(templateType, projectType, config)
            label = getattr(self.ui, "template_" + templateType)
            if path:
                text = os.path.basename(path) + "  (" + documents.templates.templateSource(path) + ")"
                tip = "Vorlage: " + path
            else:
                text = tip = "keine Vorlage gefunden"
            label.setText(text)
            label.setToolTip(tip)
            getattr(self.ui, button).setToolTip(tip)

    # Choose the project this one extends by its file. Setting the field
    # updates the model, like typing into any other field.
    def action_chooseBase(self):
        projectDir = self.obj.getProjectDir()
        if not projectDir:
            QtWidgets.QMessageBox.warning(None, 'Basisprojekt', 'Das Projekt ist noch nicht gespeichert')
            return
        options = QtWidgets.QFileDialog.Options() | QtWidgets.QFileDialog.DontUseNativeDialog
        path, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Basisprojekt wählen",
            os.path.dirname(projectDir), "GnuSolar Projekt (plant.pvp)", options=options)
        if not path:
            return
        baseDir = os.path.dirname(os.path.abspath(path))
        if os.path.normcase(baseDir) == os.path.normcase(os.path.abspath(projectDir)):
            QtWidgets.QMessageBox.warning(None, 'Basisprojekt', 'Ein Projekt kann nicht sich selbst erweitern')
            return
        self.ui.obj_base.setText(self.obj.baseFromFolder(baseDir))

    # open the project this one extends in a window of its own
    def action_openBase(self):
        path = self.obj.getBasePath()
        if not path:
            return
        if not os.path.isfile(path):
            QtWidgets.QMessageBox.warning(None, 'Basisprojekt', 'Projekt nicht gefunden\n' + path)
            return
        self.openProjectWindow(path)

    # Create a project for the next job at this place, which extends this one
    # and takes over its building, contacts, municipality and power company,
    # and open it in a window of its own
    def action_createExtension(self):
        if not self.obj.getProjectDir():
            QtWidgets.QMessageBox.warning(None, 'Erweiterung', 'Das Projekt ist noch nicht gespeichert')
            return
        folder = nextExtensionDir(self.obj.getRootDir())
        names = [name for code, name in PROJECT_TYPES]
        name, ok = QtWidgets.QInputDialog.getItem(None, "Erweiterung erstellen",
            "Neues Projekt in\n" + folder + "\nmit Gebäude, Kontakten, Gemeinde und Stromversorger "
            "dieses Projekts.\n\nTyp:", names, names.index("Batterie"), False)
        if not ok:
            return
        code = {name: code for code, name in PROJECT_TYPES}[name]
        try:
            ext = self.obj.createExtension(code)
        except OSError as e:
            QtWidgets.QMessageBox.warning(None, 'Erweiterung', 'Projekt nicht erstellt\n' + str(e))
            return
        self.openProjectWindow(ext._savePath)

    # open a project file in a window of its own, a bit right of and above
    # this window, so both can be seen
    def openProjectWindow(self, path):
        program = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "GnuSolar.py")
        args = [sys.executable, program, path]
        if self.app is not None:
            pos = self.app.window.frameGeometry().topLeft() + QtCore.QPoint(60, -60)
            args.append("--pos=%d,%d" % (pos.x(), pos.y()))
        subprocess.Popen(args)

    def action_clearBase(self):
        self.ui.obj_base.setText("")

    def action_openProjectFolder(self):
        if not self.obj._savePath:
            return
        folder = os.path.dirname(self.obj._savePath)
        openFolderIfExists(folder)

    def action_createQuote(self):
        self.createDocument("quote")

    # Create Partial Invoice
    def action_createPartialInvoice(self):
        self.createDocument("partial_invoice")

    # Create Final Invoice
    def action_createFinalInvoice(self):
        self.createDocument("final_invoice")

    # Create Small Invoice
    def action_createSmallInvoice(self):
        self.createDocument("small_invoice")

    # Create Documentation
    def action_createDocumentation(self):
        self.createDocument("documentation")

    # Create swiss QR Bill
    def action_createQrBill(self):
        # only needed here, bundled in site-packages (added by documents)
        from qrbill import QRBill
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPDF

        global config
        if not self.obj._savePath:
            QtWidgets.QMessageBox.warning(None, 'QR Bill', 'TODO: ohne Pfad')
            return

        qrAmount = self.ui.qrbill_amount.text()
        qrInfo = self.ui.qrbill_info.text()
        
        projectDir = os.path.dirname(self.obj._savePath)
        if not os.path.isdir(projectDir):
            QtWidgets.QMessageBox.warning(None, 'QR Bill', 'Pfad nicht gefunden\n' + self.obj._savePath)
            return

        today = date.today()
        fileName = "QR" + today.isoformat() + ".pdf"
        outDir = config.getFolderPath(projectDir, "invoices")
        qrPath = outDir + os.sep + fileName
        if not os.path.isdir(outDir):
            os.makedirs(outDir)

        debtor = self.obj.contacts.owner
        my_bill = QRBill(
                account=config.installer_bankIban,
                language='de',
                creditor={
                    'name': config.installer_company, 
                    'street': config.installer_street,
                    'house_num': config.installer_streetNumber,
                    'pcode': config.installer_zip,
                    'city': config.installer_city, 
                },
                debtor={
                    'name': debtor.getNameAddress(), 
                    'street': debtor.street,
                    'house_num': debtor.streetNumber,
                    'pcode': debtor.zip,
                    'city': debtor.city, 
                },
                amount=qrAmount,
                additional_information=(
                    qrInfo
                )                
            )
        with tempfile.TemporaryFile(encoding='utf-8', mode='r+') as temp:
            my_bill.as_svg(temp, full_page=True)
            temp.seek(0)
            drawing = svg2rlg(temp)
        renderPDF.drawToFile(drawing, qrPath)

        self.ui.qrbill_amount.setText("")
        self.ui.qrbill_info.setText("")

        openFolderIfExists(qrPath)

class ContactsPage(Page):
    pass


class ContactPage(Page):
    def connect(self):
        ui = self.ui
        ui.composeEmail.clicked.connect(self.action_composeEmail)
        ui.composeEmail2.clicked.connect(self.action_composeEmail2)
        ui.callPhone.clicked.connect(self.action_callPhone)
        ui.callPhone2.clicked.connect(self.action_callPhone2)
        ui.callMobile.clicked.connect(self.action_callMobile)
        setChoices(ui.obj_formality, FORMALITIES)
        # exchanging with the address book makes sense only in a project
        if self.app is None:
            ui.toAddressBook.hide()
            ui.fromAddressBook.hide()
        else:
            ui.toAddressBook.clicked.connect(self.action_toAddressBook)
            ui.fromAddressBook.clicked.connect(self.action_fromAddressBook)

    # save this contact in the address book; a contact with the same company
    # and name is updated or kept, as the user chooses
    def action_toAddressBook(self):
        if not any(getattr(self.obj, f, None) for f in ("company", "lastName", "firstName")):
            QtWidgets.QMessageBox.information(self.app.window, "Ins Adressbuch",
                                              "Der Kontakt hat weder Firma noch Namen.")
            return
        name = contactLabel(self.obj)
        store = ContactStore(Config.getUserDbPath())
        try:
            entry = Contact()
            entry._id = store.find(self.obj)
            if entry._id is not None:
                box = QtWidgets.QMessageBox(self.app.window)
                box.setWindowTitle("Ins Adressbuch")
                box.setText("«" + name + "» ist schon im Adressbuch.")
                update = box.addButton("Aktualisieren", QtWidgets.QMessageBox.AcceptRole)
                add = box.addButton("Neu hinzufügen", QtWidgets.QMessageBox.ActionRole)
                box.addButton(QtWidgets.QMessageBox.Cancel)
                box.exec_()
                if box.clickedButton() == add:
                    entry._id = None
                elif box.clickedButton() != update:
                    return
            copyFields(self.obj, entry)
            store.save(entry)
        finally:
            store.close()
        self.app.window.statusBar().showMessage("«" + name + "» im Adressbuch gespeichert", 5000)

    # replace this contact with one chosen from the address book; the role stays
    def action_fromAddressBook(self):
        store = ContactStore(Config.getUserDbPath())
        try:
            contactId = pickContact(self.app.window, store)
            chosen = store.load(contactId) if contactId is not None else None
        finally:
            store.close()
        if chosen is None:
            return
        copyFields(chosen, self.obj)
        updateUi(self.ui, self.obj, "obj")
        self.app.action_changed()

    def action_callPhone(self):
        global config
        callSip(self.obj.phone, config.sipServer)

    def action_callPhone2(self):
        global config
        callSip(self.obj.phone2, config.sipServer)

    def action_callMobile(self):
        global config
        callSip(self.obj.mobile, config.sipServer)

    def action_composeEmail(self):
        composeEmail(config.installer_email, self.obj.email , "", "")

    def action_composeEmail2(self):
        composeEmail(config.installer_email, self.obj.email2 , "", "")

class BuildingPage(Page):
    def connect(self):
        ui = self.ui
        ui.updateFromAddress.clicked.connect(self.action_updateFromAddress)
        ui.get3dModel.clicked.connect(self.action_get3dModel)
        ui.getAgisOrtho.clicked.connect(self.action_getAgisOrtho)
        ui.getAgisSurvey.clicked.connect(self.action_getAgisSurvey)

    def action_updateFromAddress(self):
        ret = self.project.updateFromAddress()

        updateUi(self.ui, self.obj, "obj")
        if isinstance(ret, str):
            QtWidgets.QMessageBox.warning(None, 'Update von Adresse', ret)

    def action_get3dModel(self):
        x = self.obj.swissGridX
        y = self.obj.swissGridY
        if not x or not y:
            QtWidgets.QMessageBox.warning(None, 'Get 3D Model Error', 'no coordiantes')
            return

        url = "http://amsler-solar.ch/swissbuildings3d-3-0/api.php?x=2" + str(x) + "&y=1" + str(y) + "&format=stl"
        response = requests.get(url=url)
        resp_txt = response.text
        if not resp_txt.startswith("solid"):
            QtWidgets.QMessageBox.warning(None, 'Get 3D Model Error', resp_txt)
            return
        
        projectDir = self.project.getProjectDir()
        if not projectDir:
            QtWidgets.QMessageBox.warning(None, 'Get 3D Model Error', 'Projekt zuerst speichern')
            return
        cad_folder = config.getFolderPath(projectDir, "plans")
        if not os.path.isdir(cad_folder):
            os.makedirs(cad_folder)
        
        stl_file = cad_folder + os.sep + "house_geo.stl"
        if os.path.isfile(stl_file):
            QtWidgets.QMessageBox.warning(None, 'Get 3D Model Error', "File exists: " + stl_file)
            return
        
        with open(stl_file, "w") as f:
            f.write(resp_txt)

        openFolderIfExists(stl_file)

    def action_getAgisOrtho(self):
        x = self.obj.swissGridX
        y = self.obj.swissGridY
        if not x or not y:
            QtWidgets.QMessageBox.warning(None, 'Get Agis Ortho', 'no coordiantes')
            return

        x = int(float(x))
        y = int(float(y))

        url = "https://www.ag.ch/geoportal/api/v1/print/"
        json = {
          # 1:500 x width=113, y height=97
          "MapExtent":{
            "Xmax":int(x+2000000 + 56),
            "Xmin":int(x+2000000 - 57),
            "Ymax":int(y+1000000 + 48),
            "Ymin":int(y+1000000 - 49)
          },
          "MapServices":[
            {
              "Url":"https://www.ag.ch/geoportal/rest/services/base_ortho2023/MapServer",
              "Opacity":1,
              "Id":"base_ortho2023",
              "Name":"base_ortho2023",
              "LayerType":1,
              "LayersInLegend":[0],
              "Visible":True,
              "VisibleLayers":[],
              "Version":""
            },
            {
              "Url":"https://www.ag.ch/geoportal/rest/services/va_avdaten/MapServer",
              "Opacity":1,
              "Id":"Amtliche Vermessung",
              "Name":"Amtliche Vermessung",
              "LayerType":0,
              "LayersInLegend":[],
              "Visible":True,
              "VisibleLayers":[0,1,6,7,9,10,11,13,14,15,16],
              "Version":""
            }
          ],
          "CopyrightText":"Die gedruckten Daten haben nur informativen Charakter. Es k\u00f6nnen keine rechtlichen Anspr\u00fcche irgendwelcher Art geltend gemacht werden.\nBitte beachten Sie auch die Ausf\u00fchrungen zum Kartendienst 'va_avdaten' unter https://www.ag.ch/geoportal/api/v1/mapservices/176/documentation.\nQuelle: Daten des Kantons Aargau, Bundesamt f\u00fcr Landestopografie",
          "Width":224.6,
          "Height":194.268,
          "LayoutId":"AgisDefault",
          "Layoutformat":"a4",
          "Layoutsubtitle":self.obj.getHumanAddress(),
          "Layouttitle":"Luftbild",
          "LegendVisible":True,
          "LogoFileName":"logo.wmf",
          "MapOnly":False,
          "MapOnlyImageType":"png",
          "OverviewVisible":False,
          "Scale":500,
          "ScalebarVisible":True,
          "CustomLegendName":"",
          "LayoutOrientation":"quer",
          "Angle":0,
          "Graphics":[]
        }
        response = requests.post(url, json=json)
        if response.status_code != 200:
            QtWidgets.QMessageBox.warning(None, 'Get Agis Ortho', 'wrong status_code=' + str(response.status_code))
            return

        pdf_url = response.text

        # download the pdf
        projectDir = self.project.getProjectDir()
        if not projectDir:
            QtWidgets.QMessageBox.warning(None, 'Get Agis Ortho', 'Projekt zuerst speichern')
            return
        gis_folder = config.getFolderPath(projectDir, "maps")
        if not os.path.isdir(gis_folder):
            os.makedirs(gis_folder)
        today = date.today()
        filename = today.isoformat() +"_Luftbild_500.pdf"
        path = gis_folder + os.sep + filename
        urllib.request.urlretrieve(pdf_url, path)

        openFolder(path)

        return

    def action_getAgisSurvey(self):
        x = self.obj.swissGridX
        y = self.obj.swissGridY
        if not x or not y:
            QtWidgets.QMessageBox.warning(None, 'Get Agis Survey', 'no coordiantes')
            return

        x = int(float(x))
        y = int(float(y))

        url = "https://www.ag.ch/geoportal/api/v1/print/"

        json = {
          # 1:500 x width=113, y height=97
          "MapExtent":{
            "Xmax":int(x+2000000 + 56),
            "Xmin":int(x+2000000 - 57),
            "Ymax":int(y+1000000 + 48),
            "Ymin":int(y+1000000 - 49)
          },
          "MapServices":[
            {
              "Url":"https://www.ag.ch/geoportal/rest/services/base_landeskarten_sw/MapServer",
              "Opacity":1,
              "Id":"base_landeskarten_sw",
              "Name":"base_landeskarten_sw",
              "LayerType":1,
              "LayersInLegend":[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49],
              "Visible":True,
              "VisibleLayers":[],
              "Version":""
            },
            {
              "Url":"https://www.ag.ch/geoportal/rest/services/va_avdaten/MapServer",
              "Opacity":1,
              "Id":"Amtliche Vermessung",
              "Name":"Amtliche Vermessung",
              "LayerType":0,
              "LayersInLegend":[],
              "Visible":True,
              "VisibleLayers":[0,1,6,7,9,10,11,13,14,15,16],
              "Version":""
            }
          ],
          "CopyrightText":"Die gedruckten Daten haben nur informativen Charakter. Es k\u00f6nnen keine rechtlichen Anspr\u00fcche irgendwelcher Art geltend gemacht werden.\nBitte beachten Sie auch die Ausf\u00fchrungen zum Kartendienst 'va_avdaten' unter https://www.ag.ch/geoportal/api/v1/mapservices/176/documentation.\nQuelle: Daten des Kantons Aargau, Bundesamt f\u00fcr Landestopografie",
          "Width":224.6,
          "Height":194.268,
          "LayoutId":"AgisDefault",
          "Layoutformat":"a4",
          "Layoutsubtitle":self.obj.getHumanAddress(),
          "Layouttitle":"Luftbild",
          "LegendVisible":True,
          "LogoFileName":"logo.wmf",
          "MapOnly":False,
          "MapOnlyImageType":"png",
          "OverviewVisible":False,
          "Scale":500,
          "ScalebarVisible":True,
          "CustomLegendName":"",
          "LayoutOrientation":"quer",
          "Angle":0,
          "Graphics":[]
        }
        response = requests.post(url, json=json)
        if response.status_code != 200:
            QtWidgets.QMessageBox.warning(None, 'Get Agis Survey', 'wrong status_code=' + str(response.status_code))
            return

        pdf_url = response.text

        # download the pdf
        projectDir = self.project.getProjectDir()
        if not projectDir:
            QtWidgets.QMessageBox.warning(None, 'Get Agis Survey', 'Projekt zuerst speichern')
            return
        gis_folder = config.getFolderPath(projectDir, "maps")
        if not os.path.isdir(gis_folder):
            os.makedirs(gis_folder)
        today = date.today()
        filename = today.isoformat() +"_Vermessung_500.pdf"
        path = gis_folder + os.sep + filename
        urllib.request.urlretrieve(pdf_url, path)

        openFolder(path)

        return

class MunicipalityPage(Page):
    def connect(self):
        ui = self.ui
        ui.openMunicipalityWebsite.clicked.connect(self.action_openMunicipalityWebsite)
        ui.createBuildingForm.clicked.connect(self.action_createBuildingForm)
        ui.createGvzDocumentation.clicked.connect(self.action_createGvzDocumentation)

    # Erzeuge Gebäudeversicherung Zürich Formular
    def action_createGvzDocumentation(self):
        projectDir = self.project.getProjectDir()
        if not projectDir:
            return

        gvzDir = config.getFolderPath(projectDir, "authorities")
        gvzPath = gvzDir + os.sep + "01_gvz_dokumentation.pdf"
        if not os.path.isdir(gvzDir):
            os.makedirs(gvzDir)

        ret = self.obj.createGvzDocumentation(gvzPath)
        if isinstance(ret, str):
            QtWidgets.QMessageBox.information(None, 'Error Creating GVZ', ret)
            return

        openFolderIfExists(gvzPath)

    # Erzeuge Solarmeldung
    def action_createBuildingForm(self):
        ret = self.obj.createBuildingForm()
        if isinstance(ret, str):
            QtWidgets.QMessageBox.information(None, 'Error Creating TAG', ret)
            return

    # Gemeinde Webseite öffnen
    def action_openMunicipalityWebsite(self):
        if not self.obj.website:
            return
        openFolder(self.obj.website)

class PowerCompanyPage(Page):
    def connect(self):
        ui = self.ui
        ui.createMundpp.clicked.connect(self.action_createMundpp)
        ui.createTag.clicked.connect(self.action_createTag)
        ui.composeTagEmail.clicked.connect(self.action_composeTagEmail)

    # Erzeuge Anschlussgesuch
    def action_createTag(self):
        global config

        projectDir = self.project.getProjectDir()
        if not projectDir:
            return
        
        # assemble the path
        today = date.today()
        form = self.obj.getTagForm()
        ext = os.path.splitext(form["file"])[1] if form else ".pdf"
        tagName = "%04d-%02d-%02d_tag_fill%s" % (today.year, today.month, today.day, ext)

        tagDir = config.getFolderPath(projectDir, "gridOperator")
        tagPath = tagDir + os.sep + tagName
        if not os.path.isdir(tagDir):
            os.makedirs(tagDir)
        
        ret = self.obj.createTag(self.project, tagPath)
        if isinstance(ret, str):
            QtWidgets.QMessageBox.information(None, 'Error Creating TAG', ret)
            return
            
        openFolderIfExists(tagPath)
        now = date.today()
        self.project.progress.tagSent = now.isoformat()

    # Sende Tag
    def action_composeTagEmail(self):
        global config
        model = self.project
        
        to = model.powerCompany.tagContact.email
        b = model.building
        subject = "TAG PV-Anlage " + str(b.street) + " " + str(b.streetNumber) + " in " + str(b.city)
        body = "Guten Tag\n\nIm Anhang finden Sie das Anschlussgesuch für eine PV-Anlage in " + str(b.city) + " sowie die zusätzlich benötigten Unterlagen.\n"
        body += "\nmit freundlichen Grüssen\n\n" + str(config.installer_firstName) + " " + str(config.installer_lastName)
        att = [""]
        composeEmail(config.installer_email, to, subject, body, att)

    # Create M+PP
    def action_createMundpp(self):
        self.createDocument("mundpp")

class ProgressPage(Page):
    def connect(self):
        # connect all pb_progress_* with action_progress
        for key, value in self.ui.__dict__.items():
            if key.startswith("pb_"):
                el = getattr(self.ui, key)
                el.clicked.connect(lambda _, x=key: self.action_progress(x))

    def action_progress(self, buttonName):
        actionName = buttonName.replace("pb_", "")

        now = date.today()
        attrName = "obj_" + actionName
        getattr(self.ui, attrName).setText(str(now))

class PlantPage(Page):
    pass


PAGES = {
    PvProject: PvProjectPage,
    Contacts: ContactsPage,
    Contact: ContactPage,
    Building: BuildingPage,
    Municipality: MunicipalityPage,
    PowerCompany: PowerCompanyPage,
    Progress: ProgressPage,
    Plant: PlantPage,
}


# the page for a model object
def createPage(ui, obj, app):
    return PAGES[type(obj)](ui, obj, app)
