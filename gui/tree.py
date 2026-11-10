#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The tree of the project window: captions, building the tree from the model,
# and the context menus (add / delete contact).
#
# Every tree item has the model object it shows in item.pvpObj.

from PyQt5.QtWidgets import QTreeWidgetItem

from model.PvProject import PvProject
from model.Contact import Contact, ContactList
from model.Site import Municipality, GridOperator
from model.compat import SiteView, PlantView, ProgressView

CAPTIONS = {
    PvProject: "PV Projekt",
    ContactList: "Kontakte",
    SiteView: "Gebäude",
    Municipality: "Gemeinde",
    GridOperator: "Stromversorger",
    ProgressView: "Fortschritt",
    PlantView: "Anlage",
}


# caption of a model object, None if there is none
def caption(obj):
    if isinstance(obj, Contact):
        return "Kontakt (" + obj.getRoleName() + ")"
    return CAPTIONS.get(type(obj))


# fill the tree widget with the project
def buildTree(tree, project):
    tree.setColumnCount(1)
    top = QTreeWidgetItem(None, ["PV-Anlage"])
    top.pvpObj = project

    # owner and electrician are always there
    project.contacts.owner
    project.contacts.installer_ac
    contacts = _addItem(top, project.contacts)
    for contact in project.contacts:
        _addItem(contacts, contact)

    _addItem(top, project.building)
    municipality = _addItem(top, project.municipality)
    _addItem(municipality, project.municipality.mainContact, "Kontakt (Haupt)")
    _addItem(municipality, project.municipality.buildingContact, "Kontakt (Baubehörde)")
    powerCompany = _addItem(top, project.powerCompany)
    _addItem(powerCompany, project.powerCompany.mainContact, "Kontakt (Haupt)")
    _addItem(powerCompany, project.powerCompany.tagContact, "Kontakt (TAG's)")
    _addItem(top, project.progress)
    _addItem(top, project.plant)

    tree.addTopLevelItems([top])
    tree.expandAll()


def _addItem(parent, obj, name=None):
    item = QTreeWidgetItem(None, [name or caption(obj) or str(obj)])
    item.pvpObj = obj
    item.pvpCaption = name
    parent.addChild(item)
    return item


# context menu of a tree item: actionKey => text, empty if none
def contextMenu(item):
    obj = item.pvpObj
    if isinstance(obj, ContactList):
        return {"contact_add": "Kontakt hinzufügen"}
    # only contacts of the contact list
    parent = item.parent().pvpObj if item.parent() else None
    if isinstance(obj, Contact) and isinstance(parent, ContactList) and parent.canRemove(obj):
        return {"contact_delete": "Kontakt löschen"}
    return {}


# run a context menu action on a tree item
def treeAction(actionKey, item):
    obj = item.pvpObj
    if actionKey == "contact_add":
        contact = obj.addContact("contact")
        _addItem(item, contact)
    elif actionKey == "contact_delete":
        item.parent().pvpObj.removeContact(obj)
        item.parent().removeChild(item)
