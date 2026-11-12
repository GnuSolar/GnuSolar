#!/usr/bin/python
# -*- coding: utf-8 -*-

# The site: one place with everything planned and built there over time, and
# the projects that did it (doc/file_format.md). One file is one site. The
# attributes are the fields of the file.
#
# Forms, document templates and form scripts written for file version 2 find
# the project they know in the properties building, plant, progress,
# powerCompany and comment (model/compat.py).

import os
import time

from model.ModelNode import ModelNode, newId
from model.Contact import Contact, ContactList, Address
from model.Site import Supply, DesignTemperature, Municipality, GridOperator
from model.Building import Building, Surrounding
from model.Device import DeviceType, Device, String, Connection
from model.Project import Project, Quote, Design, PROJECT_TYPES
from model.compat import SiteView, PlantView, ProgressView
from model import values

import plugins
import formats.pvp

from Config import *

class PvSite(ModelNode):

    # the global config is only linked here, not saved with the site
    _notSaved = ("config", "owner")

    _parts = {
        "contacts": Contact,
        "buildings": Building,
        "surroundings": Surrounding,
        "types": DeviceType,
        "devices": Device,
        "strings": String,
        "connections": Connection,
        "designs": Design,
        "quotes": Quote,
        "projects": Project,
    }
    _types = {"latitude": "number", "longitude": "number", "elevation": "number", "annualConsumption": "number",
              "horizon": "points", "plugins": "json", "ext": "json"}
    _always = ("contacts", "buildings", "surroundings", "types", "devices", "strings", "connections",
               "designs", "quotes", "projects", "notes", "plugins", "ext")

    def __init__(self, path=""):
        self.config = config
        self._savePath = None
        self._top = self
        self._currentProject = None

        self.id = None
        self.created = None             # point in time, not a day
        self.modified = None
        self.generator = None           # the program that wrote the file
        self.currency = None            # of every amount in the site, ISO 4217

        # the place
        self.label = None
        self.address = Address(self)
        self.latitude = None            # WGS84, degrees: the origin of the coordinate system
        self.longitude = None
        self.elevation = None           # m above sea level
        self.plotNumber = None          # Parzelle Nummer
        self.supply = Supply(self)
        self.annualConsumption = None   # Wh per year
        self.designTemperature = DesignTemperature(self)
        self.horizon = []               # [[azimuth, elevation], ...]
        self.municipality = Municipality(self)
        self.gridOperator = GridOperator(self)

        self.contacts = ContactList(self)
        self.buildings = []
        self.surroundings = []
        self.types = []
        self.devices = []
        self.strings = []
        self.connections = []
        self.designs = []
        self.quotes = []
        self.projects = []
        self.notes = ""
        self.plugins = []               # every plugin that wrote data to the file
        self.ext = {}

        if path != "":
            self.open(path)

    # ---- parts ------------------------------------------------------------

    def allRoofs(self):
        return [roof for building in self.buildings for roof in building.roofs]

    def allModuleGroups(self):
        return [group for roof in self.allRoofs() for group in roof.moduleGroups]

    # the entries of a list of the site; moduleGroups and roofs are
    # collected from all buildings
    def collection(self, name):
        if name == "moduleGroups":
            return self.allModuleGroups()
        if name == "roofs":
            return self.allRoofs()
        return self.__dict__[name]

    # the object with an id in a list of the site, None if there is none
    def byId(self, name, objectId):
        if objectId is None:
            return None
        for obj in self.collection(name):
            if obj.id == objectId:
                return obj
        return None

    # ---- projects -----------------------------------------------------------

    # The project the forms and documents work on: the one selected in the
    # window, otherwise the newest. A site always has one.
    @property
    def currentProject(self):
        if self._currentProject is not None and self._currentProject in self.projects:
            return self._currentProject
        if not self.projects:
            self.addProject("new_system")
        return self.projects[-1]

    @currentProject.setter
    def currentProject(self, project):
        self._currentProject = project

    # The first project works in the site folder itself. A later one gets
    # a folder of its own, so its documents don't collide with the ones of
    # the first. The name is a suggestion (page of the project, "Unterordner"),
    # the folder is created with the first document.
    def addProject(self, projectType, title=None):
        folder = self.newProjectFolder(projectType) if self.projects else ""
        project = self.addPart("projects", type=projectType, title=title, folder=folder)
        project.deriveState()
        return project

    # "2026 Batterie", a name no other project has
    def newProjectFolder(self, projectType):
        name = "%d %s" % (time.localtime().tm_year, PROJECT_TYPES.get(projectType, projectType))
        used = [project.folder for project in self.projects]
        folder, count = name, 1
        while folder in used:
            count += 1
            folder = "%s %d" % (name, count)
        return folder

    # A module group belongs to the generator (pv_array) of the project that
    # builds it. The project gets a generator if it has none.
    def addToGenerator(self, group, project=None):
        project = project or self.currentProject
        arrays = project.getDevices("pv_array")
        if arrays:
            arrays[0].set("moduleGroupIds", (arrays[0].get("moduleGroupIds") or []) + [group.id])
            return arrays[0]
        device = self.addPart("devices", kind="pv_array", projectId=project.id, moduleGroupIds=[group.id])
        device.set("from", project.commissioned)
        return device

    # folder of a project, None if the site is not saved yet
    def getProjectDir(self, project=None):
        project = project or self.currentProject
        siteDir = self.getSiteDir()
        if not siteDir:
            return None
        return os.path.join(siteDir, project.folder) if project.folder else siteDir

    # ---- documents ----------------------------------------------------------

    # what a document created by GnuSolar is: kind => (part, kind of the part, kind of the document)
    DOCUMENTS = {
        "quote": ("quote", None, "quote"),
        "partial_invoice": ("invoice", "partial", "invoice"),
        "final_invoice": ("invoice", "final", "invoice"),
        "small_invoice": ("invoice", "small", "invoice"),
        "documentation": ("step", "documentation", "filled"),
        "mundpp": ("step", "measurement", "filled"),
        "tag": ("step", "ch.tag", "filled"),
        "gvz": ("step", "documentation", "filled"),
    }

    # Record a document GnuSolar created for the current project: a quote and
    # an invoice become a new entry with the number of the file, anything
    # else is added to its step. Returns the part the document is in.
    def addDocument(self, kind, path):
        if kind not in self.DOCUMENTS or not self.getSiteDir():
            return None
        part, partKind, documentKind = self.DOCUMENTS[kind]
        project = self.currentProject
        relPath = os.path.relpath(path, self.getSiteDir()).replace(os.sep, "/")
        document = {"path": relPath, "kind": documentKind}
        number = os.path.splitext(os.path.basename(path))[0]
        if part == "quote":
            return self.addPart("quotes", number=number, state="draft", projectId=project.id, documents=[document])
        if part == "invoice":
            return project.addPart("invoices", kind=partKind, number=number, documents=[document])
        step = project.getStep(partKind) or project.addPart("steps", kind=partKind)
        if document not in step.documents:
            step.documents.append(dict(document, date=values.today()))
        return step

    # ---- the project of file version 2 -----------------------------------

    @property
    def building(self):
        return SiteView(self)

    @property
    def plant(self):
        return PlantView(self, self.currentProject)

    # what was installed before the current project and is still there
    @property
    def existing(self):
        return PlantView(self, self.currentProject, existing=True)

    @property
    def progress(self):
        return ProgressView(self, self.currentProject)

    @property
    def powerCompany(self):
        return self.gridOperator

    @property
    def comment(self):
        return self.notes

    @comment.setter
    def comment(self, text):
        self.notes = text or ""

    # ---- new projects -------------------------------------------------------

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
        self.currentProject.inquiry = values.today()
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

    # ---- Serializing stuff --------------------------------------------------

    # defaults for ModelNode.fromDict
    def _initDefaults(self):
        self.__init__()

    def fromDict(self, data):
        savePath = self._savePath
        super().fromDict(data)
        self._savePath = savePath

    # The owner and the electrician are always there for the forms; while
    # they are empty they are not written.
    def toDict(self):
        data = super().toDict()
        data["contacts"] = [c.toDict() for c in self.contacts if not c.isEmpty()]
        data["plugins"] = plugins.pluginList(data)
        return data

    # what a program does to a site before it writes it
    def prepareSave(self):
        now = int(time.time())
        if not self.id:
            self.id = newId()
        if not self.created and not self._savePath:
            self.created = now
        if not self.currency:
            self.currency = "CHF"
        self.modified = now
        self.generator = "GnuSolar " + Config.getAppVersion()
        for project in self.projects:
            project.changed()

    # folder of the site, None if not saved yet
    def getSiteDir(self):
        if not self._savePath:
            return None
        return os.path.dirname(self._savePath)

    # open from disk, the file format is in formats/pvp.py
    def open(self, path):
        formats.pvp.load(self, path)
        self._savePath = path

    # save to disk as json under specified path
    def saveAs(self, path):
        self.prepareSave()
        self._savePath = path
        return self.save(prepared=True)

    # save to disk
    def save(self, prepared=False):
        if not prepared:
            self.prepareSave()
        formats.pvp.save(self, self._savePath)
        return True

model = PvSite()
