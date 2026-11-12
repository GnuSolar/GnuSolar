#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The form scripts in data/: what they fill in for the project at hand.

import os
import shutil
import zipfile
import tempfile
import unittest

from model.PvSite import PvSite
from tests.test_site import v2_text


class ConnectionRequestTest(unittest.TestCase):

    def cells(self, path):
        with zipfile.ZipFile(path) as z:
            return z.read("xl/worksheets/sheet1.xml").decode("utf-8")

    def test_new_and_existing(self):
        folder = tempfile.mkdtemp()
        try:
            path = os.path.join(folder, "plant.pvp")
            with open(path, "w", encoding="utf-8") as f:
                f.write(v2_text())
            p = PvSite(path)
            p.powerCompany.fkFormTag = 4            # VSE TAG 2023
            from Config import config
            config.installer_signature = ""

            self.assertIsNone(p.powerCompany.createTag(p, os.path.join(folder, "new.xlsx")))
            new = self.cells(os.path.join(folder, "new.xlsx"))
            self.assertIn("Photovoltaik", new)
            self.assertNotIn("Elektrischer Energiespeicher 1", new)

            project = p.addProject("battery", "Batterie")
            batteryType = p.addPart("types", kind="battery", manufacturer="BYD", model="HVS 10.2",
                                    specs={"capacity": 10240, "powerDischarge": 10240})
            p.addPart("devices", kind="battery", projectId=project.id, typeId=batteryType.id, coupling="dc_link")
            self.assertIsNone(p.powerCompany.createTag(p, os.path.join(folder, "battery.xlsx")))
            battery = self.cells(os.path.join(folder, "battery.xlsx"))
            self.assertIn("Elektrischer Energiespeicher 1", battery)
            self.assertIn("HVS 10.2", battery)
            self.assertIn("DC (im DC Teil der Installation)", battery)
            self.assertNotIn("Photovoltaik", battery)
            # nothing of the form script stays on the model
            self.assertNotIn("fillxlsx_data", p.powerCompany.__dict__)
        finally:
            shutil.rmtree(folder)


if __name__ == "__main__":
    unittest.main()
