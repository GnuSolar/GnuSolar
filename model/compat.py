#!/usr/bin/python
# -*- coding: utf-8 -*-

# The project as file version 2 saw it: one building, one plant, one progress.
#
# The forms (Ui/Building, Ui/Plant, Ui/Progress), the document templates and
# the form scripts in data/ were written for that model. The views here give
# them the same fields on top of the version 3 model:
#
#   project.building   SiteView       the site, as text fields
#   project.plant      PlantView      modules and inverters of one order, summed up
#   project.progress   ProgressView   the dates of one order, its steps, quotes and invoices
#
# All values of a view are text, as they were in version 2: dates as
# 2015-03-21, power in kW, missing values as "". A setter raises ValueError
# for text that is not a date or a number.

import sqlite3

from model import values
from model.Site import getExt, setExt, getV2, setV2
from formats.migrate_v2 import ORDER_DATES, STEP_DATES, INVOICE_DATES, QUOTE_DATES, CONSTRUCTION_TYPES
from plugins import ch


def _text(value):
    return "" if value is None else str(value)


def _clean(text):
    return (text or "").strip() or None


# ---------------------------------------------------------------------------

class SiteView:

    def __init__(self, project):
        self._top = project

    @property
    def _site(self):
        return self._top.site

    # ---- coordinates, as LV03 like version 2 stored them --------------------

    def _getCoordinate(self, key, offset):
        value = (getExt(self._site, "ch", "lv95") or {}).get(key)
        if value is None:
            return ""
        return values.numberToText(round(value - offset, 3))

    def _setCoordinate(self, key, offset, low, high, text):
        value = values.textToNumber(text)
        if value is not None:
            if value < offset:
                value += offset
            if not low <= value <= high:
                raise ValueError("keine Schweizer Koordinate: " + str(text))
        lv95 = dict(getExt(self._site, "ch", "lv95") or {})
        if value is None:
            lv95.pop(key, None)
        else:
            lv95[key] = round(value, 3)
        setExt(self._site, "ch", "lv95", lv95)
        if "e" in lv95 and "n" in lv95:
            self._site.latitude, self._site.longitude = ch.lv95ToWgs84(lv95["e"], lv95["n"])

    swissGridX = property(lambda self: self._getCoordinate("e", 2000000),
                          lambda self, text: self._setCoordinate("e", 2000000, 2480000, 2840000, text))
    swissGridY = property(lambda self: self._getCoordinate("n", 1000000),
                          lambda self, text: self._setCoordinate("n", 1000000, 1070000, 1300000, text))

    # ---- swiss building id (EGID) -----------------------------------------

    @property
    def buildingId(self):
        egid = getExt(self._site, "ch", "egid") or []
        return _text(egid[0]) if egid else ""

    @buildingId.setter
    def buildingId(self, text):
        value = values.textToInt(text)
        egid = list(getExt(self._site, "ch", "egid") or [])
        if value is None:
            egid = egid[1:]
        elif egid:
            egid[0] = value
        else:
            egid = [value]
        setExt(self._site, "ch", "egid", egid)

    # ---- building zone (ARE) ----------------------------------------------

    def _getZone(self, key):
        return _text((getExt(self._site, "ch", "zone") or {}).get(key))

    def _setZone(self, key, text):
        zone = dict(getExt(self._site, "ch", "zone") or {})
        if _clean(text) is None:
            zone.pop(key, None)
        else:
            zone[key] = _clean(text)
        setExt(self._site, "ch", "zone", zone)

    areZoneCode = property(lambda self: self._getZone("code"), lambda self, text: self._setZone("code", text))
    areZoneName = property(lambda self: self._getZone("name"), lambda self, text: self._setZone("name", text))

    # ---- the grid operator's meters ---------------------------------------

    def _meters(self):
        return [d for d in self._top.devices if d.kind == "meter" and d.get("owner") == "grid_operator"]

    # the meter the current order brought
    def _newMeter(self):
        order = self._top.currentOrder
        for meter in self._meters():
            if meter.orderId == order.id:
                return meter
        return None

    # the meter that was there before the current order
    def _oldMeter(self):
        order = self._top.currentOrder
        new = self._newMeter()
        if new and new.replacesId:
            return self._top.byId("devices", new.replacesId)
        found = [m for m in self._meters() if m.orderId != order.id]
        return found[-1] if found else None

    @property
    def meterNumberOld(self):
        meter = self._oldMeter()
        return _text(meter.get("number")) if meter else ""

    @meterNumberOld.setter
    def meterNumberOld(self, text):
        meter = self._oldMeter()
        new = self._newMeter()
        if _clean(text) is None:
            if meter:
                self._top.removePart(meter)
                if new:
                    new.replacesId = None
            return
        if meter is None:
            meter = self._top.addPart("devices", kind="meter", owner="grid_operator", role="grid")
            # in the list before the meter which replaces it
            if new:
                self._top.devices.remove(meter)
                self._top.devices.insert(self._top.devices.index(new), meter)
                new.replacesId = meter.id
                meter.to = new.get("from")
        meter.set("number", _clean(text))

    @property
    def meterNumberNew(self):
        meter = self._newMeter()
        return _text(meter.get("number")) if meter else ""

    @meterNumberNew.setter
    def meterNumberNew(self, text):
        meter = self._newMeter()
        old = self._oldMeter()
        if _clean(text) is None:
            if meter:
                self._top.removePart(meter)
                if old:
                    old.to = None
            return
        if meter is None:
            order = self._top.currentOrder
            meter = self._top.addPart("devices", kind="meter", owner="grid_operator", role="grid",
                                      orderId=order.id)
            meter.set("from", order.commissioned)
            if old:
                meter.replacesId = old.id
                old.to = order.commissioned
        meter.set("number", _clean(text))

    # ---- other fields -----------------------------------------------------

    @property
    def mainFuseSize(self):
        return values.numberToText(self._site.supply.mainFuse)

    @mainFuseSize.setter
    def mainFuseSize(self, text):
        self._site.supply.mainFuse = values.textToNumber(text)

    @property
    def buildingState(self):
        return _text(getV2(self._site, "buildingState"))

    @buildingState.setter
    def buildingState(self, text):
        setV2(self._site, "buildingState", _clean(text))

    @property
    def plotNumber(self):
        return _text(self._site.plotNumber)

    @plotNumber.setter
    def plotNumber(self, text):
        self._site.plotNumber = _clean(text)

    @property
    def municipalityCode(self):
        return _text(self._site.municipality.code)

    @municipalityCode.setter
    def municipalityCode(self, text):
        self._site.municipality.code = _clean(text)

    @property
    def municipalityName(self):
        return _text(self._site.municipality.name)

    @municipalityName.setter
    def municipalityName(self, text):
        self._site.municipality.name = _clean(text)

    # ---- lookups ----------------------------------------------------------

    def coordinatesFromAddress(self):
        found = ch.findAddress(self.zip, self.street, self.streetNumber)
        if not found:
            return
        self.buildingId = found["egid"]
        self.swissGridX = found["x"]
        self.swissGridY = found["y"]
        self.municipalityCode = found["municipalityCode"]
        self.municipalityName = found["municipalityName"]

    def _lv95(self):
        lv95 = getExt(self._site, "ch", "lv95") or {}
        if "e" not in lv95 or "n" not in lv95:
            return None
        return lv95["e"], lv95["n"]

    def queryPlotNumber(self):
        lv95 = self._lv95()
        if not lv95:
            return
        number = ch.queryPlotNumber(*lv95)
        if number and not self.plotNumber:
            self.plotNumber = number

    def queryZoneing(self):
        lv95 = self._lv95()
        if not lv95:
            return
        zone = ch.queryZone(*lv95)
        if zone:
            self.areZoneCode = _text(zone["code"])
            self.areZoneName = _text(zone["name"])

    # Lookup the PowerCompany for this building.
    def getPowerCompanyId(self):
        from Config import Config

        # First check if in zip_code, city
        con = sqlite3.connect(Config.getMasterDbPath())
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT * FROM zip_code WHERE zip_code=?"
        res = cur.execute(sql, [self.zip])
        db_row = res.fetchone()

        if db_row:
            fkPowerCompany = db_row["fk_power_company"]
            if fkPowerCompany:
                return fkPowerCompany

        # Next in the Municipality
        sql = "SELECT * FROM municipality WHERE code=?"
        res = cur.execute(sql, [self.municipalityCode])
        db_row = res.fetchone()
        if db_row:
            fkPowerCompany = db_row["fk_power_company"]
            if fkPowerCompany:
                return fkPowerCompany

        return False

    # "Street 1, 1234 City", empty parts are left out
    def getHumanAddress(self):
        join = lambda sep, parts: sep.join(str(p) for p in parts if p)
        street = join(" ", (self.street, self.streetNumber))
        city = join(" ", (self.zip, self.city))
        return join(", ", (street, city))

    # Check wheter the address of the Building ist the same as the given
    # Contact
    def identicalAddress(self, contact):
        if self.street != contact.street or \
           self.streetNumber != contact.streetNumber or \
           self.zip != contact.zip or \
           self.city != contact.city:
            return False

        return True


