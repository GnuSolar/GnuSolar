#!/usr/bin/python
# -*- coding: utf-8 -*-

# Designs, quotes and projects (doc/file_format.md, sections 11 and 12).
#
# A project is a job at the site: the first installation, a battery, a
# replacement. It has its own steps with authorities, documents and invoices.

from model.ModelNode import ModelNode
from model import states

# type => caption
PROJECT_TYPES = {
    "new_system": "PV-Anlage",
    "extension": "Erweiterung",
    "battery": "Batterie",
    "charger": "Ladestation",
    "heat_pump": "Wärmepumpe",
    "replacement": "Ersatz",
    "repair": "Reparatur",
    "inspection": "Kontrolle",
    "service": "Service",
}
PROJECT_STATES = ("inquiry", "quoted", "running", "in_operation", "completed", "rejected", "inactive")
CONSTRUCTION_TYPES = ("on_roof", "in_roof", "facade", "flat_roof", "ground")

# kind => caption of the steps every country has. The steps with authorities
# come from the country extension (plugins).
STEP_KINDS = {
    "material": "Material",
    "measurement": "Mess- und Prüfprotokoll",
    "documentation": "Dokumentation",
    "acceptance": "Abnahme",
}
STEP_STATES = ("open",) + states.STEP_STATES + ("rejected",)

INVOICE_KINDS = {"partial": "Akonto", "final": "Schlussrechnung", "small": "Kleinrechnung", "credit": "Gutschrift"}
QUOTE_STATES = ("draft", "sent", "accepted", "rejected", "expired")
ITEM_KINDS = ("device", "material", "service", "discount", "text")
ITEM_UNITS = ("piece", "m", "m2", "h", "lump_sum")


# One variant of what could be built
class Design(ModelNode):

    _types = {"expectedYield": "json", "documents": "json", "ext": "json"}

    def __init__(self, top=None):
        self._top = top
        self.id = None
        self.label = None
        self.description = None
        self.expectedYield = {}     # {"annual": Wh, "source": ..., "date": ...}
        self.documents = []
        self.ext = {}


# A quote sent to the client. Once sent it doesn't change.
class Quote(ModelNode):

    _types = {"date": "date", "validUntil": "date", "items": "json", "total": "number", "documents": "json",
              "ext": "json"}

    def __init__(self, top=None):
        self._top = top
        self.id = None
        self.number = None
        self.date = None
        self.variant = None
        self.designId = None
        self.validUntil = None
        self.state = None           # see QUOTE_STATES
        self.items = []
        self.total = None
        self.currency = None
        self.documents = []
        self.ext = {}

    def hasContent(self):
        return any(key not in ("id", "date", "state") for key in self.toDict())


# Something done with an authority, the grid operator, a subsidy office or a
# supplier
class Step(ModelNode):

    _types = {"dates": "json", "documents": "json", "ext": "json"}

    def __init__(self, top=None):
        self._top = top
        self.id = None
        self.kind = None
        self.state = "open"         # see STEP_STATES
        self.dates = {}             # state => date it was reached
        self.documents = []
        self.notes = None
        self.ext = {}

    def setDate(self, state, day):
        if day is None:
            self.dates.pop(state, None)
        else:
            self.dates[state] = day
        self.changed()

    def changed(self):
        self.state = states.stepState(self.dates)

    def getCaption(self):
        return "Schritt: " + str(self.kind)

    def hasContent(self):
        return bool(self.dates or self.documents or self.notes or self.ext)


class Invoice(ModelNode):

    _types = {"date": "date", "amount": "number", "paid": "date", "documents": "json", "ext": "json"}

    def __init__(self, top=None):
        self._top = top
        self.id = None
        self.number = None
        self.kind = None            # see INVOICE_KINDS
        self.date = None
        self.amount = None
        self.currency = None
        self.paid = None            # date the payment arrived
        self.documents = []
        self.ext = {}

    def hasContent(self):
        return any(key not in ("id", "kind") for key in self.toDict())


class Project(ModelNode):

    _parts = {"designs": Design, "quotes": Quote, "steps": Step, "invoices": Invoice}
    _types = {"inquiry": "date", "roofMeasure": "date", "roofMeasured": "date", "ordered": "date",
              "rejected": "date", "constructionStart": "date", "constructionSort": "date",
              "constructionFixed": "bool", "commissioned": "date", "completed": "date", "archived": "date",
              "inactive": "date", "totalCost": "number", "items": "json", "ext": "json"}
    _always = ("folder",)

    def __init__(self, top=None):
        self._top = top
        self.id = None
        self.type = None            # see PROJECT_TYPES
        self.title = None
        self.state = None           # see PROJECT_STATES, derived from the dates
        self.quoteId = None         # the quote the client accepted
        self.folder = ""            # subfolder of the project in the site folder, "" is the site folder

        self.inquiry = None
        self.roofMeasure = None
        self.roofMeasured = None
        self.ordered = None
        self.rejected = None
        self.constructionStart = None
        self.constructionSort = None    # only to sort the construction planning
        self.constructionFixed = None   # the construction date can not be moved
        self.commissioned = None        # first day of operation (Inbetriebnahme)
        self.completed = None
        self.archived = None
        self.inactive = None

        self.constructionType = None    # see CONSTRUCTION_TYPES
        self.totalCost = None
        self.items = []
        self.designs = []           # variants of what could be built
        self.quotes = []            # sent to the client for this project
        self.steps = []
        self.invoices = []
        self.notes = None
        self.ext = {}

    # the quotes made for this project
    def getQuotes(self):
        return list(self.quotes)

    def deriveState(self):
        self.state = states.projectState(self.__dict__, quoted=any(q.date for q in self.getQuotes()))
        return self.state

    def changed(self):
        if self.folder is None:
            self.folder = ""
        self.deriveState()

    # The devices of the project go into operation with it, and the devices
    # they replace are removed that day.
    def set(self, key, value):
        before = self.__dict__.get(key)
        super().set(key, value)
        if key != "commissioned" or not self._top:
            return
        for device in self.getDevices():
            if device.get("from") in (None, before):
                device.set("from", value)
            replaced = self._top.byId("devices", device.replacesId)
            if replaced is not None and replaced.to in (None, before):
                replaced.to = value

    # the step of a kind, None if the project doesn't have it
    def getStep(self, kind):
        for step in self.steps:
            if step.kind == kind:
                return step
        return None

    # the number'th (from 0) invoice of a kind
    def getInvoice(self, kind, number=0):
        found = [i for i in self.invoices if i.kind == kind]
        return found[number] if number < len(found) else None

    # the devices this project installed
    def getDevices(self, kind=None):
        if not self._top:
            return []
        return [d for d in self._top.devices if d.projectId == self.id and (kind is None or d.kind == kind)]

    def getCaption(self):
        return self.title or PROJECT_TYPES.get(self.type, str(self.type))
