#!/usr/bin/python
# -*- coding: utf-8 -*-

# Types, devices, strings and connections (doc/file_format.md, sections 7
# to 10): what is installed, since when, and how it is wired.
#
# A device has the common fields below as attributes. The fields of its kind
# (KIND_FIELDS: the rating of a fuse, the role of a meter) are read and
# written with get() and set().

from model.ModelNode import ModelNode

# kind => caption
DEVICE_KINDS = {
    "pv_array": "Modulfeld",
    "inverter": "Wechselrichter",
    "battery": "Batterie",
    "meter": "Zähler",
    "charger": "Ladestation",
    "heat_pump": "Wärmepumpe",
    "heating_rod": "Heizstab",
    "energy_manager": "Energiemanager",
    "optimizer": "Optimierer",
    "grid_connection": "Netzanschluss",
    "distribution_board": "Verteilung",
    "fuse": "Sicherung",
    "breaker": "Leitungsschutzschalter",
    "rcd": "Fehlerstromschutzschalter",
    "rcbo": "FI/LS",
    "switch": "Schalter",
    "transfer_switch": "Netzumschalter",
    "spd": "Überspannungsschutz",
    "busbar": "Schiene",
    "earth_electrode": "Erder",
    "load": "Verbraucher",
    "generator": "Generator",
    "boiler": "Boiler",
    "hvac": "Klima",
    "ventilation": "Lüftung",
    "pool": "Pool",
    "ups": "USV",
    "io": "I/O",
    "other": "Anderes",
}

# kinds of types which are not devices
TYPE_KINDS = dict(DEVICE_KINDS, panel="Modul", mounting_system="Montagesystem", part="Teil")
del TYPE_KINDS["pv_array"]

BACKUP = ("none", "socket", "partial", "whole_house")

# kind => fields besides the common ones: (name, type, choices)
KIND_FIELDS = {
    "pv_array": [("moduleGroupIds", "list", None)],
    "inverter": [("backup", "text", BACKUP), ("backupNeutralBond", "text", ("relay", "external", "none"))],
    "battery": [("coupling", "text", ("ac", "dc_generator", "dc_link")), ("connectedToId", "ref:devices", None),
                ("backup", "text", BACKUP)],
    "optimizer": [("moduleGroupIds", "list", None)],
    "charger": [("connectedToId", "ref:devices", None), ("loadManagement", "bool", None)],
    "heat_pump": [("connectedToId", "ref:devices", None)],
    "heating_rod": [("connectedToId", "ref:devices", None)],
    "meter": [("owner", "text", ("grid_operator", "system")), ("number", "text", None),
              ("role", "text", ("grid", "production", "consumption", "sub")),
              ("measuring", "text", ("direct", "ct")), ("ct.primary", "number", None),
              ("ct.secondary", "number", None), ("measures.connectionId", "ref:connections", None),
              ("measures.arrowTowardsId", "ref:devices", None)],
    "fuse": [("ratedCurrent", "number", None), ("characteristic", "text", None), ("form", "text", None),
             ("poles", "int", None), ("ratedVoltage", "number", None), ("breakingCapacity", "number", None)],
    "breaker": [("ratedCurrent", "number", None), ("characteristic", "text", ("B", "C", "D", "K", "Z")),
                ("poles", "int", None), ("switchesNeutral", "bool", None), ("breakingCapacity", "number", None),
                ("form", "text", ("din_rail", "moulded_case"))],
    "rcd": [("ratedCurrent", "number", None), ("residualCurrent", "number", None),
            ("rcdType", "text", ("AC", "A", "F", "B")), ("selective", "bool", None), ("poles", "int", None)],
    "rcbo": [("ratedCurrent", "number", None), ("characteristic", "text", ("B", "C", "D", "K", "Z")),
             ("residualCurrent", "number", None), ("rcdType", "text", ("AC", "A", "F", "B")),
             ("selective", "bool", None), ("poles", "int", None), ("switchesNeutral", "bool", None),
             ("breakingCapacity", "number", None)],
    "switch": [("function", "text", ("isolator", "dc_isolator", "changeover", "bypass")),
               ("ratedCurrent", "number", None), ("poles", "int", None), ("switchesNeutral", "bool", None)],
    "transfer_switch": [("ratedCurrent", "number", None), ("poles", "int", None), ("switchesNeutral", "bool", None)],
    "spd": [("spdType", "text", ("1", "2", "1+2", "3")), ("side", "text", ("ac", "dc"))],
    "busbar": [("conductors", "list", None)],
    "load": [("power", "number", None), ("backup", "bool", None)],
    "generator": [("powerAc", "number", None), ("phases", "int", None)],
}

