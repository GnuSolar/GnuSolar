#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The fields of the pages of the site window. gui/forms.py builds the
# detail page of every part of the site from the lists here.
#
#   fieldsOf(obj)  ->  [(title of the group, [Field, ...]), ...]
#
# A Field shows the value at a path below the object ("cable.length",
# "ends.0.port"). Its type decides the input: text, number, int, date, bool,
# list (comma separated), points, json, multiline, readonly. A field with
# choices is a drop down; ref names the list of the site it points into.
#
# The page Standort shows the view of model/compat.py with the names of file
# version 2, which take and give text.

import plugins
from model import Building, Device, Project, Site
from model.PvSite import PvSite
from model.Contact import Contact, ROLES
from model.compat import SiteView


class Field:
    def __init__(self, path, caption, type="text", choices=None, ref=None, unit=None, hint=None):
        self.path = path
        self.caption = caption + (" [" + unit + "]" if unit else "")
        self.type = type
        self.choices = choices      # list of values, or dict value => caption
        self.ref = ref              # name of a list of the site
        self.hint = hint            # shown in the empty input


F = Field

# field of a device kind or of the specs of a type => (caption, unit)
NAMES = {
    "moduleGroupIds": ("Modulgruppen (IDs)", None),
    "backup": ("Notstrom", None),
    "backupNeutralBond": ("N-PE-Verbindung im Inselbetrieb", None),
    "coupling": ("Kopplung", None),
    "connectedToId": ("verbunden mit", None),
    "loadManagement": ("Lastmanagement", None),
    "owner": ("Eigentümer", None),
    "number": ("Zählernummer", None),
    "role": ("misst", None),
    "measuring": ("Messung", None),
    "ct.primary": ("Stromwandler primär", "A"),
    "ct.secondary": ("Stromwandler sekundär", "A"),
    "measures.connectionId": ("Wandler sitzen auf", None),
    "measures.arrowTowardsId": ("Pfeil zeigt zu", None),
    "ratedCurrent": ("Nennstrom", "A"),
    "characteristic": ("Charakteristik", None),
    "form": ("Bauform", None),
    "poles": ("Pole", None),
    "ratedVoltage": ("Nennspannung", "V"),
    "breakingCapacity": ("Ausschaltvermögen", "A"),
    "switchesNeutral": ("schaltet den Neutralleiter", None),
    "residualCurrent": ("Bemessungsfehlerstrom", "A"),
    "rcdType": ("FI-Typ", None),
    "selective": ("selektiv", None),
    "function": ("Funktion", None),
    "spdType": ("SPD-Typ", None),
    "side": ("Seite", None),
    "conductors": ("Leiter (L1, L2, L3, N, PE)", None),
    "power": ("Leistung", "W"),
    "powerAc": ("AC-Leistung", "W"),
    "phases": ("Phasen", None),
    "voc": ("Leerlaufspannung Voc", "V"),
    "isc": ("Kurzschlussstrom Isc", "A"),
    "vmp": ("MPP-Spannung", "V"),
    "imp": ("MPP-Strom", "A"),
    "tempCoeffVoc": ("Temperaturkoeffizient Voc", "%/°C"),
    "tempCoeffPower": ("Temperaturkoeffizient Leistung", "%/°C"),
    "efficiency": ("Wirkungsgrad", "%"),
    "width": ("Breite", "mm"),
    "height": ("Höhe", "mm"),
    "depth": ("Tiefe", "mm"),
    "weight": ("Gewicht", "kg"),
    "cells": ("Zellen", None),
    "bifacial": ("bifazial", None),
    "connector": ("Stecker", None),
    "cableLength": ("Kabellänge", "mm"),
    "apparentPower": ("Scheinleistung", "VA"),
    "mpptCount": ("Anzahl MPPT", None),
    "inputsPerMppt": ("Eingänge pro MPPT", None),
    "maxDcVoltage": ("max. DC-Spannung", "V"),
    "mpptVoltageMin": ("MPP-Spannung min.", "V"),
    "mpptVoltageMax": ("MPP-Spannung max.", "V"),
    "maxInputCurrent": ("max. Eingangsstrom", "A"),
    "hybrid": ("Hybrid", None),
    "capacity": ("Kapazität", "Wh"),
    "powerCharge": ("Ladeleistung", "W"),
    "powerDischarge": ("Entladeleistung", "W"),
    "voltage": ("Spannung", "V"),
    "chemistry": ("Chemie", None),
    "powerDc": ("DC-Leistung", "W"),
    "maxInputVoltage": ("max. Eingangsspannung", "V"),
    "maxOutputCurrent": ("max. Ausgangsstrom", "A"),
    "canDischarge": ("kann entladen (V2H)", None),
    "powerElectric": ("elektrische Leistung", "W"),
    "powerThermal": ("thermische Leistung", "W"),
    "cop": ("COP", None),
    "moduleGap": ("Modulabstand", "mm"),
    "endClampEdge": ("Rand der Endklemme", "mm"),
    "maxRailLength": ("max. Schienenlänge", "mm"),
    "frameHeightMin": ("Rahmenhöhe min.", "mm"),
    "frameHeightMax": ("Rahmenhöhe max.", "mm"),
}