def _siteAddressProperty(key):
    def getter(self):
        return _text(self._site.address.get(key))

    def setter(self, text):
        self._site.address.set(key, _clean(text))
    return property(getter, setter)


for _key in ("street", "streetNumber", "zip", "city", "region", "country"):
    setattr(SiteView, _key, _siteAddressProperty(_key))


# ---------------------------------------------------------------------------

V2_CONSTRUCTION_TYPES = {v: k for k, v in CONSTRUCTION_TYPES.items()}


class PlantView:

    # existing=True: not the devices of the order, but what was installed
    # before it and is still there. Read only.
    def __init__(self, project, order, existing=False):
        self._top = project
        self._order = order
        self._existing = existing

    def _devices(self, kind):
        if not self._existing:
            return self._order.getDevices(kind)
        return [d for d in self._top.devices
                if d.kind == kind and d.orderId != self._order.id and d.get("from") is not None and d.to is None]

    def _groups(self):
        ret = []
        for device in self._devices("pv_array"):
            for groupId in device.get("moduleGroupIds") or []:
                group = self._top.byId("moduleGroups", groupId)
                if group is not None and group not in ret:
                    ret.append(group)
        return ret

    def _readOnly(self):
        if self._existing:
            raise ValueError("bestehende Anlage: bitte im Baum bearbeiten")

    # The one module group the summary fields edit, created if wanted
    def _group(self, create):
        self._readOnly()
        groups = self._groups()
        if len(groups) > 1:
            raise ValueError("mehrere Modulgruppen: bitte im Baum bearbeiten")
        if groups or not create:
            return groups[0] if groups else None
        top = self._top
        building = top.buildings[0] if top.buildings else top.addPart("buildings")
        roof = building.roofs[0] if building.roofs else building.addPart("roofs")
        group = roof.addPart("moduleGroups")
        arrays = self._order.getDevices("pv_array")
        if arrays:
            arrays[0].set("moduleGroupIds", (arrays[0].get("moduleGroupIds") or []) + [group.id])
        else:
            device = top.addPart("devices", kind="pv_array", orderId=self._order.id, moduleGroupIds=[group.id])
            device.set("from", self._order.commissioned)
        return group

    # The type of a group or device, which must be one entered by hand and
    # used only there
    def _manualType(self, owner, kind, create):
        deviceType = owner.getType()
        if deviceType is None:
            if not create:
                return None
            deviceType = self._top.addPart("types", kind=kind, source={"db": "manual"})
            owner.typeId = deviceType.id
            return deviceType
        users = [g for g in self._top.allModuleGroups() if g.typeId == deviceType.id]
        users += [d for d in self._top.devices if d.typeId == deviceType.id]
        if (deviceType.source or {}).get("db", "manual") != "manual" or len(users) > 1:
            raise ValueError("Typ wird mehrfach verwendet: bitte im Baum bearbeiten")
        return deviceType

    # ---- modules ----------------------------------------------------------

    def _powerDc(self):
        powers = [g.getPower() if g.getPower() is not None else getV2(g, "totalPowerDc") for g in self._groups()]
        powers = [p for p in powers if p is not None]
        return sum(powers) if powers else None

    def _setPowerDc(self, power):
        group = self._group(create=power is not None)
        if group is None:
            return
        panelType = self._manualType(group, "panel", create=power is not None)
        if panelType is None:
            return
        if power is not None and group.count:
            panelPower = power / group.count
            if round(panelPower, 3) * group.count == power:
                panelPower = round(panelPower, 3)
            panelType.specs["power"] = int(panelPower) if panelPower == int(panelPower) else panelPower
            setV2(group, "totalPowerDc", None)
        else:
            # without the number of modules the power of one is not known
            panelType.specs.pop("power", None)
            setV2(group, "totalPowerDc", power)

    @property
    def totalPowerDc(self):
        power = self._powerDc()
        return "" if power is None else values.numberToText(round(power / 1000, 6))

    @totalPowerDc.setter
    def totalPowerDc(self, text):
        power = values.textToNumber(text)
        self._setPowerDc(None if power is None else round(power * 1000, 6))

    @property
    def totalPanelCount(self):
        counts = [g.count for g in self._groups() if g.count is not None]
        return _text(sum(counts)) if counts else ""

    @totalPanelCount.setter
    def totalPanelCount(self, text):
        count = values.textToInt(text)
        power = self._powerDc()
        group = self._group(create=count is not None)
        if group is None:
            return
        group.count = count
        # the total power stays, the power of one module follows
        if power is not None:
            self._setPowerDc(power)

    @property
    def panelDesc(self):
        names = []
        for group in self._groups():
            panelType = group.getType()
            if panelType and panelType.getName() and panelType.getName() not in names:
                names.append(panelType.getName())
        return ", ".join(names)

    @panelDesc.setter
    def panelDesc(self, text):
        group = self._group(create=_clean(text) is not None)
        if group is None:
            return
        panelType = self._manualType(group, "panel", create=_clean(text) is not None)
        if panelType is not None:
            panelType.manufacturer = None
            panelType.model = _clean(text)

    @property
    def totalArea(self):
        areas = []
        for group in self._groups():
            area = getV2(group, "totalArea")
            panelType = group.getType()
            if area is None and panelType and group.count:
                width, height = panelType.specs.get("width"), panelType.specs.get("height")
                if width and height:
                    area = round(width * height * group.count / 1000000, 2)
            if area is not None:
                areas.append(area)
        return values.numberToText(sum(areas)) if areas else ""

    @totalArea.setter
    def totalArea(self, text):
        area = values.textToNumber(text)
        group = self._group(create=area is not None)
        if group is not None:
            setV2(group, "totalArea", area)

    # ---- inverters --------------------------------------------------------

    def _inverter(self, create):
        self._readOnly()
        inverters = self._devices("inverter")
        if len(inverters) > 1:
            raise ValueError("mehrere Wechselrichter: bitte im Baum bearbeiten")
        if inverters or not create:
            return inverters[0] if inverters else None
        device = self._top.addPart("devices", kind="inverter", orderId=self._order.id)
        device.set("from", self._order.commissioned)
        return device

    @property
    def totalPowerAc(self):
        powers = []
        for device in self._devices("inverter"):
            deviceType = device.getType()
            power = deviceType.specs.get("powerAc") if deviceType else None
            if power is not None:
                powers.append(power * (device.count or 1))
        return values.numberToText(round(sum(powers) / 1000, 6)) if powers else ""

    @totalPowerAc.setter
    def totalPowerAc(self, text):
        power = values.textToNumber(text)
        device = self._inverter(create=power is not None)
        if device is None:
            return
        deviceType = self._manualType(device, "inverter", create=power is not None)
        if deviceType is None:
            return
        if power is None:
            deviceType.specs.pop("powerAc", None)
        else:
            power = round(power * 1000 / (device.count or 1), 6)
            deviceType.specs["powerAc"] = int(power) if power == int(power) else power

    @property
    def inverterDesc(self):
        names = []
        for device in self._devices("inverter"):
            deviceType = device.getType()
            if deviceType and deviceType.getName():
                name = deviceType.getName()
                if (device.count or 1) > 1:
                    name = str(device.count) + " x " + name
                if name not in names:
                    names.append(name)
        return ", ".join(names)

    @inverterDesc.setter
    def inverterDesc(self, text):
        device = self._inverter(create=_clean(text) is not None)
        if device is None:
            return
        deviceType = self._manualType(device, "inverter", create=_clean(text) is not None)
        if deviceType is not None:
            deviceType.manufacturer = None
            deviceType.model = _clean(text)

    # ---- batteries (new with version 3, for the form scripts) ---------------

    @property
    def batteryDesc(self):
        names = []
        for device in self._devices("battery"):
            deviceType = device.getType()
            if deviceType and deviceType.getName() and deviceType.getName() not in names:
                names.append(deviceType.getName())
        return ", ".join(names)

    # usable capacity of all batteries in kWh
    @property
    def batteryCapacity(self):
        return self._sumSpec("battery", "capacity")

    # discharge power of all batteries in kW
    @property
    def batteryPower(self):
        return self._sumSpec("battery", "powerDischarge")

    def _sumSpec(self, kind, spec):
        found = []
        for device in self._devices(kind):
            deviceType = device.getType()
            value = deviceType.specs.get(spec) if deviceType else None
            if value is not None:
                found.append(value * (device.count or 1))
        return values.numberToText(round(sum(found) / 1000, 6)) if found else ""

    # True if there are devices of a kind
    def has(self, kind):
        return bool(self._devices(kind))

    # ---- order ------------------------------------------------------------

    @property
    def totalCost(self):
        return values.numberToText(self._order.totalCost)

    @totalCost.setter
    def totalCost(self, text):
        self._readOnly()
        self._order.totalCost = values.textToNumber(text)

    @property
    def constructionType(self):
        return V2_CONSTRUCTION_TYPES.get(self._order.constructionType, "")

    @constructionType.setter
    def constructionType(self, text):
        self._readOnly()
        text = _clean(text)
        if text is not None and text not in CONSTRUCTION_TYPES:
            raise ValueError("unbekannte Bauart: " + text)
        self._order.constructionType = CONSTRUCTION_TYPES.get(text)
        for group in self._groups():
            if group.mounting in (None, "on_roof", "in_roof", "facade"):
                group.mounting = self._order.constructionType


