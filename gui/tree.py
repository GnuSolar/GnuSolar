#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The tree of the project window: captions, building the tree from the model,
# and the context menus (add / delete contact).
#
# Every tree item has the model object it shows in item.pvpObj.

from PyQt5.QtWidgets import QTreeWidgetItem

from model.PvProject import PvProject
from model.Contacts import Contacts
from model.Contact import Contact
from model.Building import Building
from model.Municipality import Municipality
from model.PowerCompany import PowerCompany
from model.Progress import Progress
from model.Plant import Plant

CAPTIONS = {
    PvProject: "PV Projekt",
    Contacts: "Kontakte",
    Building: "Gebäude",
    Municipality: "Gemeinde",
    PowerCompany: "Stromversorger",
    Progress: "Fortschritt",
    Plant: "Anlage",
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
    _addItems(project, top)
    tree.addTopLevelItems([top])
    tree.expandAll()


def _addItem(parent, obj, name):
    item = QTreeWidgetItem(None, [caption(obj) or str(name)])
    item.pvpObj = obj
    parent.addChild(item)
    _addItems(obj, item)
    return item


# Iterate through the model and add an item for every part
def _addItems(modelObj, parent):
    for key, value in modelObj.__dict__.items():
        if key == "config" or key[0] == "_":
            continue

        # Loop over all dictionary element
        if isinstance(value, dict):
            for k, v in value.items():
                if hasattr(v, "__dict__") and isinstance(v.__dict__, dict):
                    _addItem(parent, v, k)

        # recurse into child objects
        if hasattr(value, "__dict__") and isinstance(value.__dict__, dict):
            _addItem(parent, value, key)


# context menu of a tree item: actionKey => text, empty if none
def contextMenu(item):
    obj = item.pvpObj
    if isinstance(obj, Contacts):
        return {"contact_add": "Kontakt hinzufügen"}
    # only contacts of the contact list, and not the mandatory ones
    parent = item.parent().pvpObj if item.parent() else None
    if isinstance(obj, Contact) and isinstance(parent, Contacts) and parent.canRemove(obj):
        return {"contact_delete": "Kontakt löschen"}
    return {}


# run a context menu action on a tree item
def treeAction(actionKey, item):
    obj = item.pvpObj
    if actionKey == "contact_add":
        contact = obj.addContact("test")
        if contact is not None:
            child = QTreeWidgetItem(None, [caption(contact)])
            child.pvpObj = contact
            item.addChild(child)
    elif actionKey == "contact_delete":
        item.parent().pvpObj.removeContact(obj)
        item.parent().removeChild(item)
