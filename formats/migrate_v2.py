#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Migration of a project of file version 2 to a site of version 3, on the plain data
# (doc/file_format_v3/file_format.md, section 15).
#
#   new = migrate(old, taken=..., files=[...], report=Report())
#
# old is the "project" object of a version 2 file, new the "site" of version 3.
# Nothing is read or written here. Version 2 has one building, one plant and
# one progress; they become the site, a building with one roof, and one project
# of type new_system.
#
# Version 2 values are text as typed. Values that are not what version 3
# expects (a year instead of a date, text instead of a number) are never
# dropped: an unreadable date goes to the notes, anything else to
# ext.gnusolar.v2 of the object it belonged to. The report lists them.

import re
import uuid

from model import values
from model.states import projectState, stepState
import plugins
from plugins import ch

CONSTRUCTION_TYPES = {"builton": "on_roof", "integrated": "in_roof", "facade": "facade"}
ROLES = {"owner": "owner", "installer_ac": "electrician"}

# progress field => field of the project
PROJECT_DATES = {
    "inquiryReceived": "inquiry",
    "roofMeasure": "roofMeasure",
    "roofMeasured": "roofMeasured",
    "orderReceived": "ordered",
    "orderRejected": "rejected",
    "constructionStart": "constructionStart",
    "constructionSort": "constructionSort",
    "launch": "commissioned",
    "archived": "archived",
    "inactiv": "inactive",
}

# progress field => (kind of the step, state of the step)
STEP_DATES = {
    "tagSent": ("ch.tag", "submitted"),
    "tagReceived": ("ch.tag", "approved"),
    "iaSent": ("ch.ia", "submitted"),
    "iaReceived": ("ch.ia", "approved"),
    "bauSent": ("ch.building_permit", "submitted"),
    "bauReceived": ("ch.building_permit", "approved"),
    "materialOrdered": ("material", "ordered"),
    "materialReceived": ("material", "approved"),
    "documentationCreated": ("documentation", "filled"),
    "documentationPlaced": ("documentation", "submitted"),
    "siNaDcOrdered": ("ch.sina_dc", "ordered"),
    "siNaDcReceived": ("ch.sina_dc", "approved"),
    "siNaAcOrdered": ("ch.sina_ac", "ordered"),
    "siNaAcReceived": ("ch.sina_ac", "approved"),
    "eivComplete": ("ch.pronovo", "submitted"),
    "eivPayed": ("ch.pronovo", "paid"),
}
STEP_ORDER = ("ch.tag", "ch.ia", "ch.building_permit", "material", "documentation",
              "ch.sina_dc", "ch.sina_ac", "ch.pronovo")

# progress field => (kind of the invoice, number of that kind, field of the invoice)
INVOICE_DATES = {
    "partialInvoiceSent": ("partial", 0, "date"),
    "partialInvoiceReceived": ("partial", 0, "paid"),
    "partialInvoice2Sent": ("partial", 1, "date"),
    "partialInvoice2Received": ("partial", 1, "paid"),
    "finalInvoiceSent": ("final", 0, "date"),
    "finalInvoiceReceived": ("final", 0, "paid"),
}

QUOTE_DATES = ("quote1Sent", "quote2Sent", "quote3Sent", "quote4Sent")

# fields which version 3 doesn't have on purpose
DROPPED = {
    "": ("state",),
    "municipality": ("fkPowerCompany",),
    "powerCompany": ("fkContactTag",),
}

_DATE_IN_TEXT = re.compile(r"\d{4}-\d{1,2}-\d{1,2}")


# What a migration did with values that didn't fit. Every entry is
# (path of the version 2 field, value).
class Report:
    def __init__(self):
        self.kept = []       # moved to ext.gnusolar.v2
        self.notes = []      # unreadable dates, moved to the notes
        self.dropped = []    # fields version 3 doesn't have on purpose
        self.manual = []     # needs a look: two dates in one field


def _empty(value):
    return value is None or (isinstance(value, str) and not value.strip())


def _text(value):
    if _empty(value):
        return None
    return value.strip() if isinstance(value, str) else str(value)


# remove empty values, lists and dicts
def _clean(node):
    if isinstance(node, dict):
        ret = {}
        for key, value in node.items():
            value = _clean(value)
            if value is None or value == {} or value == []:
                continue
            ret[key] = value
        return ret
    if isinstance(node, list):
        return [_clean(v) for v in node]
    return node


