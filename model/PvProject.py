#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# Photovoltaics Project Base Class

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

class PvProject:
    
    def __init__(self, path=""):
        self._savePath = None
        self._ui = None
        self.contacts = Contacts()
        self.building = Building()
        self.municipality = Municipality()
        self.powerCompany = PowerCompany()
        self.progress = Progress()
        self.plant = Plant()
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
        
        config.nextQuoteNumber = config.nextQuoteNumber + 1
        config.write()

        openFolderIfExists(quotePath)

    # Create Partial Invoice
    def action_createPartialInvoice(self):
        global config

        invoicePath = createFromTemplate("partial_invoice", self._savePath, self)
        
        config.nextInvoiceNumber = config.nextInvoiceNumber + 1
        config.write()

        openFolderIfExists(invoicePath)

    # Create Final Invoice
    def action_createFinalInvoice(self):
        global config

        invoicePath = createFromTemplate("final_invoice", self._savePath, self)
        
        config.nextInvoiceNumber = config.nextInvoiceNumber + 1
        config.write()

        openFolderIfExists(invoicePath)

    # Create Small Invoice
    def action_createSmallInvoice(self):
        global config

        invoicePath = createFromTemplate("small_invoice", self._savePath, self)
        
        config.nextInvoiceNumber = config.nextInvoiceNumber + 1
        config.write()

        openFolderIfExists(invoicePath)

    # Create swiss QR Bill
    def action_createQrBill(self):
        global config

        qrAmount = self._ui.qrbill_amount.text()
        qrInfo = self._ui.qrbill_info.text()
        
        projectDir = os.path.dirname(self._savePath)
        if not os.path.isdir(projectDir):
            QtWidgets.QMessageBox.warning(None, templateType + ' erstellen', 'Pfad nicht gefunden\n' + self.path)
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
                    'name': debtor.lastName + " " + debtor.firstName, 
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

    # Create Documentation
    def action_createDocumentation(self):
        documentationPath = self.createFromTemplate("documentation")
        openFolderIfExists(documentationPath)






    # Serializing stuff

    def toJson(self):
        jsonpickle.set_preferred_backend('json')
        jsonpickle.set_encoder_options('json', sort_keys=True, indent=4)
        
        _savePath = self._savePath      # don't serialize this attribute
        del self._savePath
        _ui = self._ui
        del self._ui
        
        ret = jsonpickle.encode(self)
        
        self._savePath = _savePath
        self._ui = _ui
        
        return ret
        
    def fromJson(self, json_str):
        ret = jsonpickle.decode(json_str)

        # Migrate data from older models.

        # plantLocation was renamed to building
        try:
            ret.building = ret.plantLocation
        except Exception:
            pass
        
        # owner.address is no more
        try:
            ret.owner.street = ret.owner.address.street
            ret.owner.streetNumber = ret.owner.address.streetNumber
            ret.owner.zip = ret.owner.address.zip
            ret.owner.city = ret.owner.address.city
        except Exception:
            pass

        # owner moved to contacts._owner
        if hasattr(ret, "owner"):
            if not hasattr(ret, "contacts"):
                ret.contacts = Contacts()
            ret.contacts._owner = ret.owner

        # loop over all attributes from self and copy them over from ret
        # makes sure if you open a file with an older model, the attributes 
        # default to default :)
        self._copyOver(self, ret)

        
    def _copyOver(self, src, dest):
        for key, value in src.__dict__.items():

            if not hasattr(dest, key):
                continue
                
            if hasattr(value, "__dict__") and isinstance(value.__dict__, dict):
                self._copyOver(getattr(src, key), getattr(dest, key))
            else:
                setattr(src, key, getattr(dest, key))
    
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
