#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The tree of the project window: building the tree from the model, and the
# actions of its nodes (add an order, a step, a device ..., delete a part).
#
# Every tree item has the model object it shows in item.pvpObj.

from PyQt5.QtWidgets import QTreeWidgetItem

from model.ModelNode import ModelNode
from model.PvProject import PvProject
from model.Contact import Contact, ContactList, ROLE_NAMES
from model.Building import Building, Roof, ModuleGroup, Obstacle, Surrounding, OBSTACLE_KINDS, SURROUNDING_KINDS
from model.Device import DeviceType, Device, String, Connection, DEVICE_KINDS, TYPE_KINDS, CONNECTION_KINDS
from model.Order import Order, Step, Invoice, Quote, Design, ORDER_TYPES, INVOICE_KINDS
from model.compat import SiteView, PlantView, ProgressView
from model.checks import check
from gui.captions import caption
from gui.fields import stepKinds

# the devices an order usually brings
ORDER_DEVICE_KINDS = ("inverter", "battery", "meter", "charger", "heat_pump", "heating_rod", "energy_manager",
                      "optimizer")


# A list of the project shown as a node of the tree
class Section:
    def __init__(self, top, key, caption, text):
        self._top = top
        self.key = key
        self.caption = caption
        self.text = text


SECTIONS = (
    ("quotes", "Offerten", "Offerten, die dem Kunden geschickt wurden. Eine gesendete Offerte ändert nicht mehr, "
                           "eine neue Fassung ist eine neue Offerte."),
    ("designs", "Auslegungen", "Varianten, was gebaut werden könnte. Modulgruppen und Offerten verweisen darauf."),
    ("buildings", "Gebäude und Dächer", "Gebäude mit ihren Dachflächen, Hindernissen und Modulgruppen."),
    ("surroundings", "Umgebung", "Was neben den Gebäuden Schatten wirft: Bäume, Nachbarhäuser, Mauern."),
    ("devices", "Geräte", "Alles Installierte: Wechselrichter, Batterien, Zähler, Verteilungen, Sicherungen ... "
                          "Ersetzte Geräte bleiben mit ihrem Enddatum erhalten."),
    ("types", "Typen", "Die Produkte, die das Projekt verwendet: Module, Wechselrichter, Batterien, Montagesysteme."),
    ("strings", "Strings", "Wie die Module an die Wechselrichter angeschlossen sind."),
    ("connections", "Verbindungen", "Kabel zwischen den Geräten: Leistung, Schutzleiter und Signal. Geräte und "
                                    "Verbindungen zusammen sind das Schema der Installation."),
)


# raised by an action which only has something to tell
class Message(Exception):
    pass


# One entry of a context menu or button of a page: func does it and returns
# the object to show afterwards. entries makes it a submenu. confirm is a
# question to ask first. refresh=False: func doesn't change the project, or
# shows the change itself (gui/pages.py).
class Action:
    def __init__(self, text, func=None, entries=None, confirm=None, refresh=True):
        self.text = text
        self.func = func
        self.entries = entries
        self.confirm = confirm
        self.refresh = refresh


# ---- building the tree ------------------------------------------------------

# fill the tree widget with the project
def buildTree(tree, project):
    tree.setColumnCount(1)
    top = QTreeWidgetItem(None, ["PV-Anlage"])
    top.pvpObj = project
    expand = [top]

    # owner and electrician are always there
    project.contacts.owner
    project.contacts.installer_ac
    contacts = _addItem(top, project.contacts)
    expand.append(contacts)
    for contact in project.contacts:
        _addItem(contacts, contact)

    site = _addItem(top, project.building)
    _addItem(site, project.site)
    municipality = _addItem(top, project.municipality)
    _addItem(municipality, project.municipality.mainContact, "Kontakt (Haupt)")
    _addItem(municipality, project.municipality.buildingContact, "Kontakt (Baubehörde)")
    powerCompany = _addItem(top, project.powerCompany)
    _addItem(powerCompany, project.powerCompany.mainContact, "Kontakt (Haupt)")
    _addItem(powerCompany, project.powerCompany.tagContact, "Kontakt (TAG's)")
    expand += [site, municipality, powerCompany]

    # a project always has an order
    project.currentOrder
    for order in project.orders:
        item = _addItem(top, order)
        expand.append(item)
        _addItem(item, ProgressView(project, order))
        _addItem(item, PlantView(project, order))
        for step in order.steps:
            _addItem(item, step)
        for invoice in order.invoices:
            _addItem(item, invoice)

    for key, text, help in SECTIONS:
        section = _addItem(top, Section(project, key, text, help))
        if key == "buildings":
            for building in project.buildings:
                buildingItem = _addItem(section, building)
                for roof in building.roofs:
                    roofItem = _addItem(buildingItem, roof)
                    for part in roof.moduleGroups + roof.obstacles:
                        _addItem(roofItem, part)
        elif key == "devices":
            _addDevices(section, project, None)
        else:
            for part in project.collection(key):
                _addItem(section, part)
        section.setText(0, text + " (" + str(len(project.collection(key))) + ")")

    tree.addTopLevelItems([top])
    for item in expand:
        item.setExpanded(True)


