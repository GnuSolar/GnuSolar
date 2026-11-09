#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# Photovoltaics Project Base Class

from model.ModelNode import ModelNode
import formats.pvp
import subprocess
import os
import datetime
from datetime import date

from model.Contacts import Contacts
from model.Building import Building
from model.Municipality import Municipality
from model.PowerCompany import PowerCompany
from model.Progress import Progress
from model.Plant import Plant

from Config import *

class PvProject(ModelNode):

    # the global config is only linked here, not saved with the project
    _notSaved = ("config",)

    def __init__(self, path=""):
        self.config = config
        self._savePath = None
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
        
        
    # Serializing stuff
    # defaults for ModelNode.fromDict
    def _initDefaults(self):
        self.__init__()

    # folder of the project, None if not saved yet
    def getProjectDir(self):
        if not self._savePath:
            return None
        return os.path.dirname(self._savePath)

    # open from disk, the file format is in formats/pvp.py
    def open(self, path):
        formats.pvp.load(self, path)
        self._savePath = path
    
    # save to disk as json under specified path
    def saveAs(self, path):
        self._savePath = path
        return self.save()
    
    # save to disk
    def save(self):
        formats.pvp.save(self, self._savePath)
        return True

model = PvProject()