def _named(path, name, fieldType="text", **more):
    caption, unit = NAMES.get(name, (name, None))
    return Field(path, caption, fieldType, unit=unit, **more)

_LIFETIME = [
    F("projectId", "Projekt", ref="projects"),
    F("from", "in Betrieb seit", "date"),
    F("to", "entfernt am", "date"),
]


# all kinds of steps: the common ones and those of the enabled country
# extensions
def stepKinds():
    kinds = dict(Project.STEP_KINDS)
    for plugin in plugins.enabled():
        kinds.update(getattr(plugin, "STEP_KINDS", {}))
    return kinds


def _contact(obj):
    return [
        ("Kontakt", [
            F("organization", "Firma"),
            F("title", "Anrede"),
            F("lastName", "Name"),
            F("firstName", "Vorname"),
            F("address.street", "Strasse"),
            F("address.streetNumber", "Nummer"),
            F("address.zip", "PLZ"),
            F("address.city", "Ort"),
            F("roles", "Rollen", "list", hint=", ".join(ROLES)),
        ]),
        ("Erreichbar", [
            F("email", "E-Mail"),
            F("email2", "E-Mail 2"),
            F("phone", "Telefon"),
            F("phone2", "Telefon 2"),
            F("mobile", "Mobile"),
        ]),
        ("Bankverbindung", [
            F("accountOwner", "Kontoinhaber"),
            F("accountBank", "Bankname"),
            F("accountIban", "IBAN"),
        ]),
    ]


def _siteView(obj):
    return [
        ("Gebäude", [
            F("buildingState", "Status", choices=("new", "existing")),
            F("street", "Strasse"),
            F("streetNumber", "Nummer"),
            F("zip", "PLZ"),
            F("city", "Ort"),
        ]),
        ("Grundstück", [
            F("buildingId", "amtl. Gebäude-Id"),
            F("areZoneName", "Bauzone BFS"),
            F("areZoneCode", "Bauzone Nr"),
            F("plotNumber", "Parzelle"),
            F("swissGridX", "Koordinate LV03 x"),
            F("swissGridY", "Koordinate LV03 y"),
        ]),
        ("Anschluss", [
            F("meterNumberOld", "Zähler bisher"),
            F("meterNumberNew", "Zähler neu"),
            F("mainFuseSize", "HAK Sicherung", unit="A"),
        ]),
    ]


def _municipality(obj):
    return [
        ("Gemeinde", [
            F("name", "Gemeinde"),
            F("code", "Nummer"),
            F("website", "Webseite"),
        ]),
    ]


def _gridOperator(obj):
    return [
        ("Netzbetreiber", [
            F("name", "Netzbetreiber"),
            F("connectionContact.email", "Anschlussgesuch E-Mail"),
        ]),
    ]


def _site(obj):
    return [
        ("Standort", [
            F("label", "Bezeichnung"),
            # the property keeps the notes a text
            F("comment", "Bemerkungen", "multiline"),
            F("latitude", "Breite (WGS84)", "number", unit="°"),
            F("longitude", "Länge (WGS84)", "number", unit="°"),
            F("elevation", "Höhe über Meer", "number", unit="m"),
            F("annualConsumption", "Jahresverbrauch", "number", unit="Wh"),
            F("horizon", "Horizont: Azimut, Höhe; ...", "points"),
        ]),
        ("Netzanschluss", [
            F("supply.phases", "Phasen", "int"),
            F("supply.voltage", "Spannung", "number", unit="V"),
            F("supply.frequency", "Frequenz", "number", unit="Hz"),
            F("supply.earthingSystem", "Netzform", choices=Site.EARTHING_SYSTEMS),
            F("supply.mainFuse", "Hausanschlusssicherung", "number", unit="A"),
        ]),
        ("Auslegungstemperaturen", [
            F("designTemperature.minAmbient", "tiefste Umgebungstemperatur", "number", unit="°C"),
            F("designTemperature.maxCell", "höchste Zelltemperatur", "number", unit="°C"),
        ]),
        ("Erweiterungen", [F("ext", "Daten von Plugins (JSON)", "json")]),
    ]