# ---------------------------------------------------------------------------

class ProgressView:

    def __init__(self, project, order):
        self._top = project
        self._order = order

    # ---- quotes: quote1Sent is the date of the first quote of the order -----

    def _getQuote(self, number):
        quotes = self._order.getQuotes()
        return values.dateToText(quotes[number].date) if number < len(quotes) else ""

    def _setQuote(self, number, text):
        day = values.textToDate(text)
        quotes = self._order.getQuotes()
        if number < len(quotes):
            quote = quotes[number]
            quote.date = day
            if day is not None and quote.state in (None, "draft"):
                quote.state = "sent"
            if day is None and not quote.hasContent():
                self._top.removePart(quote)
        elif day is not None:
            self._top.addPart("quotes", date=day, state="sent", orderId=self._order.id)

    # ---- steps ------------------------------------------------------------

    def _getStep(self, kind, state):
        step = self._order.getStep(kind)
        return values.dateToText(step.dates.get(state)) if step else ""

    def _setStep(self, kind, state, text):
        day = values.textToDate(text)
        step = self._order.getStep(kind)
        if step is None:
            if day is None:
                return
            step = self._order.addPart("steps", kind=kind)
        step.setDate(state, day)
        if not step.hasContent():
            self._order.removePart(step)

    # ---- invoices ---------------------------------------------------------

    def _getInvoice(self, kind, number, field):
        invoice = self._order.getInvoice(kind, number)
        return values.dateToText(invoice.get(field)) if invoice else ""

    def _setInvoice(self, kind, number, field, text):
        day = values.textToDate(text)
        invoice = self._order.getInvoice(kind, number)
        if invoice is None:
            if day is None:
                return
            invoice = self._order.addPart("invoices", kind=kind)
        invoice.set(field, day)
        if not invoice.hasContent():
            self._order.removePart(invoice)

    # ---- the construction date can not be moved ---------------------------

    @property
    def constructionFixed(self):
        return bool(self._order.constructionFixed)

    @constructionFixed.setter
    def constructionFixed(self, value):
        self._order.constructionFixed = True if value else None

    # returns state of the project:
    #  activ: Something needs to be done at some point
    #  inactiv: Project will probably be built or not nothing to be done
    #  archived: everything said and done
    #  rejected: project will never be built by us

    def getState(self):
        if self.orderRejected:
            return "9 - rejected " + self.orderRejected

        # manuell archiviert
        if self.archived:
            return "8 - archived " + self.archived + " manu"

        # EIV ausbezahlt und Schlussrechnung bezahlt => archiviert
        if self.eivPayed and self.finalInvoiceReceived:
            return "8 - archived " + self.eivPayed + " auto"

        # Auftrag abgeschlossen
        if self.eivPayed:
            return "7.2 - EIV payed " + self.eivPayed

        if self.eivComplete:
            return "7.1 - EIV complete " + self.eivComplete

        if self.launch:
            return "6 - in Betrieb " + self.launch

        # Auftrag erhalten und noch nicht abgeschlossen => aktiv
        if self.orderReceived:
            return "5 - building " + self.orderReceived

        # Auftrag noch nicht erhalten und letzte Aktion nicht älter als
        # 3? Monate => aktiv
        lastQuote = max([values.dateToText(q.date) for q in self._order.getQuotes() if q.date] or [""])
        if lastQuote:
            return "4 - quoted " + lastQuote

        if self.inquiryReceived:
            return "3 - lead " + self.inquiryReceived

        return "1 - nothing"

    # returns what to do for the project sortable by Importance
    def getToDo(self):
        if not self.launch:
            if self.inquiryReceived and not self.quote1Sent:
                return "2 - quote"

            if self.orderReceived and not self.tagSent:
                return "3 - send TAG"

            if self.orderReceived and not self.bauSent:
                return "3 - send Bau"

            if not self.tagReceived and self.tagSent:
                return "4 - check TAG"

            if not self.bauReceived and self.bauSent:
                return "4 - check Bau"

            if not self.iaReceived and self.iaSent:
                return "4 - check IA"

        if not self.siNaDcReceived and self.siNaDcOrdered:
            return "6 - check siNaDc"

        if not self.siNaAcReceived and self.siNaAcOrdered:
            return "6 - check siNaDc"

        if not self.orderReceived:
            return "1 - wait customer"

        return "0 - I dunno"

    # constructionSort defaults to orderReceived
    def getConstructionSort(self):
        if not self.constructionSort:
            self.constructionSort = self.orderReceived
        return self.constructionSort


def _orderDateProperty(field):
    def getter(self):
        return values.dateToText(self._order.get(field))

    def setter(self, text):
        self._order.set(field, values.textToDate(text))
    return property(getter, setter)


for _name, _field in ORDER_DATES.items():
    setattr(ProgressView, _name, _orderDateProperty(_field))
for _number, _name in enumerate(QUOTE_DATES):
    setattr(ProgressView, _name, property(lambda self, n=_number: self._getQuote(n),
                                          lambda self, text, n=_number: self._setQuote(n, text)))
for _name, (_kind, _state) in STEP_DATES.items():
    setattr(ProgressView, _name, property(lambda self, k=_kind, s=_state: self._getStep(k, s),
                                          lambda self, text, k=_kind, s=_state: self._setStep(k, s, text)))
for _name, (_kind, _number, _field) in INVOICE_DATES.items():
    setattr(ProgressView, _name, property(
        lambda self, k=_kind, n=_number, f=_field: self._getInvoice(k, n, f),
        lambda self, text, k=_kind, n=_number, f=_field: self._setInvoice(k, n, f, text)))