# the devices built into parent (None: the ones built into nothing)
def _addDevices(parentItem, project, parent):
    ids = {d.id for d in project.devices}
    for device in project.devices:
        inside = device.parentId if device.parentId in ids else None
        if inside == (parent.id if parent else None) and device is not parent:
            item = _addItem(parentItem, device)
            _addDevices(item, project, device)


def _addItem(parent, obj, name=None):
    item = QTreeWidgetItem(None, [name or caption(obj)])
    item.pvpObj = obj
    item.pvpCaption = name
    parent.addChild(item)
    return item


# the caption a tree item should have now
def itemCaption(item):
    if getattr(item, "pvpCaption", None) or isinstance(item.pvpObj, Section):
        return item.text(0)
    return caption(item.pvpObj)


def allItems(item):
    yield item
    for i in range(item.childCount()):
        yield from allItems(item.child(i))


# The item showing an object. Views (Fortschritt, Anlage) are made anew with
# every tree, they are the same if they show the same order.
def findItem(tree, obj):
    if tree.topLevelItemCount() == 0:
        return None
    for item in allItems(tree.topLevelItem(0)):
        other = item.pvpObj
        if other is obj:
            return item
        if type(other) is type(obj):
            if isinstance(obj, Section) and other.key == obj.key:
                return item
            if isinstance(obj, (PlantView, ProgressView)) and other._order is obj._order:
                return item
            if isinstance(obj, SiteView):
                return item
    return None


# the order a tree item belongs to, None if it is not below an order
def orderOf(item):
    while item is not None:
        if isinstance(item.pvpObj, Order):
            return item.pvpObj
        item = item.parent()
    return None


# ---- deleting ---------------------------------------------------------------

def _ids(node, found):
    if isinstance(node, ModelNode):
        if node.__dict__.get("id"):
            found.add(node.id)
        for child in node.children():
            _ids(child, found)


def _uses(value, ids):
    if isinstance(value, str):
        return value in ids
    if isinstance(value, dict):
        return any(_uses(v, ids) for v in value.values())
    if isinstance(value, list):
        return any(_uses(v, ids) for v in value)
    return False


# captions of the parts outside of obj which refer to it or to a part of it
def usedBy(project, obj):
    ids = set()
    _ids(obj, ids)
    inside = set()

    def collect(node):
        inside.add(id(node))
        for child in node.children():
            collect(child)
    collect(obj)

    found = []

    def walk(node):
        if id(node) in inside:
            return
        fields = dict(node.__dict__.get("_unknown") or {})
        fields.update({k: v for k, v in node.__dict__.items() if node._isSaved(k) and k != "id"})
        if any(_uses(v, ids) for v in fields.values() if not isinstance(v, ModelNode)
               and not (isinstance(v, list) and v and isinstance(v[0], ModelNode))):
            found.append(caption(node))
        for child in node.children():
            walk(child)
    walk(project)
    return found


def _delete(project, owner, obj):
    def func():
        users = usedBy(project, obj)
        if users:
            raise ValueError("Wird noch verwendet von:\n" + "\n".join(users[:10]))
        if isinstance(owner, ContactList):
            owner.removeContact(obj)
        else:
            owner.removePart(obj)
        return owner if not isinstance(owner, (PvProject, ContactList)) else None
    return Action("Löschen", func, confirm="'" + caption(obj) + "' wirklich löschen?")


# ---- context menus ----------------------------------------------------------