def _project(obj):
    return [
        ("Projekt", [
            F("type", "Art", choices=Project.PROJECT_TYPES),
            F("title", "Titel"),
            F("state", "Status", "readonly"),
            F("folder", "Unterordner"),
            F("quoteId", "angenommene Offerte", ref="quotes"),
            F("constructionType", "Bauart", choices=Project.CONSTRUCTION_TYPES),
            F("totalCost", "Gesamtkosten", "number"),
            F("notes", "Notizen", "multiline"),
        ]),
        ("Termine", [
            F("inquiry", "Anfrage", "date"),
            F("roofMeasure", "Dach ausmessen geplant", "date"),
            F("roofMeasured", "Dach ausgemessen", "date"),
            F("ordered", "Zusage", "date"),
            F("rejected", "Absage", "date"),
            F("constructionStart", "Baustart", "date"),
            F("constructionSort", "Sortierung Bauplanung", "date"),
            F("constructionFixed", "Baustart fix", "bool"),
            F("commissioned", "Inbetriebnahme", "date"),
            F("completed", "abgeschlossen", "date"),
            F("archived", "archiviert", "date"),
            F("inactive", "inaktiv", "date"),
        ]),
        ("Positionen", [F("items", "Positionen (JSON)", "json")]),
    ]


def _step(obj):
    return [
        ("Schritt", [
            F("kind", "Art", choices=stepKinds()),
            F("state", "Status", "readonly"),
            F("dates.ordered", "bestellt", "date"),
            F("dates.filled", "ausgefüllt", "date"),
            F("dates.signed", "unterschrieben", "date"),
            F("dates.submitted", "eingereicht", "date"),
            F("dates.approved", "bewilligt / erhalten", "date"),
            F("dates.paid", "bezahlt", "date"),
            F("dates.rejected", "abgelehnt", "date"),
            F("notes", "Notizen", "multiline"),
            F("documents", "Dokumente (JSON)", "json"),
        ]),
    ]


def _invoice(obj):
    return [
        ("Rechnung", [
            F("kind", "Art", choices=Project.INVOICE_KINDS),
            F("number", "Nummer"),
            F("date", "Datum", "date"),
            F("amount", "Betrag", "number"),
            F("currency", "Währung"),
            F("paid", "bezahlt am", "date"),
            F("documents", "Dokumente (JSON)", "json"),
        ]),
    ]


def _quote(obj):
    return [
        ("Offerte", [
            F("number", "Nummer"),
            F("date", "Datum", "date"),
            F("state", "Status", choices=Project.QUOTE_STATES),
            F("projectId", "Projekt", ref="projects"),
            F("variant", "Variante"),
            F("designId", "Auslegung", ref="designs"),
            F("validUntil", "gültig bis", "date"),
            F("total", "Total", "number"),
            F("currency", "Währung"),
            F("items", "Positionen (JSON)", "json"),
            F("documents", "Dokumente (JSON)", "json"),
        ]),
    ]


def _design(obj):
    return [
        ("Auslegung", [
            F("label", "Bezeichnung"),
            F("description", "Beschreibung", "multiline"),
            F("expectedYield.annual", "erwarteter Jahresertrag", "number", unit="Wh"),
            F("expectedYield.source", "berechnet mit"),
            F("expectedYield.date", "berechnet am", "date"),
            F("documents", "Dokumente (JSON)", "json"),
        ]),
    ]


def _building(obj):
    return [
        ("Gebäude", [
            F("label", "Bezeichnung"),
            F("x", "x (Ost)", "number", unit="mm"),
            F("y", "y (Nord)", "number", unit="mm"),
            F("z", "z", "number", unit="mm"),
            F("azimuth", "Drehung", "number", unit="°"),
            F("model", "3D-Modell (JSON)", "json"),
        ]),
    ]


