#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# Photovoltaics Project Base Class

from model.ModelNode import ModelNode
import json
import jsonpickle
import subprocess
import os
import datetime

from model.Contact import *
from model.Contacts import *
from model.Building import *
from model.Progress import *
from model.PowerCompany import *
from model.Plant import *

from GnuSolar import *
from Config import *

class PvProject(ModelNode):

    # the global config is only linked here, not saved with the project
    _notSaved = ("config",)

    def __init__(self, path=""):
        self.config = config
        self._savePath = None
        self._ui = None
        self.contacts = Contacts(self)
        self.building = Building(self)
        self.municipality = Municipality(self)
        self.powerCompany = PowerCompany(self)
        self.progress = Progress(self)
        self.plant = Plant(self)
        self.comment = None
        
        # project state:
        #  'Request'       Anfrage
        #  'Quote'         offeriert
        #  'Wait'          wartet auf iergendwas
        #  'Order'         Zusage
        #  'Construction'  im Bau
        #  'Running'       im Betrieb
        #  'BuiltOther'    jemand anders gebaut
        self.state = None

        if path != "":
            self.open(path)

    def initFromAddress(self, street, streetNumber, zipCode, city):
        if not self.building.street:
            self.building.street = street
        if not self.building.streetNumber:
            self.building.streetNumber = streetNumber
        if not self.building.zip:
            self.building.zip = zipCode
        if not self.building.city:
            self.building.city = city
        
        # Anfrage erhalten gleich jetzt
        today = date.today()
        self.progress.inquiryReceived = today.isoformat()
        return

    # updates location, municipality and powerCompany from Address
    def updateFromAddress(self):
        self.building.coordinatesFromAddress()
        self.building.queryPlotNumber()
        self.building.queryZoneing()
        
        if self.building.municipalityCode:
            self.municipality.fromCode(self.building.municipalityCode)
        else:
            return "no municipalityCode found for this Address"

        powId = self.building.getPowerCompanyId()
        if powId:
            self.powerCompany.fromId(powId)
        else:
            return "no PowerCompany found for building. BuildingId=" + str(self.building.swissGridX) + "/" + str(self.building.swissGridY)
        
        return True
        
        
    # Ui hooks
    def getTreeCaption(self):
        return "PV Projekt"

    def initUi(self, ui):
        self._ui = ui
        ui.openProjectFolder.clicked.connect(self.action_openProjectFolder)
        ui.createQuote.clicked.connect(self.action_createQuote)
        ui.createPartialInvoice.clicked.connect(self.action_createPartialInvoice)
        ui.createFinalInvoice.clicked.connect(self.action_createFinalInvoice)
        ui.createSmallInvoice.clicked.connect(self.action_createSmallInvoice)
        ui.createQrBill.clicked.connect(self.action_createQrBill)
        ui.createDocumentation.clicked.connect(self.action_createDocumentation)

    def action_openProjectFolder(self):
        if not self._savePath:
            return
        folder = os.path.dirname(self._savePath)
        openFolderIfExists(folder)

    def action_createQuote(self):
        global config

        quotePath = createFromTemplate("quote", self._savePath, self)

        openFolderIfExists(quotePath)

    # Create Partial Invoice
    def action_createPartialInvoice(self):
        global config

        invoicePath = createFromTemplate("partial_invoice", self._savePath, self)

        openFolderIfExists(invoicePath)

    # Create Final Invoice
    def action_createFinalInvoice(self):
        global config

        invoicePath = createFromTemplate("final_invoice", self._savePath, self)

        openFolderIfExists(invoicePath)

    # Create Small Invoice
    def action_createSmallInvoice(self):
        global config

        invoicePath = createFromTemplate("small_invoice", self._savePath, self)

        openFolderIfExists(invoicePath)

    # Create Documentation
    def action_createDocumentation(self):
        documentationPath = createFromTemplate("documentation", self._savePath, self)
        openFolderIfExists(documentationPath)

    # Create swiss QR Bill
    def action_createQrBill(self):
        global config
        if not self._savePath:
            QtWidgets.QMessageBox.warning(None, 'QR Bill', 'TODO: ohne Pfad')
            return

        qrAmount = self._ui.qrbill_amount.text()
        qrInfo = self._ui.qrbill_info.text()
        
        projectDir = os.path.dirname(self._savePath)
        if not os.path.isdir(projectDir):
            QtWidgets.QMessageBox.warning(None, 'QR Bill', 'Pfad nicht gefunden\n' + self._savePath)
            return

        today = date.today()
        fileName = "QR" + today.isoformat() + ".pdf"
        outDir =  projectDir + os.sep + "fin"
        qrPath = outDir + os.sep + fileName
        if not os.path.isdir(outDir):
            os.makedirs(outDir)

        debtor = self.contacts.owner
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

        self._ui.qrbill_amount.setText("")
        self._ui.qrbill_info.setText("")

        openFolderIfExists(qrPath)

    # Serializing stuff
    def toJson(self):
        jsonpickle.set_preferred_backend('json')
        jsonpickle.set_encoder_options('json', sort_keys=True, indent=4)
        
        ret = jsonpickle.encode(self)
        
        return ret
        
    def fromJson(self, json_str):
        # files from before the ModelNode format have no py/state, they were
        # converted with tools/migrate_pvp.py on 2026-11-09
        if "py/state" not in json.loads(json_str):
            raise Exception("Old file format, convert it with tools/migrate_pvp.py of a GnuSolar version from before 2026-11-09")

        ret = jsonpickle.decode(json_str)

        # take over the saved data, the runtime attributes (_savePath, config) stay
        self.__dict__.update(ret.__getstate__())
        self.link(self)

    # defaults for ModelNode.__setstate__
    def _initDefaults(self):
        self.__init__()

    # folder of the project, None if not saved yet
    def getProjectDir(self):
        if not self._savePath:
            return None
        return os.path.dirname(self._savePath)

    # open from disk
    def open(self, path):
        self._savePath = path
        f = open(path)
        json_str = f.read()
        f.close()
    
        self.fromJson(json_str)
    
    # save to disk as json under specified path
    def saveAs(self, path):
        self._savePath = path
        return self.save()
    
    # save to disk
    def save(self):
        json = self.toJson()

        f = open(self._savePath, 'w')
        f.write(json)
        f.close()
        return True

model = PvProject()