def _add(text, owner, key, **values):
    return Action(text, lambda: owner.addPart(key, **values))


def _addKinds(text, owner, key, kinds, field="kind", **values):
    if not isinstance(kinds, dict):
        kinds = {kind: kind for kind in kinds}
    return Action(text, entries=[_add(name, owner, key, **dict(values, **{field: kind}))
                                 for kind, name in kinds.items()])


# The actions of a tree item
def contextMenu(item):
    obj = item.pvpObj
    project = obj if isinstance(obj, PvProject) else getattr(obj, "_top", None)
    parent = item.parent().pvpObj if item.parent() else None

    if isinstance(obj, PvProject):
        def checkProject():
            found = check(obj)
            raise Message("\n".join(found) if found else "Nichts gefunden: Verweise und Verbindungen sind in Ordnung.")
        return [Action("Neuer Auftrag", entries=[
                    Action(name, lambda t=orderType: obj.addOrder(t)) for orderType, name in ORDER_TYPES.items()]),
                Action("Projekt prüfen", checkProject)]

    if isinstance(obj, ContactList):
        return [Action("Kontakt hinzufügen", entries=[
            Action(name, lambda r=role: obj.addContact(r)) for role, name in ROLE_NAMES.items()])]

    # only contacts of the contact list, not the ones of the snapshots
    if isinstance(obj, Contact):
        return [_delete(project, parent, obj)] if isinstance(parent, ContactList) else []

    if isinstance(obj, Order):
        missing = {kind: name for kind, name in stepKinds().items() if obj.getStep(kind) is None}
        actions = [
            _addKinds("Schritt hinzufügen", obj, "steps", missing),
            _addKinds("Rechnung hinzufügen", obj, "invoices", INVOICE_KINDS),
            _add("Offerte hinzufügen", project, "quotes", orderId=obj.id, state="draft"),
            _addKinds("Gerät hinzufügen", project, "devices",
                      {kind: DEVICE_KINDS[kind] for kind in ORDER_DEVICE_KINDS}, orderId=obj.id),
        ]
        if len(project.orders) > 1:
            actions.append(_delete(project, project, obj))
        return actions

    if isinstance(obj, (Step, Invoice)):
        return [_delete(project, parent, obj)]

    if isinstance(obj, Section):
        key = obj.key
        if key == "quotes":
            return [_add("Offerte hinzufügen", project, key, orderId=project.currentOrder.id, state="draft")]
        if key == "designs":
            return [_add("Auslegung hinzufügen", project, key)]
        if key == "buildings":
            return [_add("Gebäude hinzufügen", project, key)]
        if key == "surroundings":
            return [_addKinds("Umgebung hinzufügen", project, key, SURROUNDING_KINDS)]
        if key == "devices":
            return [_addKinds("Gerät hinzufügen", project, key, DEVICE_KINDS)]
        if key == "types":
            return [_addKinds("Typ hinzufügen", project, key, TYPE_KINDS, source={"db": "manual"})]
        if key == "strings":
            return [_add("String hinzufügen", project, key)]
        if key == "connections":
            return [_addKinds("Verbindung hinzufügen", project, key, CONNECTION_KINDS)]
        return []

    if isinstance(obj, Building):
        return [_add("Dach hinzufügen", obj, "roofs"), _delete(project, project, obj)]

    if isinstance(obj, Roof):
        return [_add("Modulgruppe hinzufügen", obj, "moduleGroups"),
                _addKinds("Hindernis hinzufügen", obj, "obstacles", OBSTACLE_KINDS),
                _delete(project, parent, obj)]

    if isinstance(obj, (ModuleGroup, Obstacle)):
        return [_delete(project, parent, obj)]

    if isinstance(obj, Device):
        def replacement():
            new = project.addPart("devices", kind=obj.kind, typeId=obj.typeId, label=obj.label,
                                  location=obj.location, parentId=obj.parentId, replacesId=obj.id,
                                  orderId=project.currentOrder.id)
            return new
        return [_addKinds("Eingebautes Gerät hinzufügen", project, "devices", DEVICE_KINDS, parentId=obj.id),
                Action("Ersatzgerät hinzufügen", replacement),
                _delete(project, project, obj)]

    if isinstance(obj, (Quote, Design, Surrounding, DeviceType, String, Connection)):
        return [_delete(project, project, obj)]

    return []
