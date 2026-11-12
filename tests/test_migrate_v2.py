#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import unittest

from formats.migrate_v2 import migrate, Report
from model import values
from plugins import ch
from tests import v2_example


def ids():
    n = 0
    while True:
        n += 1
        yield "id-%d" % n


def run(old=None, files=None):
    report = Report()
    gen = ids()
    new = migrate(old or v2_example.project(), taken=1794312000, files=files, report=report, newId=lambda: next(gen))
    return new, report


def day(text):
    return values.textToDate(text)


class MigrateV2Test(unittest.TestCase):

    def test_site(self):
        new, report = run()
        site = new
        self.assertEqual(site["address"], {"street": "Kirchweg", "streetNumber": "26", "zip": "4314", "city": "Musterwil"})
        self.assertEqual(site["plotNumber"], "1060")
        self.assertEqual(site["supply"], {"mainFuse": 40})
        self.assertEqual(site["ext"]["ch"], {"v": 1, "lv95": {"e": 2632561.2, "n": 1265432.8}, "egid": [190335642],
                                             "zone": {"code": "11", "name": "Wohnzonen"}})
        self.assertEqual((site["latitude"], site["longitude"]), ch.lv95ToWgs84(2632561.2, 1265432.8))
        self.assertEqual(site["ext"]["gnusolar"]["v2"], {"buildingState": "existing"})
        self.assertIn(("building.buildingState", "existing"), report.kept)

    def test_snapshots(self):
        new, report = run()
        mun = new["municipality"]
        self.assertEqual(mun["taken"], 1794312000)
        self.assertEqual((mun["id"], mun["code"], mun["name"], mun["stateCode"]), (1215, "4264", "Musterwil", "AG"))
        self.assertEqual(mun["ext"]["ch"], {"v": 1, "buildingFormId": 2})
        self.assertEqual(mun["buildingContact"], {"organization": "Bauverwaltung",
                                                  "channels": [{"kind": "email", "value": "bau@example.ch"}]})
        grid = new["gridOperator"]
        self.assertEqual(grid["address"], {"address1": "Kirchweg 1", "zip": "4314", "city": "Musterwil"})
        self.assertEqual(grid["connectionContact"]["organization"], "Netz AG")
        self.assertEqual(grid["ext"]["ch"], {"v": 1, "tagFormId": 4})
        self.assertNotIn("mainContact", grid)
        self.assertIn(("municipality.fkPowerCompany", 402), report.dropped)
        self.assertIn(("powerCompany.fkContactTag", 12), report.dropped)
        self.assertIn(("state", "Running"), report.dropped)

    def test_contacts(self):
        new, report = run()
        self.assertEqual(len(new["contacts"]), 1)       # the empty electrician is left out
        owner = new["contacts"][0]
        self.assertEqual(owner["roles"], ["owner"])
        self.assertEqual(owner["address"]["city"], "Musterwil")
        self.assertEqual(owner["channels"], [{"kind": "phone", "value": "061 000 00 00"},
                                             {"kind": "mobile", "value": "079 000 00 00"},
                                             {"kind": "email", "value": "hans@example.ch"}])
        self.assertEqual(owner["bankAccounts"], [{"owner": "Hans Muster", "bank": "Musterbank",
                                                  "iban": "CH00 0000 0000 0000 0000 0",
                                                  "ext": {"ch": {"v": 1, "iid": "80808"}}}])

    def test_plant(self):
        new, report = run()
        types = {t["kind"]: t for t in new["types"]}
        self.assertEqual(types["panel"]["model"], "JA Solar 440")
        self.assertEqual(types["panel"]["specs"], {"power": 440})
        self.assertEqual(types["inverter"]["specs"], {"powerAc": 10000})
        group = new["buildings"][0]["roofs"][0]["moduleGroups"][0]
        self.assertEqual(group["count"], 24)
        self.assertEqual(group["mounting"], "on_roof")
        self.assertEqual(group["typeId"], types["panel"]["id"])
        self.assertEqual(group["ext"]["gnusolar"]["v2"], {"totalArea": 47.9})
        devices = {d["kind"]: d for d in new["devices"] if d["kind"] != "meter"}
        self.assertEqual(devices["pv_array"]["moduleGroupIds"], [group["id"]])
        self.assertEqual(devices["pv_array"]["from"], day("2026-06-20"))
        self.assertEqual(devices["inverter"]["projectId"], new["projects"][0]["id"])

    def test_meters(self):
        new, report = run()
        old, newMeter = [d for d in new["devices"] if d["kind"] == "meter"]
        self.assertEqual((old["number"], old["to"]), ("12345678", day("2026-06-20")))
        self.assertNotIn("projectId", old)
        self.assertEqual((newMeter["number"], newMeter["from"], newMeter["replacesId"]),
                         ("87654321", day("2026-06-20"), old["id"]))

    def test_project(self):
        new, report = run()
        project = new["projects"][0]
        self.assertEqual(project["type"], "new_system")
        self.assertEqual(project["title"], "PV-Anlage 10.56 kWp")
        self.assertEqual(project["state"], "in_operation")
        self.assertEqual(project["folder"], "")
        self.assertEqual(project["inquiry"], day("2026-03-01"))
        self.assertEqual(project["ordered"], day("2026-04-15"))
        self.assertEqual(project["commissioned"], day("2026-06-20"))
        self.assertIs(project["constructionFixed"], True)
        self.assertEqual(project["constructionType"], "on_roof")
        self.assertEqual(project["totalCost"], 18450)
        self.assertNotIn("roofMeasure", project)
        self.assertEqual(new["notes"], "Hund im Garten")

    def test_steps(self):
        new, report = run()
        steps = {s["kind"]: s for s in new["projects"][0]["steps"]}
        self.assertEqual(steps["ch.tag"]["dates"], {"submitted": day("2026-04-20"), "approved": day("2026-05-10")})
        self.assertEqual(steps["ch.tag"]["state"], "approved")
        self.assertNotIn("material", steps)
        # a year is no date: kept as a note
        self.assertEqual(steps["ch.pronovo"]["dates"], {"submitted": day("2026-07-01")})
        self.assertEqual(steps["ch.pronovo"]["notes"], "eivPayed: 2027")
        # two dates: the first one, and a note
        self.assertEqual(steps["ch.ia"]["dates"], {"submitted": day("2026-05-01")})
        self.assertEqual(steps["ch.ia"]["notes"], "iaSent: 2026-05-01/2026-06-01")
        self.assertEqual(steps["ch.building_permit"]["notes"], "bauReceived: other")
        self.assertIn(("progress.iaSent", "2026-05-01/2026-06-01"), report.manual)
        self.assertEqual(len(report.notes), 3)

    def test_quotes_and_invoices(self):
        files = ["off/O2026-03-0041.odt", "off/O2026-03-0041.pdf", "off/O2026-04-0050.odt",
                 "fin/R2026-06-0123.pdf", "fin/R2026-06-0130_Schluss.pdf", "fin/QR2026-06-01.pdf"]
        new, report = run(files=files)
        project = new["projects"][0]
        # the quotes are parts of the project
        self.assertNotIn("quotes", new)
        self.assertEqual([(q["date"], q["number"], q["state"], sorted(q)) for q in project["quotes"]],
                         [(day("2026-03-20"), "O2026-03-0041", "sent", ["date", "documents", "id", "number", "state"]),
                          (day("2026-04-02"), "O2026-04-0050", "sent", ["date", "documents", "id", "number", "state"])])
        self.assertEqual(project["quotes"][0]["documents"], [{"path": "off/O2026-03-0041.pdf", "kind": "quote"}])
        self.assertEqual([(i["kind"], i["date"], i.get("paid"), i["number"]) for i in project["invoices"]],
                         [("partial", day("2026-06-01"), day("2026-06-20"), "R2026-06-0123"),
                          ("final", day("2026-06-25"), None, "R2026-06-0130")])

    def test_numbers_without_files(self):
        new, report = run()
        self.assertNotIn("number", new["projects"][0]["quotes"][0])

    def test_values_that_do_not_fit(self):
        old = v2_example.project()
        old["plant"].update({"totalPanelCount": "", "totalPowerDc": "10.56", "totalCost": "ca. 18000",
                             "constructionType": "carport"})
        old["building"].update({"swissGridX": "abc", "mainFuseSize": "3x40"})
        old["newField"] = "x"
        new, report = run(old)
        group = new["buildings"][0]["roofs"][0]["moduleGroups"][0]
        self.assertNotIn("count", group)
        self.assertEqual(group["ext"]["gnusolar"]["v2"]["totalPowerDc"], 10560)
        self.assertNotIn("specs", [t for t in new["types"] if t["kind"] == "panel"][0])
        project = new["projects"][0]
        self.assertEqual(project["ext"]["gnusolar"]["v2"], {"totalCost": "ca. 18000", "constructionType": "carport"})
        # what the building had and what the project had lie together now
        self.assertEqual(new["ext"]["gnusolar"]["v2"], {"buildingState": "existing", "swissGridX": "abc",
                                                         "swissGridY": "265432.8", "mainFuseSize": "3x40",
                                                         "newField": "x"})
        self.assertNotIn("lv95", new["ext"]["ch"])

    def test_empty_project(self):
        old = v2_example.project()
        for part in ("building", "plant", "progress"):
            old[part] = {key: None for key in old[part]}
        old["contacts"]["contacts"]["owner"] = v2_example.contact("owner")
        new, report = run(old)
        self.assertEqual(new["contacts"], [])
        self.assertEqual(new["buildings"], [])
        self.assertEqual(new["devices"], [])
        self.assertEqual(new["types"], [])
        self.assertEqual(new["projects"], [{"id": new["projects"][0]["id"], "type": "new_system", "folder": "",
                                          "state": "inquiry", "title": "PV-Anlage"}])

    def test_coordinates(self):
        # the example of swisstopo's formulas: 8°43'49.79" E, 46°02'38.87" N
        lat, lon = ch.lv95ToWgs84(2700000, 1100000)
        self.assertAlmostEqual(lat, 46.044131, places=5)
        self.assertAlmostEqual(lon, 8.730497, places=5)
        self.assertEqual(ch.lv95FromText("632561.2", " 265432.8\t"), (2632561.2, 1265432.8))
        self.assertEqual(ch.lv95FromText("2632561", "1265432"), (2632561, 1265432))
        self.assertIsNone(ch.lv95FromText("1", "2"))

    def test_plugins(self):
        new, report = run()
        self.assertEqual(new["plugins"], [{"id": "ch", "name": "Switzerland", "version": "1"}])


if __name__ == "__main__":
    unittest.main()
