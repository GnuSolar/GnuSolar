#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Captions of the model parts, for the tree and the drop downs.

from model.PvProject import PvProject
from model.Contact import Contact, ContactList
from model.Site import Site, Municipality, GridOperator
from model.Building import Building, Roof, ModuleGroup, Obstacle, Surrounding
from model.Device import DeviceType, Device, String, Connection, TYPE_KINDS
from model.Order import Order, Step, Invoice, Quote, Design, INVOICE_KINDS
from model.compat import SiteView, PlantView, ProgressView
from model import values

CAPTIONS = {
    PvProject: "PV Projekt",
    ContactList: "Kontakte",
    SiteView: "Standort",
    Site: "Netzanschluss und Lage",
    Municipality: "Gemeinde",
    GridOperator: "Stromversorger",
    ProgressView: "Fortschritt",
    PlantView: "Anlage",
}


# caption of a kind of step, also of plugins which are not enabled
def _stepName(kind):
    import plugins
    from model.Order import STEP_KINDS
    if kind in STEP_KINDS:
        return STEP_KINDS[kind]
    plugin = plugins.get(str(kind).split(".")[0])
    return getattr(plugin, "STEP_KINDS", {}).get(kind, kind)


def _join(prefix, *parts):
    detail = " ".join(str(p) for p in parts if p not in (None, ""))
    return prefix + (": " + detail if detail else "")


# caption of a model object
def caption(obj):
    if isinstance(obj, Contact):
        name = " ".join(p for p in (obj.organization, obj.lastName, obj.firstName) if p)
        return "Kontakt (" + obj.getRoleName() + ")" + (" " + name if name else "")
    if isinstance(obj, Order):
        return _join("Auftrag", obj.getCaption())
    if isinstance(obj, Step):
        return _join("Schritt", _stepName(obj.kind), "(" + str(obj.state) + ")")
    if isinstance(obj, Invoice):
        return _join("Rechnung", INVOICE_KINDS.get(obj.kind, obj.kind), obj.number, values.dateToText(obj.date))
    if isinstance(obj, Quote):
        return _join("Offerte", obj.number, values.dateToText(obj.date), obj.variant)
    if isinstance(obj, Design):
        return _join("Auslegung", obj.label)
    if isinstance(obj, Building):
        return _join("Gebäude", obj.label)
    if isinstance(obj, Roof):
        direction = None if obj.azimuth is None else values.numberToText(obj.azimuth) + "°"
        return _join("Dach", obj.label, direction)
    if isinstance(obj, ModuleGroup):
        moduleType = obj.getType()
        count = None if obj.count is None else str(obj.count) + " x"
        return _join("Modulgruppe", count, moduleType.getName() if moduleType else None)
    if isinstance(obj, Obstacle):
        return _join("Hindernis", obj.kind)
    if isinstance(obj, Surrounding):
        return _join("Umgebung", obj.kind, obj.label)
    if isinstance(obj, DeviceType):
        return _join(TYPE_KINDS.get(obj.kind, str(obj.kind)), obj.getName())
    if isinstance(obj, Device):
        return obj.getCaption()
    if isinstance(obj, String):
        return _join("String", obj.label)
    if isinstance(obj, Connection):
        return _join("Verbindung", obj.getCaption())
    if hasattr(obj, "caption"):
        return obj.caption
    return CAPTIONS.get(type(obj)) or str(obj)
