#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The tree of the site window: building the tree from the model, and the
# actions of its nodes (add a project, a step, a device ..., delete a part).
#
# Every tree item has the model object it shows in item.pvpObj.

from PyQt5.QtWidgets import QTreeWidgetItem

from model.ModelNode import ModelNode
from model.PvSite import PvSite
from model.Contact import Contact, ContactList, ROLE_NAMES
from model.Building import Building, Roof, ModuleGroup, Obstacle, Surrounding, OBSTACLE_KINDS, SURROUNDING_KINDS
from model.Device import DeviceType, Device, String, Connection, DEVICE_KINDS, TYPE_KINDS, CONNECTION_KINDS
from model.Project import Project, Step, Invoice, Quote, Design, PROJECT_TYPES, INVOICE_KINDS
from model.compat import SiteView
from model.checks import check
from gui.captions import caption
from gui.fields import stepKinds

# the devices a project usually brings
PROJECT_DEVICE_KINDS = ("inverter", "battery", "meter", "charger", "heat_pump", "heating_rod", "energy_manager",
                      "optimizer")


# A list of the site shown as a node of the tree
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
    ("types", "Typen", "Die Produkte, die am Standort verwendet werden: Module, Wechselrichter, Batterien, Montagesysteme."),
    ("strings", "Strings", "Wie die Module an die Wechselrichter angeschlossen sind."),
    ("connections", "Verbindungen", "Kabel zwischen den Geräten: Leistung, Schutzleiter und Signal. Geräte und "
                                    "Verbindungen zusammen sind das Schema der Installation."),
)


# raised by an action which only has something to tell
class Message(Exception):
    pass


# One entry of a context menu or button of a page: func does it and returns
# the object to show afterwards. entries makes it a submenu. confirm is a
# question to ask first. refresh=False: func doesn't change the site, or
# shows the change itself (gui/pages.py).
class Action:
    def __init__(self, text, func=None, entries=None, confirm=None, refresh=True):
        self.text = text
        self.func = func
        self.entries = entries
        self.confirm = confirm
        self.refresh = refresh


# ---- building the tree ------------------------------------------------------

# fill the tree widget with the site
def buildTree(tree, site):
    tree.setColumnCount(1)
    top = QTreeWidgetItem(None, [caption(site)])
    top.pvpObj = site
    expand = [top]

    # owner and electrician are always there
    site.contacts.owner
    site.contacts.installer_ac
    contacts = _addItem(top, site.contacts)
    expand.append(contacts)
    for contact in site.contacts:
        _addItem(contacts, contact)

    address = _addItem(top, site.building)
    municipality = _addItem(top, site.municipality)
    _addItem(municipality, site.municipality.mainContact, "Kontakt (Haupt)")
    _addItem(municipality, site.municipality.buildingContact, "Kontakt (Baubehörde)")
    powerCompany = _addItem(top, site.powerCompany)
    _addItem(powerCompany, site.powerCompany.mainContact, "Kontakt (Haupt)")
    _addItem(powerCompany, site.powerCompany.tagContact, "Kontakt (TAG's)")
    expand += [address, municipality, powerCompany]

    # a site always has a project
    site.currentProject
    for project in site.projects:
        item = _addItem(top, project)
        expand.append(item)
        for step in project.steps:
            _addItem(item, step)
        for invoice in project.invoices:
            _addItem(item, invoice)

    for key, text, help in SECTIONS:
        section = _addItem(top, Section(site, key, text, help))
        if key == "buildings":
            for building in site.buildings:
                buildingItem = _addItem(section, building)
                for roof in building.roofs:
                    roofItem = _addItem(buildingItem, roof)
                    for part in roof.moduleGroups + roof.obstacles:
                        _addItem(roofItem, part)
        elif key == "devices":
            _addDevices(section, site, None)
        else:
            for part in site.collection(key):
                _addItem(section, part)
        section.setText(0, text + " (" + str(len(site.collection(key))) + ")")

    tree.addTopLevelItems([top])
    for item in expand:
        item.setExpanded(True)


# the devices built into parent (None: the ones built into nothing)
def _addDevices(parentItem, site, parent):
    ids = {d.id for d in site.devices}
    for device in site.devices:
        inside = device.parentId if device.parentId in ids else None
        if inside == (parent.id if parent else None) and device is not parent:
            item = _addItem(parentItem, device)
            _addDevices(item, site, device)


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


# The item showing an object. The view of the site (Standort) is made anew
# with every tree.
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
            if isinstance(obj, SiteView):
                return item
    return None


# the project a tree item belongs to, None if it is not below a project
def projectOf(item):
    while item is not None:
        if isinstance(item.pvpObj, Project):
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


# captions of the parts outside of obj which refer to it or to a part of it.
# ignore: generators whose list of module groups doesn't count.
def usedBy(site, obj, ignore=()):
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
        if any(node is other for other in ignore):
            fields.pop("moduleGroupIds", None)
        if any(_uses(v, ids) for v in fields.values() if not isinstance(v, ModelNode)
               and not (isinstance(v, list) and v and isinstance(v[0], ModelNode))):
            found.append(caption(node))
        for child in node.children():
            walk(child)
    walk(site)
    return found


