#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The version 3 project: file format, and the fields of version 2 on top of
# it (model/compat.py).

import os
import json
import tempfile
import unittest

from model.PvProject import PvProject
from model import values
import formats.pvp
from tests import v2_example


def v2_text(project=None):
    return json.dumps({"format": "gnusolar-project", "version": 2, "project": project or v2_example.project()})


def load(project=None):
    p = PvProject()
    formats.pvp.loads(p, v2_text(project), taken=1794312000)
    return p


def day(text):
    return values.textToDate(text)


class FileFormatTest(unittest.TestCase):

    def test_roundtrip(self):
        p = load()
        p.prepareSave()
        text = formats.pvp.dumps(p)
        data = json.loads(text)
        self.assertEqual((data["format"], data["version"]), ("gnusolar-project", 3))
        self.assertEqual(len(data["project"]["id"]), 36)
        q = PvProject()
        formats.pvp.loads(q, text)
        self.assertIsNone(q._migratedFrom)
        self.assertEqual(formats.pvp.dumps(q), text)

    def test_unknown_fields_and_plugin_data_survive(self):
        p = load()
        data = json.loads(formats.pvp.dumps(p))
        project = data["project"]
        project["futureField"] = {"a": 1}
        project["devices"][0]["ext"] = {"huawei.fusionsolar": {"v": 1, "plantId": "NE=33"}}
        project["devices"][0]["futureDeviceField"] = 5
        project["orders"][0]["steps"][0]["somethingNew"] = [1, 2]
        project["plugins"].append({"id": "huawei.fusionsolar", "version": "1.2", "name": "Huawei FusionSolar"})
        q = PvProject()
        formats.pvp.loads(q, json.dumps(data))
        again = json.loads(formats.pvp.dumps(q))["project"]
        self.assertEqual(again["futureField"], {"a": 1})
        self.assertEqual(again["devices"][0]["ext"], project["devices"][0]["ext"])
        self.assertEqual(again["devices"][0]["futureDeviceField"], 5)
        self.assertEqual(again["orders"][0]["steps"][0]["somethingNew"], [1, 2])
        self.assertEqual([p["id"] for p in again["plugins"]], ["ch", "huawei.fusionsolar"])

    def test_newer_version_is_refused(self):
        with self.assertRaises(Exception):
            formats.pvp.loads(PvProject(), json.dumps({"format": "gnusolar-project", "version": 4, "project": {}}))

    def test_save_keeps_the_version_2_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "plant.pvp")
            with open(path, "w", encoding="utf-8") as f:
                f.write(v2_text())
            p = PvProject(path)
            self.assertEqual(p._migratedFrom, 2)
            p.save()
            self.assertEqual(json.load(open(path + ".v2"))["version"], 2)
            self.assertEqual(json.load(open(path))["version"], 3)
            self.assertFalse(os.path.exists(path + ".tmp"))
            # a second save doesn't touch the copy
            os.remove(path + ".v2")
            p.save()
            self.assertFalse(os.path.exists(path + ".v2"))
            self.assertIsNone(PvProject(path)._migratedFrom)

    def test_new_project(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "plant.pvp")
            p = PvProject()
            p.initFromAddress("Kirchweg", "26", "4314", "Musterwil")
            p.saveAs(path)
            data = json.load(open(path))["project"]
            self.assertEqual(data["site"]["address"], {"street": "Kirchweg", "streetNumber": "26", "zip": "4314",
                                                       "city": "Musterwil"})
            self.assertEqual(data["orders"][0]["type"], "new_system")
            self.assertEqual(data["orders"][0]["state"], "inquiry")
            self.assertEqual(data["orders"][0]["inquiry"], values.today())
            self.assertEqual(data["currency"], "CHF")
            self.assertEqual(data["contacts"], [])
            self.assertTrue(data["created"])