def _roof(obj):
    return [
        ("Dach", [
            F("label", "Bezeichnung"),
            F("kind", "Art", choices=Building.ROOF_KINDS),
            F("covering", "Eindeckung", choices=Building.ROOF_COVERINGS),
            F("azimuth", "Ausrichtung (0 = Nord, 180 = Süd)", "number", unit="°"),
            F("inclination", "Neigung", "number", unit="°"),
            F("eaveHeight", "Traufhöhe", "number", unit="mm"),
            F("ridgeHeight", "Firsthöhe", "number", unit="mm"),
        ]),
        ("Lage und Form", [
            F("x", "x", "number", unit="mm"),
            F("y", "y", "number", unit="mm"),
            F("z", "z", "number", unit="mm"),
            F("outline", "Umriss: x, y; ...", "points"),
        ]),
        ("Randabstände", [
            F("margins.eave", "Traufe", "number", unit="mm"),
            F("margins.ridge", "First", "number", unit="mm"),
            F("margins.left", "links", "number", unit="mm"),
            F("margins.right", "rechts", "number", unit="mm"),
        ]),
    ]


def _moduleGroup(obj):
    return [
        ("Modulgruppe", [
            F("typeId", "Modultyp", ref="types:panel"),
            F("count", "Anzahl Module", "int"),
            F("rows", "Reihen", "int"),
            F("columns", "Spalten", "int"),
            F("orientation", "Ausrichtung", choices=Building.ORIENTATIONS),
            F("mounting", "Montage", choices=Building.MOUNTINGS),
            F("mountingSystemTypeId", "Montagesystem", ref="types:mounting_system"),
            F("designId", "Auslegung", ref="designs"),
        ]),
        ("Lage", [
            F("x", "x", "number", unit="mm"),
            F("y", "y", "number", unit="mm"),
            F("gapX", "Abstand x", "number", unit="mm"),
            F("gapY", "Abstand y", "number", unit="mm"),
            F("tilt", "Neigung der Module", "number", unit="°"),
            F("azimuth", "Ausrichtung der Module", "number", unit="°"),
            F("rowPitch", "Reihenabstand", "number", unit="mm"),
            F("panels", "einzelne Module (JSON)", "json"),
        ]),
    ]


def _obstacle(obj):
    return [
        ("Hindernis", [
            F("kind", "Art", choices=Building.OBSTACLE_KINDS),
            F("shape", "Form", choices=Building.OBSTACLE_SHAPES),
            F("x", "x", "number", unit="mm"),
            F("y", "y", "number", unit="mm"),
            F("width", "Breite", "number", unit="mm"),
            F("height", "Höhe", "number", unit="mm"),
            F("radius", "Radius", "number", unit="mm"),
            F("points", "Punkte: x, y; ...", "points"),
        ]),
    ]


def _surrounding(obj):
    return [
        ("Umgebung", [
            F("kind", "Art", choices=Building.SURROUNDING_KINDS),
            F("label", "Bezeichnung"),
            F("x", "x", "number", unit="mm"),
            F("y", "y", "number", unit="mm"),
            F("z", "z", "number", unit="mm"),
            F("height", "Höhe", "number", unit="mm"),
            F("radius", "Radius", "number", unit="mm"),
            F("outline", "Umriss: x, y; ...", "points"),
        ]),
    ]


def _deviceType(obj):
    specs = [_named("specs." + name, name, fieldType) for name, fieldType in Device.SPEC_FIELDS.get(obj.kind, [])]
    specs.append(F("specs.ports", "Anschlüsse (JSON): name, kind, connector", "json"))
    return [
        ("Typ", [
            F("kind", "Art", choices=Device.TYPE_KINDS),
            F("manufacturer", "Hersteller"),
            F("model", "Modell"),
            F("source.db", "Quelle", choices=("manual", "OpenPanelDatabase", "OpenInverterDatabase", "PVSOL", "PVsyst")),
            F("source.url", "URL"),
            F("source.datasheetSha256", "SHA-256 des Datenblatts"),
        ]),
        ("Technische Daten", specs),
    ]