# kind of a type => common fields of its specs: (name, type)
SPEC_FIELDS = {
    "panel": [("power", "number"), ("voc", "number"), ("isc", "number"), ("vmp", "number"), ("imp", "number"),
              ("tempCoeffVoc", "number"), ("tempCoeffPower", "number"), ("efficiency", "number"),
              ("width", "number"), ("height", "number"), ("depth", "number"), ("weight", "number"),
              ("cells", "int"), ("bifacial", "bool"), ("connector", "text"), ("cableLength", "number")],
    "inverter": [("powerAc", "number"), ("apparentPower", "number"), ("phases", "int"), ("mpptCount", "int"),
                 ("inputsPerMppt", "int"), ("maxDcVoltage", "number"), ("mpptVoltageMin", "number"),
                 ("mpptVoltageMax", "number"), ("maxInputCurrent", "number"), ("hybrid", "bool")],
    "battery": [("capacity", "number"), ("powerCharge", "number"), ("powerDischarge", "number"),
                ("voltage", "number"), ("chemistry", "text")],
    "optimizer": [("powerDc", "number"), ("maxInputVoltage", "number"), ("maxInputCurrent", "number"),
                  ("maxOutputCurrent", "number")],
    "charger": [("powerAc", "number"), ("phases", "int"), ("canDischarge", "bool")],
    "heat_pump": [("powerElectric", "number"), ("powerThermal", "number"), ("cop", "number")],
    "mounting_system": [("moduleGap", "number"), ("endClampEdge", "number"), ("maxRailLength", "number"),
                        ("frameHeightMin", "number"), ("frameHeightMax", "number")],
}

# kind => names of the ports of simple devices
FIXED_PORTS = {
    "fuse": ("in", "out"),
    "breaker": ("in", "out"),
    "rcd": ("in", "out"),
    "rcbo": ("in", "out"),
    "switch": ("in", "out"),
    "transfer_switch": ("common", "a", "b"),
    "busbar": ("bar",),
    "grid_connection": ("out",),
    "load": ("in",),
    "earth_electrode": ("pe",),
    "spd": ("line", "pe"),
}

CONNECTION_KINDS = ("ac", "dc", "pe", "bond", "signal")
PROTOCOLS = ("rs485", "can", "ethernet", "ct", "digital", "analog", "other")
CONDUCTORS = ("L1", "L2", "L3", "N", "PE", "PEN", "+", "-")
WARRANTY_LAYERS = ("legal", "manufacturer", "online_extension", "purchased_extension", "performance")


# A product: a module, an inverter, a battery model, a mounting system
class DeviceType(ModelNode):

    _types = {"source": "json", "specs": "json", "ext": "json"}

    def __init__(self, top=None):
        self._top = top
        self.id = None
        self.kind = None            # see TYPE_KINDS
        self.manufacturer = None
        self.model = None
        self.source = {}            # {"db": "manual", ...}: where the type came from
        self.specs = {}             # the specifications, see SPEC_FIELDS
        self.ext = {}

    # "manufacturer model"
    def getName(self):
        return " ".join(part for part in (self.manufacturer, self.model) if part)

    # the ports of the type: [{"name": "PV1", "kind": "dc", "connector": "MC4"}, ...]
    def getPorts(self):
        return self.specs.get("ports") or []