class Version2FieldsTest(unittest.TestCase):

    def test_site(self):
        b = load().building
        self.assertEqual((b.street, b.streetNumber, b.zip, b.city), ("Kirchweg", "26", "4314", "Musterwil"))
        self.assertEqual((b.swissGridX, b.swissGridY), ("632561.2", "265432.8"))
        self.assertEqual((b.buildingId, b.plotNumber, b.mainFuseSize), ("190335642", "1060", "40"))
        self.assertEqual((b.areZoneCode, b.areZoneName, b.buildingState), ("11", "Wohnzonen", "existing"))
        self.assertEqual((b.meterNumberOld, b.meterNumberNew), ("12345678", "87654321"))
        self.assertEqual(b.getHumanAddress(), "Kirchweg 26, 4314 Musterwil")
        self.assertEqual(b.country, "")

    def test_site_edit(self):
        p = load()
        b = p.building
        b.swissGridX = "2645484.8"
        b.swissGridY = "252470.8"
        self.assertEqual(p.site.ext["ch"]["lv95"], {"e": 2645484.8, "n": 1252470.8})
        self.assertAlmostEqual(p.site.latitude, 47.4215, places=3)
        with self.assertRaises(ValueError):
            b.swissGridX = "12"
        b.mainFuseSize = "63"
        self.assertEqual(p.site.supply.mainFuse, 63)
        with self.assertRaises(ValueError):
            b.mainFuseSize = "3x40"
        b.buildingId = ""
        self.assertNotIn("egid", p.site.ext["ch"])
        b.areZoneCode = ""
        b.areZoneName = ""
        b.swissGridX = ""
        b.swissGridY = ""
        self.assertNotIn("ch", p.site.ext)

    def test_meters(self):
        p = load(dict(v2_example.project(), building=dict(v2_example.project()["building"],
                                                           meterNumberOld="", meterNumberNew="")))
        b = p.building
        self.assertEqual((b.meterNumberOld, b.meterNumberNew), ("", ""))
        b.meterNumberNew = "222"
        b.meterNumberOld = "111"
        old, new = [d for d in p.devices if d.kind == "meter"]
        self.assertEqual((old.get("number"), old.to, old.orderId), ("111", day("2026-06-20"), None))
        self.assertEqual((new.get("number"), new.get("from"), new.replacesId), ("222", day("2026-06-20"), old.id))
        b.meterNumberOld = ""
        self.assertEqual(len([d for d in p.devices if d.kind == "meter"]), 1)
        self.assertIsNone(new.replacesId)

    def test_plant(self):
        pl = load().plant
        self.assertEqual((pl.totalPowerDc, pl.totalPanelCount, pl.panelDesc), ("10.56", "24", "JA Solar 440"))
        self.assertEqual((pl.totalArea, pl.totalPowerAc, pl.inverterDesc), ("47.9", "10", "Fronius Symo 10.0-3-M"))
        self.assertEqual((pl.totalCost, pl.constructionType), ("18450", "builton"))

    def test_plant_edit(self):
        p = load()
        pl = p.plant
        pl.totalPanelCount = "26"
        self.assertEqual(pl.totalPowerDc, "10.56")       # the total stays
        pl.totalPowerDc = "11,44"
        self.assertEqual(p.types[0].specs["power"], 440)
        pl.totalPowerAc = "8"
        self.assertEqual(p.types[1].specs["powerAc"], 8000)
        pl.constructionType = "integrated"
        self.assertEqual(p.orders[0].constructionType, "in_roof")
        self.assertEqual(p.allModuleGroups()[0].mounting, "in_roof")
        with self.assertRaises(ValueError):
            pl.totalCost = "ca. 18000"
        pl.totalPanelCount = ""
        self.assertEqual(pl.totalPowerDc, "11.44")       # kept without the number of modules
        pl.totalPanelCount = "26"
        self.assertEqual(p.types[0].specs["power"], 440)

    def test_plant_from_nothing(self):
        p = PvProject()
        pl = p.plant
        self.assertEqual((pl.totalPowerDc, pl.totalPanelCount, pl.panelDesc, pl.inverterDesc), ("", "", "", ""))
        pl.totalPowerDc = "9.9"
        pl.totalPanelCount = "22"
        pl.panelDesc = "Modul 450"
        pl.inverterDesc = "WR 10"
        pl.totalPowerAc = "10"
        self.assertEqual(len(p.buildings[0].roofs[0].moduleGroups), 1)
        self.assertEqual([(t.kind, t.model) for t in p.types], [("panel", "Modul 450"), ("inverter", "WR 10")])
        self.assertEqual(p.types[0].specs, {"power": 450})
        self.assertEqual([d.kind for d in p.devices], ["pv_array", "inverter"])
        self.assertEqual(p.devices[0].orderId, p.orders[0].id)
        self.assertEqual((pl.totalPowerDc, pl.totalPowerAc), ("9.9", "10"))

    def test_plant_with_several_groups(self):
        p = load()
        roof = p.buildings[0].roofs[0]
        second = roof.addPart("moduleGroups", typeId=p.types[0].id, count=10)
        p.devices[0].set("moduleGroupIds", p.devices[0].get("moduleGroupIds") + [second.id])
        pl = p.plant
        self.assertEqual((pl.totalPanelCount, pl.totalPowerDc), ("34", "14.96"))
        with self.assertRaises(ValueError):
            pl.totalPanelCount = "30"

    def test_existing_system(self):
        p = load()
        battery = p.addOrder("battery", "Batterie 10 kWh")
        batteryType = p.addPart("types", kind="battery", manufacturer="BYD", model="HVS 10.2",
                                specs={"capacity": 10240, "powerDischarge": 10240})
        p.addPart("devices", kind="battery", orderId=battery.id, typeId=batteryType.id)
        self.assertIs(p.currentOrder, battery)
        self.assertEqual((p.plant.totalPowerDc, p.plant.batteryDesc, p.plant.batteryCapacity),
                         ("", "BYD HVS 10.2", "10.24"))
        self.assertTrue(p.plant.has("battery"))
        self.assertEqual((p.existing.totalPowerDc, p.existing.inverterDesc), ("10.56", "Fronius Symo 10.0-3-M"))
        self.assertFalse(p.existing.has("battery"))
        with self.assertRaises(ValueError):
            p.existing.totalPowerDc = "5"
        p.currentOrder = p.orders[0]
        self.assertEqual(p.plant.totalPowerDc, "10.56")
        self.assertEqual(p.existing.totalPowerDc, "")

    def test_progress(self):
        pr = load().progress
        self.assertEqual((pr.inquiryReceived, pr.orderReceived, pr.launch), ("2026-03-01", "2026-04-15", "2026-06-20"))
        self.assertEqual((pr.quote1Sent, pr.quote2Sent, pr.quote3Sent), ("2026-03-20", "2026-04-02", ""))
        self.assertEqual((pr.tagSent, pr.tagReceived, pr.bauSent, pr.bauReceived), ("2026-04-20", "2026-05-10", "2026-04-21", ""))
        self.assertEqual((pr.partialInvoiceSent, pr.partialInvoiceReceived, pr.finalInvoiceSent), ("2026-06-01", "2026-06-20", "2026-06-25"))
        self.assertIs(pr.constructionFixed, True)
        self.assertEqual(pr.getState(), "7.1 - EIV complete 2026-07-01")
        self.assertEqual(pr.getConstructionSort(), "2026-04-15")

    def test_progress_edit(self):
        p = load()
        pr = p.progress
        order = p.orders[0]
        pr.eivPayed = "2026-09-01"
        self.assertEqual(order.getStep("ch.pronovo").state, "paid")
        self.assertEqual(pr.getState(), "7.2 - EIV payed 2026-09-01")
        pr.finalInvoiceReceived = "10.09.2026"
        self.assertEqual(order.getInvoice("final").paid, day("2026-09-10"))
        self.assertEqual(pr.getState(), "8 - archived 2026-09-01 auto")
        pr.materialOrdered = "2026-05-01"
        self.assertEqual(order.getStep("material").dates, {"ordered": day("2026-05-01")})
        pr.materialOrdered = ""
        self.assertIsNone(order.getStep("material"))
        pr.quote3Sent = "2026-04-10"
        self.assertEqual(len(p.quotes), 3)
        pr.quote3Sent = ""
        self.assertEqual(len(p.quotes), 2)
        with self.assertRaises(ValueError):
            pr.tagSent = "2026"
        self.assertEqual(pr.tagSent, "2026-04-20")
        pr.constructionFixed = False
        self.assertIsNone(order.constructionFixed)

    def test_launch_moves_the_devices(self):
        p = load()
        p.progress.launch = "2026-07-01"
        self.assertEqual({d.get("from") for d in p.devices if d.orderId}, {day("2026-07-01")})
        self.assertEqual(p.devices[2].to, day("2026-07-01"))     # the old meter

    def test_states(self):
        p = PvProject()
        pr = p.progress
        self.assertEqual(pr.getState(), "1 - nothing")
        pr.inquiryReceived = "2026-01-05"
        self.assertEqual((pr.getState(), pr.getToDo()), ("3 - lead 2026-01-05", "2 - quote"))
        pr.quote1Sent = "2026-01-10"
        self.assertEqual((pr.getState(), pr.getToDo()), ("4 - quoted 2026-01-10", "1 - wait customer"))
        pr.orderReceived = "2026-02-01"
        self.assertEqual((pr.getState(), pr.getToDo()), ("5 - building 2026-02-01", "3 - send TAG"))
        self.assertEqual(p.orders[0].deriveState(), "running")
        pr.orderRejected = "2026-02-02"
        self.assertEqual(pr.getState(), "9 - rejected 2026-02-02")
        self.assertEqual(p.orders[0].deriveState(), "rejected")

    def test_contacts(self):
        p = load()
        owner = p.contacts.owner
        self.assertEqual((owner.firstName, owner.lastName, owner.street, owner.zip), ("Hans", "Muster", "Kirchweg", "4314"))
        self.assertEqual((owner.phone, owner.phone2, owner.mobile, owner.email, owner.email2),
                         ("061 000 00 00", "", "079 000 00 00", "hans@example.ch", ""))
        self.assertEqual((owner.accountOwner, owner.accountIban, owner.accountIid, owner.company),
                         ("Hans Muster", "CH00 0000 0000 0000 0000 0", "80808", ""))
        self.assertEqual(owner.getNameCity(), "Muster Hans Musterwil")
        self.assertEqual(owner.role, "owner")
        self.assertTrue(p.building.identicalAddress(owner))
        # the electrician is there for the forms, but not saved while empty
        electrician = p.contacts.installer_ac
        self.assertEqual((electrician.role, electrician.lastName, electrician.phone), ("installer_ac", None, ""))
        self.assertEqual(len(p.toDict()["contacts"]), 1)
        electrician.company = "Elektro AG"
        electrician.phone2 = "062 111 11 11"
        electrician.email = "info@example.ch"
        electrician.phone = "062 000 00 00"
        self.assertEqual(p.toDict()["contacts"][1]["channels"], [
            {"kind": "phone", "value": "062 000 00 00"}, {"kind": "phone", "value": "062 111 11 11"},
            {"kind": "email", "value": "info@example.ch"}])
        self.assertEqual((electrician.phone, electrician.phone2), ("062 000 00 00", "062 111 11 11"))
        owner.accountIid = ""
        owner.accountOwner = ""
        owner.accountBank = ""
        owner.accountIban = ""
        self.assertEqual(owner.bankAccounts, [])

    def test_snapshots(self):
        p = load()
        self.assertEqual((p.municipality.name, p.municipality.fkFormBuilding), ("Musterwil", 2))
        self.assertEqual(p.municipality.buildingContact.email, "bau@example.ch")
        self.assertEqual((p.powerCompany.name, p.powerCompany.fkFormTag, p.powerCompany.zipCode),
                         ("Elektra Musterwil", 4, "4314"))
        self.assertEqual(p.powerCompany.tagContact.email, "tag@example.ch")
        self.assertEqual(p.comment, "Hund im Garten")


if __name__ == "__main__":
    unittest.main()