def _device(obj):
    kindFields = []
    for name, fieldType, choices in Device.KIND_FIELDS.get(obj.kind, []):
        if fieldType.startswith("ref:"):
            kindFields.append(_named(name, name, ref=fieldType[4:]))
        else:
            kindFields.append(_named(name, name, fieldType, choices=choices))
    groups = [
        ("Gerät", [
            F("kind", "Art", choices=Device.DEVICE_KINDS),
            F("label", "Bezeichnung"),
            F("typeId", "Typ", ref="types:" + str(obj.kind)),
            F("count", "Anzahl", "int"),
            F("serial", "Seriennummer"),
            F("firmware", "Firmware"),
            F("location", "Ort"),
            F("parentId", "eingebaut in", ref="devices"),
            F("replacesId", "ersetzt", ref="devices"),
        ] + _LIFETIME),
    ]
    if kindFields:
        groups.append((Device.DEVICE_KINDS.get(obj.kind, str(obj.kind)), kindFields))
    groups.append(("Zugang", [
        F("access.local.host", "Host / IP"),
        F("access.local.port", "Port", "int"),
        F("access.local.protocol", "Protokoll",
          choices=("modbus_tcp", "modbus_rtu_gateway", "sunspec", "http", "https", "aurora", "other")),
        F("access.local.unitId", "Modbus Unit ID", "int"),
        F("access.local.modbusSpec", "ModbusSpec"),
        F("access.cloud.portal", "Portal"),
        F("access.cloud.linked", "im Portal verknüpft", "bool"),
    ]))
    groups.append(("Garantien und Erweiterungen", [
        F("warranties", "Garantien (JSON): layer, start, end, condition", "json"),
        F("ext", "Daten von Plugins (JSON)", "json"),
    ]))
    return groups


def _string(obj):
    return [
        ("String", [
            F("label", "Bezeichnung"),
            F("inverterId", "Wechselrichter", ref="devices:inverter"),
            F("mppt", "MPPT", "int"),
            F("input", "Eingang", "int"),
            F("moduleGroupId", "Modulgruppe", ref="moduleGroups"),
            F("modulesInSeries", "Module in Serie", "int"),
            F("parallel", "parallel", "int"),
            F("connector", "Stecker am Wechselrichter"),
        ]),
        ("Kabel", [
            F("cable.crossSection", "Querschnitt", "number", unit="mm²"),
            F("cable.length", "Länge (einfach)", "number", unit="mm"),
            F("cable.material", "Material", choices=("copper", "aluminium")),
        ]),
    ]


def _connection(obj):
    return [
        ("Verbindung", [
            F("kind", "Art", choices=Device.CONNECTION_KINDS),
            F("label", "Bezeichnung"),
            F("conductors", "Leiter (L1, L2, L3, N, PE, PEN, +, -)", "list"),
            F("protocol", "Protokoll (Signal)", choices=Device.PROTOCOLS),
        ]),
        ("Von", [
            F("ends.0.deviceId", "Gerät", ref="devices"),
            F("ends.0.port", "Anschluss"),
            F("ends.0.connector", "Stecker"),
        ]),
        ("Nach", [
            F("ends.1.deviceId", "Gerät", ref="devices"),
            F("ends.1.port", "Anschluss"),
            F("ends.1.connector", "Stecker"),
        ]),
        ("Kabel", [
            F("cable.designation", "Bezeichnung"),
            F("cable.cores", "Adern", "int"),
            F("cable.crossSection", "Querschnitt", "number", unit="mm²"),
            F("cable.outerDiameter", "Aussendurchmesser", "number", unit="mm"),
            F("cable.length", "Länge", "number", unit="mm"),
            F("cable.material", "Material", choices=("copper", "aluminium")),
        ]),
        ("Lebensdauer", list(_LIFETIME)),
    ]


FIELDS = {
    PvSite: _site,
    Contact: _contact,
    SiteView: _siteView,
    Site.Municipality: _municipality,
    Site.GridOperator: _gridOperator,
    Project.Project: _project,
    Project.Step: _step,
    Project.Invoice: _invoice,
    Project.Quote: _quote,
    Project.Design: _design,
    Building.Building: _building,
    Building.Roof: _roof,
    Building.ModuleGroup: _moduleGroup,
    Building.Obstacle: _obstacle,
    Building.Surrounding: _surrounding,
    Device.DeviceType: _deviceType,
    Device.Device: _device,
    Device.String: _string,
    Device.Connection: _connection,
}


# the groups of fields of a part, [] if its page has none (Kontakte, Geräte)
def fieldsOf(obj):
    func = FIELDS.get(type(obj))
    return func(obj) if func else []