def _delete(site, owner, obj):
    def func():
        # a module group leaves the generators it is part of; they are no
        # reason to keep it
        member = []
        if isinstance(obj, ModuleGroup):
            for device in site.devices:
                ids = device.get("moduleGroupIds") or []
                if obj.id in ids:
                    member.append((device, [i for i in ids if i != obj.id]))
        users = usedBy(site, obj, ignore=[device for device, ids in member])
        if users:
            raise ValueError("Wird noch verwendet von:\n" + "\n".join(users[:10]))
        if isinstance(owner, ContactList):
            owner.removeContact(obj)
        else:
            owner.removePart(obj)
        for device, ids in member:
            device.set("moduleGroupIds", ids or None)
        return owner if not isinstance(owner, (PvSite, ContactList)) else None
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
    site = obj if isinstance(obj, PvSite) else getattr(obj, "_top", None)
    parent = item.parent().pvpObj if item.parent() else None

    if isinstance(obj, PvSite):
        def checkSite():
            found = check(obj)
            raise Message("\n".join(found) if found else "Nichts gefunden: Verweise und Verbindungen sind in Ordnung.")
        return [Action("Neues Projekt", entries=[
                    Action(name, lambda t=projectType: obj.addProject(t)) for projectType, name in PROJECT_TYPES.items()]),
                Action("Standort prüfen", checkSite)]

    if isinstance(obj, ContactList):
        return [Action("Kontakt hinzufügen", entries=[
            Action(name, lambda r=role: obj.addContact(r)) for role, name in ROLE_NAMES.items()])]

    # only contacts of the contact list, not the ones of the snapshots
    if isinstance(obj, Contact):
        return [_delete(site, parent, obj)] if isinstance(parent, ContactList) else []

    if isinstance(obj, Project):
        missing = {kind: name for kind, name in stepKinds().items() if obj.getStep(kind) is None}
        actions = [
            _addKinds("Schritt hinzufügen", obj, "steps", missing),
            _addKinds("Rechnung hinzufügen", obj, "invoices", INVOICE_KINDS),
            _add("Offerte hinzufügen", site, "quotes", projectId=obj.id, state="draft"),
            _addKinds("Gerät hinzufügen", site, "devices",
                      {kind: DEVICE_KINDS[kind] for kind in PROJECT_DEVICE_KINDS}, projectId=obj.id),
        ]
        if len(site.projects) > 1:
            actions.append(_delete(site, site, obj))
        return actions

    if isinstance(obj, (Step, Invoice)):
        return [_delete(site, parent, obj)]

    if isinstance(obj, Section):
        key = obj.key
        if key == "quotes":
            return [_add("Offerte hinzufügen", site, key, projectId=site.currentProject.id, state="draft")]
        if key == "designs":
            return [_add("Auslegung hinzufügen", site, key)]
        if key == "buildings":
            return [_add("Gebäude hinzufügen", site, key)]
        if key == "surroundings":
            return [_addKinds("Umgebung hinzufügen", site, key, SURROUNDING_KINDS)]
        if key == "devices":
            return [_addKinds("Gerät hinzufügen", site, key, DEVICE_KINDS)]
        if key == "types":
            return [_addKinds("Typ hinzufügen", site, key, TYPE_KINDS, source={"db": "manual"})]
        if key == "strings":
            return [_add("String hinzufügen", site, key)]
        if key == "connections":
            return [_addKinds("Verbindung hinzufügen", site, key, CONNECTION_KINDS)]
        return []

    if isinstance(obj, Building):
        return [_add("Dach hinzufügen", obj, "roofs"), _delete(site, site, obj)]

    if isinstance(obj, Roof):
        # a new module group is part of the generator of the project at hand
        def addGroup():
            group = obj.addPart("moduleGroups")
            site.addToGenerator(group)
            return group
        return [Action("Modulgruppe hinzufügen", addGroup),
                _addKinds("Hindernis hinzufügen", obj, "obstacles", OBSTACLE_KINDS),
                _delete(site, parent, obj)]

    if isinstance(obj, (ModuleGroup, Obstacle)):
        return [_delete(site, parent, obj)]

    if isinstance(obj, Device):
        def replacement():
            new = site.addPart("devices", kind=obj.kind, typeId=obj.typeId, label=obj.label,
                                  location=obj.location, parentId=obj.parentId, replacesId=obj.id,
                                  projectId=site.currentProject.id)
            return new
        return [_addKinds("Eingebautes Gerät hinzufügen", site, "devices", DEVICE_KINDS, parentId=obj.id),
                Action("Ersatzgerät hinzufügen", replacement),
                _delete(site, site, obj)]

    if isinstance(obj, (Quote, Design, Surrounding, DeviceType, String, Connection)):
        return [_delete(site, site, obj)]

    return []