# One installed thing: an inverter, a battery, a fuse
class Device(ModelNode):

    _types = {"count": "int", "from": "date", "to": "date", "access": "json", "warranties": "json", "ext": "json"}

    def __init__(self, top=None):
        self._top = top
        self.id = None
        self.kind = None            # see DEVICE_KINDS
        self.typeId = None
        self.label = None           # the name on the board and in the diagram: "WR 1", "F1"
        self.count = None
        self.serial = None
        self.firmware = None
        self.location = None

        # lifetime
        self.projectId = None                 # the project that installed it
        self.__dict__["from"] = None        # date it went into operation
        self.to = None                      # date it was removed
        self.replacesId = None
        self.parentId = None                # the device it is built into

        self.access = {}            # {"local": {...}, "cloud": {...}}, never login data
        self.warranties = []
        self.ext = {}

    def getType(self):
        return self._top.byId("types", self.typeId) if self._top else None

    # a value of the specifications of the type, None if not known
    def getSpec(self, name):
        deviceType = self.getType()
        return deviceType.specs.get(name) if deviceType else None

    def getManufacturer(self):
        deviceType = self.getType()
        return (deviceType.manufacturer or "") if deviceType else ""

    def getModel(self):
        deviceType = self.getType()
        return (deviceType.model or "") if deviceType else ""

    # installed on a date (timestamp): in operation and not removed
    def isInstalled(self, day):
        since = self.get("from")
        if since is None or since > day:
            return False
        return self.to is None or self.to > day

    # names of the ports: of the type, or the fixed ones of the kind
    def getPortNames(self):
        deviceType = self.getType()
        names = [p.get("name") for p in deviceType.getPorts() if p.get("name")] if deviceType else []
        if names:
            return names
        if self.kind == "switch" and self.get("function") in ("changeover", "bypass"):
            return ["common", "a", "b"]
        if self.kind == "meter":
            return ["in", "out"] if self.get("measuring") != "ct" else []
        return list(FIXED_PORTS.get(self.kind, ()))

    # the connector of a port, None if the type doesn't say
    def getConnector(self, port):
        deviceType = self.getType()
        for p in (deviceType.getPorts() if deviceType else []):
            if p.get("name") == port:
                return p.get("connector")
        return None

    def getCaption(self):
        name = DEVICE_KINDS.get(self.kind, str(self.kind))
        deviceType = self.getType()
        detail = self.label or (deviceType.getName() if deviceType else "") or self.get("number") or ""
        return name + (": " + str(detail) if detail else "")


# How modules are wired to an inverter
class String(ModelNode):

    _types = {"mppt": "int", "input": "int", "modulesInSeries": "int", "parallel": "int", "cable": "json",
              "ext": "json"}

    def __init__(self, top=None):
        self._top = top
        self.id = None
        self.inverterId = None
        self.mppt = None                # counts from 1
        self.input = None
        self.moduleGroupId = None
        self.modulesInSeries = None
        self.parallel = None
        self.label = None
        self.cable = {}                 # {"crossSection": mm2, "length": mm, "material": ...}
        self.connector = None           # the plug at the inverter
        self.ext = {}


# One cable, or one set of wires, between two ports
class Connection(ModelNode):

    _types = {"ends": "json", "conductors": "list", "cable": "json", "from": "date", "to": "date", "ext": "json"}

    def __init__(self, top=None):
        self._top = top
        self.id = None
        self.kind = None                # see CONNECTION_KINDS
        self.ends = []                  # [{"deviceId": ..., "port": ..., "connector": ...}, {...}]
        self.conductors = []            # see CONDUCTORS
        self.cable = {}
        self.protocol = None            # for signal, see PROTOCOLS
        self.label = None
        self.projectId = None
        self.__dict__["from"] = None
        self.to = None
        self.ext = {}

    def getCaption(self):
        names = []
        for end in self.ends:
            device = self._top.byId("devices", end.get("deviceId")) if self._top else None
            name = (device.label or device.getCaption()) if device else "?"
            names.append(name + ("." + end["port"] if end.get("port") else ""))
        text = " – ".join(names)
        return " ".join(part for part in (self.label, self.kind, text) if part)
