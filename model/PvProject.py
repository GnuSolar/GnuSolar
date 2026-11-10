#!/usr/bin/python
# -*- coding: utf-8 -*-

# The project: one site with everything planned and built there over time
# (doc/file_format.md). The attributes are the fields of the file.
#
# Forms, document templates and form scripts written for file version 2 find
# the project they know in the properties building, plant, progress,
# municipality, powerCompany and comment (model/compat.py).

import os
import time

from model.ModelNode import ModelNode, newId
from model.Contact import Contact, ContactList
from model.Site import Site
from model.Building import Building, Surrounding
from model.Device import DeviceType, Device, String, Connection
from model.Order import Order, Quote, Design
from model.compat import SiteView, PlantView, ProgressView
from model import values

import plugins
import formats.pvp

from Config import *

class PvProject(ModelNode):

    # the global config is only linked here, not saved with the project
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
        "orders": Order,
    }
    _types = {"plugins": "json", "ext": "json"}
    _always = ("site", "contacts", "buildings", "surroundings", "types", "devices", "strings", "connections",
               "designs", "quotes", "orders", "notes", "plugins", "ext")

    def __init__(self, path=""):
        self.config = config
        self._savePath = None
        self._top = self
        self._currentOrder = None

        self.id = None
        self.created = None             # point in time, not a day
        self.modified = None
        self.generator = None           # the program that wrote the file
        self.currency = None            # of every amount in the project, ISO 4217
        self.site = Site(self)
        self.contacts = ContactList(self)
        self.buildings = []
        self.surroundings = []
        self.types = []
        self.devices = []
        self.strings = []
        self.connections = []
        self.designs = []
        self.quotes = []
        self.orders = []
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

    # the entries of a list of the project; moduleGroups and roofs are
    # collected from all buildings
    def collection(self, name):
        if name == "moduleGroups":
            return self.allModuleGroups()
        if name == "roofs":
            return self.allRoofs()
        return self.__dict__[name]

    # the object with an id in a list of the project, None if there is none
    def byId(self, name, objectId):
        if objectId is None:
            return None
        for obj in self.collection(name):
            if obj.id == objectId:
                return obj
        return None

    # ---- orders -----------------------------------------------------------

    # The order the forms and documents work on: the one selected in the
    # window, otherwise the newest. A project always has one.
    @property
    def currentOrder(self):
        if self._currentOrder is not None and self._currentOrder in self.orders:
            return self._currentOrder
        if not self.orders:
            self.addOrder("new_system")
        return self.orders[-1]

    @currentOrder.setter
    def currentOrder(self, order):
        self._currentOrder = order

    def addOrder(self, orderType, title=None):
        order = self.addPart("orders", type=orderType, title=title)
        order.deriveState()
        return order

    # folder of an order, None if the project is not saved yet
    def getOrderDir(self, order=None):
        order = order or self.currentOrder
        projectDir = self.getProjectDir()
        if not projectDir:
            return None
        return os.path.join(projectDir, order.folder) if order.folder else projectDir

    # ---- the project of file version 2 --------------------------------------

    @property
    def building(self):
        return SiteView(self)

    @property
    def plant(self):
        return PlantView(self, self.currentOrder)

    # what was installed before the current order and is still there
    @property
    def existing(self):
        return PlantView(self, self.currentOrder, existing=True)

    @property
    def progress(self):
        return ProgressView(self, self.currentOrder)

    @property
    def municipality(self):
        return self.site.municipality

    @property
    def powerCompany(self):
        return self.site.gridOperator

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
        self.currentOrder.inquiry = values.today()
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

    # what a program does to a project before it writes it
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
        for order in self.orders:
            order.changed()

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
        self.prepareSave()
        self._savePath = path
        return self.save(prepared=True)

    # save to disk
    def save(self, prepared=False):
        if not prepared:
            self.prepareSave()
        formats.pvp.save(self, self._savePath)
        return True

model = PvProject()