class _Migration:
    def __init__(self, old, taken, files, report, newId):
        self.old = old
        self.taken = taken
        self.files = files or []
        self.report = report or Report()
        self.newId = newId or (lambda: str(uuid.uuid4()))

    # ---- values that don't fit ------------------------------------------

    # keep a version 2 value which has no field in version 3
    def keep(self, obj, path, value):
        if _empty(value):
            return
        ns = obj.setdefault("ext", {}).setdefault("gnusolar", {"v": 1})
        ns.setdefault("v2", {})[path.split(".")[-1]] = value
        self.report.kept.append((path, value))

    def number(self, obj, path, value, integer=False, factor=1):
        if _empty(value):
            return None
        try:
            number = values.textToInt(str(value)) if integer else values.textToNumber(str(value))
        except ValueError:
            self.keep(obj, path, value)
            return None
        if factor != 1:
            number = round(number * factor, 6)
            if number == int(number):
                number = int(number)
        return number

    # Timestamp of a version 2 date. Text that is no date goes to notes (a
    # list of lines); of two dates the first one is taken.
    def date(self, path, value, notes):
        if _empty(value):
            return None
        if not isinstance(value, str):
            value = str(value)
        try:
            return values.textToDate(value)
        except ValueError:
            pass
        name = path.split(".")[-1]
        notes.append(name + ": " + value.strip())
        self.report.notes.append((path, value))
        found = _DATE_IN_TEXT.findall(value)
        if len(found) > 1:
            self.report.manual.append((path, value))
            try:
                return values.textToDate(found[0])
            except ValueError:
                pass
        return None

    def leftovers(self, obj, prefix, old, known):
        dropped = DROPPED.get(prefix, ())
        for key, value in (old or {}).items():
            if key in known or _empty(value):
                continue
            path = (prefix + "." if prefix else "") + key
            if key in dropped:
                self.report.dropped.append((path, value))
            elif isinstance(value, (dict, list)) and not _clean(value):
                continue
            else:
                self.keep(obj, path, value)

    # ---- contacts ---------------------------------------------------------

    CONTACT_FIELDS = ("role", "company", "department", "title", "firstName", "middleName", "lastName",
                      "nickName", "floor", "room", "street", "streetNumber", "address1", "address2", "zip",
                      "city", "country", "email", "email2", "phone", "phone2", "mobile", "accountOwner",
                      "accountBank", "accountIban", "accountIid", "accountBic")

    # A version 3 contact without id and roles, None if it has no values
    def contact(self, old, path):
        old = old or {}
        new = {"organization": _text(old.get("company"))}
        for key in ("department", "title", "firstName", "middleName", "lastName", "nickName"):
            new[key] = _text(old.get(key))
        new["address"] = {key: _text(old.get(key)) for key in
                          ("street", "streetNumber", "address1", "address2", "floor", "room", "zip", "city", "country")}
        new["channels"] = [{"kind": kind, "value": _text(old.get(key))}
                           for key, kind in (("phone", "phone"), ("phone2", "phone"), ("mobile", "mobile"),
                                             ("email", "email"), ("email2", "email"))
                           if not _empty(old.get(key))]
        account = {"owner": _text(old.get("accountOwner")), "bank": _text(old.get("accountBank")),
                   "iban": _text(old.get("accountIban")), "bic": _text(old.get("accountBic"))}
        if not _empty(old.get("accountIid")):
            account["ext"] = {"ch": {"v": ch.DATA_VERSION, "iid": _text(old.get("accountIid"))}}
        new["bankAccounts"] = [account] if _clean(account) else []
        self.leftovers(new, path, old, self.CONTACT_FIELDS)
        new = _clean(new)
        return new or None

    def contacts(self):
        ret = []
        old = (self.old.get("contacts") or {}).get("contacts") or {}
        for role in sorted(old, key=lambda r: (r not in ROLES, list(ROLES).index(r) if r in ROLES else 0, r)):
            contact = self.contact(old[role], "contacts.contacts." + role)
            if not contact:
                continue
            new = {"id": self.newId(), "roles": [ROLES.get(role, "contact")]}
            new.update(contact)
            if role not in ROLES:
                self.keep(new, "contacts.contacts." + role + ".role", role)
            ret.append(new)
        return ret

    # ---- site -------------------------------------------------------------

    def municipality(self, building):
        old = self.old.get("municipality") or {}
        new = {}
        for key in ("id", "name", "countryCode", "stateCode", "districtCode", "website"):
            new[key] = old.get(key) if not isinstance(old.get(key), str) else _text(old.get(key))
        code = _text(old.get("code"))
        buildingCode = _text(building.get("municipalityCode"))
        new["code"] = code or buildingCode
        new["name"] = new["name"] or _text(building.get("municipalityName"))
        new["mainContact"] = self.contact(old.get("mainContact"), "municipality.mainContact")
        new["buildingContact"] = self.contact(old.get("buildingContact"), "municipality.buildingContact")
        if old.get("fkFormBuilding") is not None:
            new["ext"] = {"ch": {"v": ch.DATA_VERSION, "buildingFormId": old["fkFormBuilding"]}}
        if code and buildingCode and code != buildingCode:
            self.keep(new, "building.municipalityCode", buildingCode)
        name = _text(building.get("municipalityName"))
        if name and new["name"] != name:
            self.keep(new, "building.municipalityName", name)
        self.leftovers(new, "municipality", old, ("id", "code", "name", "countryCode", "stateCode", "districtCode",
                                                  "website", "mainContact", "buildingContact", "fkFormBuilding"))
        new = _clean(new)
        if new:
            new["taken"] = self.taken
        return new

    def gridOperator(self):
        old = self.old.get("powerCompany") or {}
        new = {"id": old.get("id"), "name": _text(old.get("name"))}
        new["address"] = {"address1": _text(old.get("address1")), "address2": _text(old.get("address2")),
                          "zip": _text(old.get("zipCode")), "city": _text(old.get("city"))}
        new["mainContact"] = self.contact(old.get("mainContact"), "powerCompany.mainContact")
        new["connectionContact"] = self.contact(old.get("tagContact"), "powerCompany.tagContact")
        ext = {"vseId": old.get("vseId") if not isinstance(old.get("vseId"), str) else _text(old.get("vseId")),
               "tagFormId": old.get("fkFormTag"), "iaFormId": old.get("fkFormIa")}
        if _clean(ext):
            ext["v"] = ch.DATA_VERSION
            new["ext"] = {"ch": ext}
        self.leftovers(new, "powerCompany", old, ("id", "name", "address1", "address2", "zipCode", "city", "vseId",
                                                  "mainContact", "tagContact", "fkFormTag", "fkFormIa"))
        new = _clean(new)
        if new:
            new["taken"] = self.taken
        return new

    # the fields of the place: address, coordinates, grid connection, master data
    def place(self):
        old = self.old.get("building") or {}
        site = {"address": {key: _text(old.get(key)) for key in
                            ("street", "streetNumber", "zip", "city", "region", "country")},
                "plotNumber": _text(old.get("plotNumber"))}
        site["supply"] = {"mainFuse": self.number(site, "building.mainFuseSize", old.get("mainFuseSize"))}

        ext = {}
        if not _empty(old.get("swissGridX")) or not _empty(old.get("swissGridY")):
            lv95 = ch.lv95FromText(old.get("swissGridX"), old.get("swissGridY"))
            if lv95:
                ext["lv95"] = {"e": lv95[0], "n": lv95[1]}
                site["latitude"], site["longitude"] = ch.lv95ToWgs84(*lv95)
            else:
                self.keep(site, "building.swissGridX", old.get("swissGridX"))
                self.keep(site, "building.swissGridY", old.get("swissGridY"))
        egid = self.number(site, "building.buildingId", old.get("buildingId"), integer=True)
        if egid is not None:
            ext["egid"] = [egid]
        zone = _clean({"code": _text(old.get("areZoneCode")), "name": _text(old.get("areZoneName"))})
        if zone:
            ext["zone"] = zone
        self.keep(site, "building.buildingState", old.get("buildingState"))

        site["municipality"] = self.municipality(old)
        site["gridOperator"] = self.gridOperator()
        self.leftovers(site, "building", old, (
            "street", "streetNumber", "zip", "city", "region", "country", "plotNumber", "mainFuseSize",
            "swissGridX", "swissGridY", "buildingId", "areZoneCode", "areZoneName", "buildingState",
            "municipalityCode", "municipalityName", "meterNumberOld", "meterNumberNew"))
        if ext:
            ext["v"] = ch.DATA_VERSION
            site.setdefault("ext", {})["ch"] = ext
        return _clean(site)

    # ---- project ------------------------------------------------------------

    def project(self, new):
        progress = self.old.get("progress") or {}
        plant = self.old.get("plant") or {}
        notes = []
        project = {"id": self.newId(), "type": "new_system", "folder": ""}

        for key, field in PROJECT_DATES.items():
            project[field] = self.date("progress." + key, progress.get(key), notes)
        project["constructionFixed"] = True if progress.get("constructionFixed") else None

        constructionType = _text(plant.get("constructionType"))
        if constructionType in CONSTRUCTION_TYPES:
            project["constructionType"] = CONSTRUCTION_TYPES[constructionType]
        else:
            self.keep(project, "plant.constructionType", constructionType)
        project["totalCost"] = self.number(project, "plant.totalCost", plant.get("totalCost"))

        # steps
        steps = {}
        for key, (kind, state) in STEP_DATES.items():
            step = steps.setdefault(kind, {"dates": {}, "notes": []})
            step["dates"][state] = self.date("progress." + key, progress.get(key), step["notes"])
        project["steps"] = []
        for kind in STEP_ORDER:
            step = _clean(steps[kind])
            if not step:
                continue
            project["steps"].append(_clean({
                "id": self.newId(), "kind": kind, "state": stepState(step.get("dates")),
                "dates": step.get("dates"), "notes": "\n".join(step.get("notes", [])) or None}))

        # invoices
        invoices = {}
        for key, (kind, number, field) in INVOICE_DATES.items():
            invoice = invoices.setdefault((kind, number), {"kind": kind})
            invoice[field] = self.date("progress." + key, progress.get(key), notes)
        project["invoices"] = []
        for invoice in invoices.values():
            if invoice.get("date") or invoice.get("paid"):
                invoice["id"] = self.newId()
                project["invoices"].append(_clean(invoice))
        self.numberDocuments(project["invoices"], "fin", "R", "invoice", "date")

        # quotes
        project["quotes"] = []
        for key in QUOTE_DATES:
            day = self.date("progress." + key, progress.get(key), notes)
            if day:
                project["quotes"].append({"id": self.newId(), "date": day, "state": "sent"})
        self.numberDocuments(project["quotes"], "off", "O", "quote", "date")

        known = set(PROJECT_DATES) | set(STEP_DATES) | set(INVOICE_DATES) | set(QUOTE_DATES) | {"constructionFixed"}
        self.leftovers(project, "progress", progress, known)
        project["notes"] = "\n".join(notes) or None
        project["state"] = projectState(project, quoted=bool(project["quotes"]))
        return project

    # Give quotes or invoices their number from the files O2026-11-0042.pdf /
    # R2026-06-0123.pdf in folder, where the files of a month and the entries
    # of that month are the same count.
    def numberDocuments(self, entries, folder, letter, kind, dateField):
        pattern = re.compile("^" + folder + "/(" + letter + r"(\d{4})-(\d{2})-(\d{4})[^/.]*)\.(\w+)$")
        byMonth = {}
        for path in sorted(self.files):
            m = pattern.match(path.replace("\\", "/"))
            if not m:
                continue
            numbers = byMonth.setdefault((int(m.group(2)), int(m.group(3))), {})
            number = m.group(1)[:13]
            # prefer the pdf, it is what was sent
            if number not in numbers or m.group(5).lower() == "pdf":
                numbers[number] = path.replace("\\", "/")
        entriesByMonth = {}
        for entry in entries:
            if entry.get(dateField):
                day = values.timestampToDay(entry[dateField])
                entriesByMonth.setdefault((day.year, day.month), []).append(entry)
        for month, monthEntries in entriesByMonth.items():
            numbers = byMonth.get(month, {})
            if len(numbers) != len(monthEntries):
                continue
            monthEntries.sort(key=lambda e: e[dateField])
            for entry, number in zip(monthEntries, sorted(numbers)):
                entry["number"] = number
                entry["documents"] = [{"path": numbers[number], "kind": kind}]

    # ---- plant ------------------------------------------------------------

    def plant(self, new, project):
        plant = self.old.get("plant") or {}
        building = self.old.get("building") or {}
        commissioned = project.get("commissioned")

        # modules: a manual type, a roof with one module group, a pv_array
        group = {"id": self.newId()}
        count = self.number(group, "plant.totalPanelCount", plant.get("totalPanelCount"), integer=True)
        power = self.number(group, "plant.totalPowerDc", plant.get("totalPowerDc"), factor=1000)
        area = self.number(group, "plant.totalArea", plant.get("totalArea"))
        panelDesc = _text(plant.get("panelDesc"))
        if count is not None or power is not None or area is not None or panelDesc or group.get("ext"):
            panelType = {"id": self.newId(), "kind": "panel", "model": panelDesc, "source": {"db": "manual"}}
            if power is not None and count:
                panelPower = power / count
                if round(panelPower, 3) * count == power:
                    panelPower = round(panelPower, 3)
                if panelPower == int(panelPower):
                    panelPower = int(panelPower)
                panelType["specs"] = {"power": panelPower}
            elif power is not None:
                # without the number of modules the power of one is not known
                group.setdefault("ext", {}).setdefault("gnusolar", {"v": 1}).setdefault("v2", {})["totalPowerDc"] = power
            if area is not None:
                group.setdefault("ext", {}).setdefault("gnusolar", {"v": 1}).setdefault("v2", {})["totalArea"] = area
            group["count"] = count
            group["typeId"] = panelType["id"]
            group["mounting"] = project.get("constructionType") if project.get("constructionType") != "flat_roof" else None
            new["types"].append(_clean(panelType))
            new["buildings"].append({"id": self.newId(), "roofs": [
                {"id": self.newId(), "moduleGroups": [_clean(group)]}]})
            new["devices"].append(_clean({"id": self.newId(), "kind": "pv_array", "projectId": project["id"],
                                          "moduleGroupIds": [group["id"]], "from": commissioned}))

        # inverter: a manual type and a device
        inverter = {"id": self.newId(), "kind": "inverter", "projectId": project["id"], "from": commissioned}
        powerAc = self.number(inverter, "plant.totalPowerAc", plant.get("totalPowerAc"), factor=1000)
        inverterDesc = _text(plant.get("inverterDesc"))
        if powerAc is not None or inverterDesc or inverter.get("ext"):
            inverterType = {"id": self.newId(), "kind": "inverter", "model": inverterDesc, "source": {"db": "manual"},
                            "specs": {"powerAc": powerAc}}
            inverter["typeId"] = inverterType["id"]
            new["types"].append(_clean(inverterType))
            new["devices"].append(_clean(inverter))

        # the grid operator's meters: the old one was there before the project,
        # the new one came with it
        oldMeter = None
        if not _empty(building.get("meterNumberOld")):
            oldMeter = {"id": self.newId(), "kind": "meter", "owner": "grid_operator", "role": "grid",
                        "number": _text(building["meterNumberOld"])}
            new["devices"].append(oldMeter)
        if not _empty(building.get("meterNumberNew")):
            meter = {"id": self.newId(), "kind": "meter", "owner": "grid_operator", "role": "grid",
                     "number": _text(building["meterNumberNew"]), "projectId": project["id"], "from": commissioned}
            if oldMeter:
                meter["replacesId"] = oldMeter["id"]
                oldMeter["to"] = commissioned
            new["devices"].append(_clean(meter))
        if oldMeter:
            new["devices"][new["devices"].index(oldMeter)] = _clean(oldMeter)

        self.leftovers(project, "plant", plant, ("constructionType", "totalPowerDc", "totalArea", "totalPanelCount",
                                               "panelDesc", "totalPowerAc", "inverterDesc", "totalCost"))

        if power is not None:
            project["title"] = "PV-Anlage " + values.numberToText(round(power / 1000, 2)) + " kWp"
        else:
            project["title"] = "PV-Anlage"

    # ---- site ----------------------------------------------------------

    def run(self):
        new = self.place()
        new.update({
            "id": self.newId(),
            "currency": "CHF",
            "contacts": self.contacts(),
            "buildings": [],
            "surroundings": [],
            "types": [],
            "devices": [],
            "strings": [],
            "connections": [],
            "projects": [],
            "notes": self.old.get("comment") or "",
            "plugins": [],
        })
        new.setdefault("ext", {})
        project = self.project(new)
        self.plant(new, project)
        new["projects"].append(_clean(project))
        self.leftovers(new, "", self.old, ("building", "comment", "contacts", "municipality", "plant",
                                           "powerCompany", "progress", "state"))
        if not _empty(self.old.get("state")):
            self.report.dropped.append(("state", self.old.get("state")))
        for prefix in ("municipality", "powerCompany"):
            for key in DROPPED[prefix]:
                value = (self.old.get(prefix) or {}).get(key)
                if not _empty(value) and (prefix + "." + key, value) not in self.report.dropped:
                    self.report.dropped.append((prefix + "." + key, value))
        new["plugins"] = plugins.pluginList(new)
        return new


# The version 3 site of a version 2 project.
#   taken   date of the master data snapshots (timestamp): the date of the file
#   files   paths of the files in the site folder, relative to it, to find
#           the numbers of quotes and invoices
#   report  a Report, filled with what didn't fit
#   newId   function returning a new id, for tests
def migrate(old, taken=None, files=None, report=None, newId=None):
    return _Migration(old, taken, files, report, newId).run()
