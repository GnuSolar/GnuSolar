#!/usr/bin/python
# -*- coding: utf-8 -*-

# Checks of a project: references that point nowhere, and the electrical
# installation (doc/file_format.md, section 10): ports that the device
# doesn't have, connectors that don't fit, cables without a second end.
#
#   check(project)  ->  list of texts, empty if nothing was found

from model.ModelNode import ModelNode

# field => list of the project it points into
REFERENCES = {
    "typeId": "types",
    "mountingSystemTypeId": "types",
    "designId": "designs",
    "orderId": "orders",
    "quoteId": "quotes",
    "replacesId": "devices",
    "parentId": "devices",
    "connectedToId": "devices",
    "inverterId": "devices",
    "moduleGroupId": "moduleGroups",
    "moduleGroupIds": "moduleGroups",
}

# terminals take any cable
TERMINALS = ("screw terminal", "spring terminal", "cable lug")


def _name(obj):
    from gui.captions import caption
    return caption(obj)


def _parts(node):
    for child in node.children():
        yield child
        yield from _parts(child)


def check(project):
    found = []

    # every id only once
    seen = {}
    for part in _parts(project):
        partId = part.__dict__.get("id")
        if partId is None:
            continue
        if partId in seen:
            found.append("Gleiche ID bei '%s' und '%s'" % (_name(seen[partId]), _name(part)))
        seen[partId] = part

    # references
    for part in _parts(project):
        for field, collection in REFERENCES.items():
            value = part.get(field)
            for objectId in (value if isinstance(value, list) else [value]):
                if objectId is not None and project.byId(collection, objectId) is None:
                    found.append("%s: %s zeigt auf nichts" % (_name(part), field))

    # devices
    for device in project.devices:
        since, until = device.get("from"), device.to
        if since is not None and until is not None and until < since:
            found.append("%s: entfernt vor der Inbetriebnahme" % _name(device))
        parent = device
        for _ in range(len(project.devices) + 1):
            parent = project.byId("devices", parent.parentId)
            if parent is None:
                break
            if parent is device:
                found.append("%s: ist in sich selbst eingebaut" % _name(device))
                break

    # connections
    for connection in project.connections:
        ends = [end for end in connection.ends if end.get("deviceId")]
        if len(ends) != 2:
            found.append("%s: braucht zwei Enden" % _name(connection))
        connectors = []
        for end in ends:
            device = project.byId("devices", end.get("deviceId"))
            if device is None:
                found.append("%s: ein Ende zeigt auf kein Gerät" % _name(connection))
                continue
            port = end.get("port")
            ports = device.getPortNames()
            if port and ports and port not in ports:
                found.append("%s: %s hat keinen Anschluss '%s' (%s)" % (
                    _name(connection), _name(device), port, ", ".join(ports)))
            connector = end.get("connector") or (device.getConnector(port) if port else None)
            if connector:
                connectors.append(connector)
        # plugs of different makes on one DC cable are a known cause of faults
        plugs = {c for c in connectors if c not in TERMINALS}
        if connection.kind == "dc" and len(plugs) > 1:
            found.append("%s: verschiedene Stecker (%s)" % (_name(connection), ", ".join(sorted(plugs))))

    # meters with current transformers
    for device in project.devices:
        if device.kind != "meter" or device.get("measuring") != "ct":
            continue
        measures = device.get("measures") or {}
        if not measures.get("connectionId"):
            found.append("%s: Stromwandler ohne Kabel (measures)" % _name(device))
        elif project.byId("connections", measures["connectionId"]) is None:
            found.append("%s: die Stromwandler sitzen auf einem Kabel, das es nicht gibt" % _name(device))

    # strings
    for string in project.strings:
        inverter = project.byId("devices", string.inverterId)
        if inverter is not None and inverter.kind != "inverter":
            found.append("%s: %s ist kein Wechselrichter" % (_name(string), _name(inverter)))
        mpptCount = inverter.getSpec("mpptCount") if inverter is not None else None
        if mpptCount and string.mppt and string.mppt > mpptCount:
            found.append("%s: MPPT %d, der Wechselrichter hat %d" % (_name(string), string.mppt, mpptCount))

    return found
