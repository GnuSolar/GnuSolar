#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The electrical installation of doc/file_format.md, section 10, read into
# the model, and the checks on it.

import re
import os
import json
import unittest

from model.PvSite import PvSite
from model.checks import check
from model import values


# the example of section 10: a hybrid inverter with partial backup
def example():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "doc", "file_format.md")
    text = open(path, encoding="utf-8").read()
    start = text.index("### Example", text.index("## 10. Electrical installation"))
    block = re.search(r"```json\n(.*?)```", text[start:], re.S).group(1)
    return json.loads("{" + block + "}")


def load(data):
    p = PvSite()
    p.fromDict(data)
    p.link(p)
    return p


class ElectricalInstallationTest(unittest.TestCase):

    def test_example_of_the_specification(self):
        data = example()
        p = load(data)
        self.assertEqual(len(p.devices), 16)
        self.assertEqual(len(p.connections), 14)
        # it is written back as it was read
        again = p.toDict()
        self.assertEqual(again["devices"], data["devices"])
        self.assertEqual(again["connections"], data["connections"])
        # the inverter has no type, so its ports are not known: no complaints
        self.assertEqual(check(p), [])

        breaker = p.byId("devices", "Q1")
        self.assertEqual((breaker.get("ratedCurrent"), breaker.get("poles"), breaker.get("switchesNeutral")), (32, 4, True))
        self.assertEqual(breaker.getPortNames(), ["in", "out"])
        self.assertEqual(p.byId("devices", "L").getPortNames(), ["bar"])
        meter = p.byId("devices", "M0")
        self.assertEqual(meter.get("ct"), {"primary": 120, "secondary": 0.04})
        self.assertEqual(meter.getPortNames(), [])

    def test_findings(self):
        p = load(example())
        inverterType = p.addPart("types", kind="inverter", specs={"mpptCount": 2, "ports": [
            {"name": "PV1", "kind": "dc", "connector": "MC4"}, {"name": "GRID", "kind": "ac"},
            {"name": "BAT", "kind": "dc", "connector": "SUNCLIX"}]})
        inverter = p.byId("devices", "INV")
        inverter.typeId = inverterType.id
        found = check(p)
        # the example uses BACKUP, BMS and PE, which this type doesn't list
        self.assertEqual(len([f for f in found if "hat keinen Anschluss" in f]), 3)

        battery = p.byId("devices", "BAT")
        p.byId("connections", "W10").ends[1]["connector"] = "MC4"
        self.assertTrue(any("verschiedene Stecker (MC4, SUNCLIX)" in f for f in check(p)))
        p.byId("connections", "W10").ends[1]["connector"] = "SUNCLIX"
        self.assertFalse(any("verschiedene Stecker" in f for f in check(p)))

        p.byId("connections", "W3").ends[1]["port"] = "top"
        self.assertTrue(any("hat keinen Anschluss 'top' (in, out)" in f for f in check(p)))
        p.byId("connections", "W4").ends.pop()
        self.assertTrue(any("braucht zwei Enden" in f for f in check(p)))
        p.byId("devices", "M0").get("measures")["connectionId"] = "W99"
        self.assertTrue(any("Kabel, das es nicht gibt" in f for f in check(p)))
        battery.set("connectedToId", "nothing")
        self.assertTrue(any("connectedToId zeigt auf nichts" in f for f in check(p)))
        p.byId("devices", "HV").parentId = "Q1"
        self.assertTrue(any("ist in sich selbst eingebaut" in f for f in check(p)))
        string = p.addPart("strings", inverterId="INV", mppt=3)
        self.assertTrue(any("MPPT 3, der Wechselrichter hat 2" in f for f in check(p)))

    def test_installed_on_a_date(self):
        # the example of section 17: an inverter replaced by a hybrid one
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "doc", "file_format.md")
        text = open(path, encoding="utf-8").read()
        block = re.search(r"```json\n(.*?)```", text[text.index("## 17. Example"):], re.S).group(1)
        data = json.loads(block)
        p = load(data["site"])
        self.assertEqual(p.toDict(), data["site"])
        self.assertEqual(check(p), [])
        installed = lambda day: [d.kind for d in p.devices if d.isInstalled(values.textToDate(day))]
        self.assertEqual(installed("2014-01-01"), [])
        self.assertEqual(installed("2020-01-01"), ["pv_array", "inverter"])
        self.assertEqual(installed("2026-12-01"), ["pv_array", "inverter", "battery"])
        self.assertEqual(p.devices[2].replacesId, p.devices[1].id)
        p.currentProject = p.projects[1]
        self.assertEqual((p.plant.batteryCapacity, p.existing.totalPowerDc), ("10.24", "6.24"))


if __name__ == "__main__":
    unittest.main()
