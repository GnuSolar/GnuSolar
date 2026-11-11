#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The buttons of the pages of the project window which do more than adding
# and deleting parts (gui/tree.py): creating documents, lookups, calls and
# e-mails.
#
# A page handles its buttons: it asks for what is missing, shows messages,
# opens folders, and calls the model, documents and services for the actual
# work. The model itself knows nothing about the window.
#
#   page = createPage(obj, app)     None if the page has no such buttons
#   page.actions                    the buttons above the fields
#   page.fieldActions               path of a field => the button beside it
#
# obj is the model object shown (PvProject, Contact, ...), app the GnuSolar
# application (None in the address book).

import os
import json
import tempfile
import urllib.request
from datetime import date

import requests
from PyQt5 import QtWidgets

import documents.templates
from documents import DocumentError
from gui.tree import Action
from Config import config
from Usefull import openFolder, openFolderIfExists, composeEmail, callSip

from model.PvProject import PvProject
from model.Contact import Contact
from model.Site import Municipality, GridOperator
from model.compat import SiteView


# Ask for some texts in one dialog. Returns the texts, None if cancelled.
def askTexts(title, captions):
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle(title)
    layout = QtWidgets.QFormLayout(dialog)
    inputs = []
    for caption in captions:
        inputs.append(QtWidgets.QLineEdit())
        layout.addRow(caption, inputs[-1])
    buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return None
    return [el.text() for el in inputs]


class Page:
    def __init__(self, obj, app):
        self.obj = obj
        self.app = app
        self.project = obj if isinstance(obj, PvProject) else getattr(obj, "_top", None)
        self.actions = [self._action(text, func) for text, func in self.buttons()]
        self.fieldActions = {path: self._action(text, func) for path, (text, func) in self.fieldButtons().items()}

    def _action(self, text, func):
        return Action(text, func, refresh=False)

    # the buttons above the fields: [(text, method)]
    def buttons(self):
        return []

    # the buttons beside a field: path => (text, method)
    def fieldButtons(self):
        return {}

    # the project was changed: mark it, build the tree and the page anew
    def changed(self):
        if self.app is not None:
            self.app.action_changed()
            self.app.showModel(select=self.obj)

    # Create a document from a template, show problems, open the new file
    def createDocument(self, templateType):
        try:
            path = documents.templates.createFromTemplate(templateType, self.project._savePath, self.project, config)
        except DocumentError as e:
            QtWidgets.QMessageBox.warning(None, e.title, str(e))
            return None
        self.recordDocument(templateType, path)
        openFolderIfExists(path)
        return path

    # Note a created document in the project and show it in the tree
    def recordDocument(self, kind, path):
        part = self.project.addDocument(kind, path)
        if part is not None:
            self.changed()


class PvProjectPage(Page):
    def buttons(self):
        return [
            ("Projektordner öffnen", self.action_openProjectFolder),
            ("neue Offerte", self.action_createQuote),
            ("Anlagedoku erstellen", self.action_createDocumentation),
            ("Akontorechnung", self.action_createPartialInvoice),
            ("Schlussrechnung", self.action_createFinalInvoice),
            ("Kleinrechnung", self.action_createSmallInvoice),
            ("QR Bill erstellen", self.action_createQrBill),
        ]

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

        projectDir = os.path.dirname(self.obj._savePath)
        if not os.path.isdir(projectDir):
            QtWidgets.QMessageBox.warning(None, 'QR Bill', 'Pfad nicht gefunden\n' + self.obj._savePath)
            return
        projectDir = self.obj.getOrderDir()

        answer = askTexts("QR Bill", ["Betrag", "Info"])
        if answer is None:
            return
        qrAmount, qrInfo = answer

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

        openFolderIfExists(qrPath)

class ContactPage(Page):
    def fieldButtons(self):
        return {
            "email": ("E-Mail", self.action_composeEmail),
            "email2": ("E-Mail", self.action_composeEmail2),
            "phone": ("Anruf", self.action_callPhone),
            "phone2": ("Anruf", self.action_callPhone2),
            "mobile": ("Anruf", self.action_callMobile),
        }

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
    def buttons(self):
        return [
            ("Update von Adresse", self.action_updateFromAddress),
            ("Get 3D Model", self.action_get3dModel),
            ("Get Agis Ortho", self.action_getAgisOrtho),
            ("Get Agis Survey", self.action_getAgisSurvey),
        ]

    def action_updateFromAddress(self):
        ret = self.project.updateFromAddress()

        self.changed()
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
    def buttons(self):
        return [
            ("Solarmeldung erstellen", self.action_createBuildingForm),
            ("GVZ Dokumentation", self.action_createGvzDocumentation),
        ]

    def fieldButtons(self):
        return {"website": ("Webseite öffnen", self.action_openMunicipalityWebsite)}

    # Erzeuge Gebäudeversicherung Zürich Formular
    def action_createGvzDocumentation(self):
        projectDir = self.project.getOrderDir()
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

        self.recordDocument("gvz", gvzPath)
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
    def buttons(self):
        return [
            ("M+PP erstellen", self.action_createMundpp),
            ("Anschlussgesuch erstellen", self.action_createTag),
        ]

    def fieldButtons(self):
        return {"connectionContact.email": ("TAG E-Mail", self.action_composeTagEmail)}

    # Erzeuge Anschlussgesuch
    def action_createTag(self):
        global config

        projectDir = self.project.getOrderDir()
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
        self.project.addDocument("tag", tagPath)
        self.changed()

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

PAGES = {
    PvProject: PvProjectPage,
    Contact: ContactPage,
    SiteView: BuildingPage,
    Municipality: MunicipalityPage,
    GridOperator: PowerCompanyPage,
}


# the page for a model object, None if it has no buttons of its own
def createPage(obj, app):
    page = PAGES.get(type(obj))
    return page(obj, app) if page else None
