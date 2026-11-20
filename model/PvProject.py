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

# the types of project: the code saved in the file, the name shown
PROJECT_TYPES = (
    ("pvSystem", "PV-Anlage"),
    ("battery", "Batterie"),
    ("chargingPile", "Ladestation"),
    ("other", "Anderes"),
)

# the name shown for a type code, the code itself if it is unknown
def projectTypeName(code):
    return dict(PROJECT_TYPES).get(code, code or "")

# the parts an extension takes over from the project it extends: the place,
# the people and the offices. The plant, the dates and the comment are its own.
EXTENSION_COPIES = ("building", "contacts", "municipality", "powerCompany")

# the folder for the next extension of the project in folder projectDir:
# <projectDir>_2, or _3 and so on if that one exists already
def nextExtensionDir(projectDir):
    n = 2
    while os.path.exists(projectDir + "_" + str(n)):
        n += 1
    return projectDir + "_" + str(n)

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

        # what the project builds, a code of PROJECT_TYPES
        self.type = "pvSystem"

        # the project this one extends (a battery added to an existing plant):
        # the folder of that project, relative to the folder of this one and
        # with "/" between the parts, e.g. "../Heid 2.3". None if it extends
        # no project.
        self.base = None
        
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

    # the file of the project this one extends, None if there is none
    def getBasePath(self):
        projectDir = self.getProjectDir()
        if not self.base or not projectDir:
            return None
        folder = os.path.join(projectDir, *self.base.split("/"))
        return os.path.join(os.path.normpath(folder), "plant.pvp")

    # the value of base for the project in the folder baseDir
    def baseFromFolder(self, baseDir):
        rel = os.path.relpath(baseDir, self.getProjectDir())
        return rel.replace(os.sep, "/")

    # the folder of the first project at this place: of the project this one
    # extends, or of this one if it extends none
    def getRootDir(self):
        basePath = self.getBasePath()
        if basePath and os.path.isfile(basePath):
            return os.path.dirname(basePath)
        return self.getProjectDir()

    # Create a project for the next job at this place, of the given type, in
    # the next free folder next to the first project, which it extends. It
    # takes over the parts of EXTENSION_COPIES as they are now, saved or not.
    # The new project is saved, this one is not changed.
    def createExtension(self, type):
        rootDir = self.getRootDir()
        data = self.toDict()
        ext = PvProject()
        ext.fromDict({k: data[k] for k in EXTENSION_COPIES})
        ext.link(ext)
        ext.type = type
        ext.progress.inquiryReceived = date.today().isoformat()

        folder = nextExtensionDir(rootDir)
        os.makedirs(folder)
        ext._savePath = os.path.join(folder, "plant.pvp")
        ext.base = ext.baseFromFolder(rootDir)
        ext.save()
        return ext

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
