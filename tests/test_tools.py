#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# tools/: converting all projects, merging folder copies.

import os
import io
import json
import shutil
import tempfile
import unittest
import contextlib

from model.PvSite import PvSite
from tools import migrate_pvp, merge_copies
from tests import v2_example
from tests.test_site import v2_text


def quiet(func, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        ret = func(*args)
    return ret, out.getvalue()


class ToolsTest(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)

    def site(self, name, data=None):
        folder = os.path.join(self.root, name)
        os.makedirs(folder)
        with open(os.path.join(folder, "plant.pvp"), "w", encoding="utf-8") as f:
            f.write(v2_text(data))
        return folder

    def test_migrate_all(self):
        self.site("Musterwil/Kirchweg 26")
        self.site("Musterwil/Dorfstrasse 1")
        ret, out = quiet(migrate_pvp.main, [self.root])
        self.assertEqual(ret, 0, out)
        self.assertIn("files: 2, already current: 0, to convert: 2, errors: 0", out)
        self.assertIn("lost values: 0", out)
        self.assertIn("CHECK  Musterwil/Kirchweg 26: progress.iaSent", out)
        self.assertEqual(json.load(open(os.path.join(self.root, "Musterwil/Kirchweg 26/plant.pvp")))["version"], 2)

        backup = os.path.join(self.root, "backup.tar.gz")
        ret, out = quiet(migrate_pvp.main, [self.root, "--write", backup])
        self.assertEqual(ret, 0, out)
        self.assertTrue(os.path.isfile(backup))
        self.assertEqual(json.load(open(os.path.join(self.root, "Musterwil/Kirchweg 26/plant.pvp")))["version"], 3)
        ret, out = quiet(migrate_pvp.main, [self.root])
        self.assertIn("already current: 2, to convert: 0", out)

    def test_merge_copy(self):
        main = self.site("Musterwil/Kirchweg 26")
        second = v2_example.project()
        second["plant"].update({"panelDesc": "", "totalPanelCount": "", "totalPowerDc": "", "totalArea": "",
                                "inverterDesc": "Hybrid 10", "totalCost": "12800"})
        second["progress"] = {key: None for key in second["progress"]}
        second["progress"].update({"inquiryReceived": "2028-02-01", "orderReceived": "2028-03-01",
                                   "tagSent": "2028-03-05"})
        second["contacts"]["contacts"]["owner"]["email2"] = "neu@example.ch"
        second["comment"] = "Batterie nachrüsten"
        copy = self.site("Musterwil/Kirchweg 26_2", second)
        self.assertEqual(merge_copies.find_copies(self.root), [(main, copy)])

        (site,), out = quiet(lambda: (merge_copies.merge_folders(main, copy, False),))
        self.assertEqual(json.load(open(os.path.join(main, "plant.pvp")))["version"], 2)     # dry run
        ret, out = quiet(merge_copies.main, [main, copy, "--write"])
        self.assertEqual(ret, 0, out)
        self.assertIn("project added: PV-Anlage (running), folder ../Kirchweg 26_2", out)

        merged = PvSite(os.path.join(main, "plant.pvp"))
        self.assertEqual([o.folder for o in merged.projects], ["", "../Kirchweg 26_2"])
        self.assertEqual(len(merged.contacts), 1)                     # the same owner
        self.assertEqual([d.kind for d in merged.devices], ["pv_array", "inverter", "meter", "meter", "inverter"])
        self.assertEqual(merged.devices[-1].projectId, merged.projects[1].id)
        self.assertEqual(len(merged.types), 3)
        self.assertIn("--- ../Kirchweg 26_2 ---\nBatterie nachrüsten", merged.notes)
        merged.currentProject = merged.projects[1]
        self.assertEqual((merged.progress.tagSent, merged.plant.inverterDesc, merged.plant.totalPowerDc),
                         ("2028-03-05", "Hybrid 10", ""))
        self.assertEqual(merged.existing.totalPowerDc, "10.56")
        self.assertEqual(merged.getProjectDir(), os.path.join(main, "../Kirchweg 26_2"))
        self.assertTrue(os.path.isfile(os.path.join(main, "plant.pvp.before_merge")))
        self.assertTrue(os.path.isfile(os.path.join(copy, "plant.pvp.merged")))
        self.assertFalse(os.path.exists(os.path.join(copy, "plant.pvp")))

        # a second copy of the same site
        third = self.site("Musterwil/Kirchweg 26_3", second)
        ret, out = quiet(merge_copies.main, [main, third, "--write"])
        self.assertEqual(ret, 0, out)
        merged = PvSite(os.path.join(main, "plant.pvp"))
        self.assertEqual([o.folder for o in merged.projects], ["", "../Kirchweg 26_2", "../Kirchweg 26_3"])
        self.assertEqual(json.load(open(os.path.join(main, "plant.pvp.before_merge")))["version"], 2)


if __name__ == "__main__":
    unittest.main()
