#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The settings of the installer: the names of the folders in a project folder.

import os
import json
import tempfile
import unittest

import Config
from Config import folderPreset, folderNameError


class FolderNamesTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.getConfigDir = Config.Config.getConfigDir
        Config.Config.getConfigDir = lambda: self.tmp.name

    def tearDown(self):
        Config.Config.getConfigDir = self.getConfigDir
        self.tmp.cleanup()

    def stored(self):
        return json.load(open(os.path.join(self.tmp.name, "config.json"), encoding="utf-8"))

    def test_new_installation(self):
        config = Config.Config()
        config.load()
        self.assertEqual(config.folders, folderPreset("long"))
        self.assertEqual(config.getFolder("quotes"), "Offerten")
        self.assertEqual(self.stored()["folders"]["invoices"], "Rechnungen")

    # a config file from before the setting keeps the names GnuSolar used then
    def test_existing_installation(self):
        with open(os.path.join(self.tmp.name, "config.json"), "w") as f:
            json.dump({"projectRoot": "/somewhere", "nextQuoteNumber": 41}, f)
        config = Config.Config()
        config.load()
        self.assertEqual(config.folders, {"quotes": "off", "invoices": "fin", "documentation": "doc",
                                          "gridOperator": "evu", "authorities": "gov", "plans": "cad", "maps": "gis"})
        self.assertNotIn("folders", self.stored())
        config.useQuoteNumber()
        self.assertEqual(self.stored()["folders"]["quotes"], "off")

        # names of the installer are read back
        config.folders["quotes"] = "Angebote"
        config.write()
        config = Config.Config()
        config.load()
        self.assertEqual((config.getFolder("quotes"), config.getFolder("invoices")), ("Angebote", "fin"))

    def test_folder_path(self):
        config = Config.Config()
        config.folders = {"quotes": "Verkauf/Offerten", "invoices": "", "plans": "../cad", "maps": 7}
        project = os.path.join("root", "Ort", "Strasse 1")
        self.assertEqual(config.getFolderPath(project, "quotes"), os.path.join(project, "Verkauf", "Offerten"))
        self.assertEqual(config.getFolderPath(project, "invoices"), project)
        # a name that can't be used and a missing name: the written out name
        self.assertEqual(config.getFolderPath(project, "plans"), os.path.join(project, "Pläne"))
        self.assertEqual(config.getFolder("maps"), "Karten")
        self.assertEqual(config.getFolder("documentation"), "Dokumentation")

    def test_folder_name_error(self):
        for name in ("", "off", "Offerten 2026", "Finanzen/Rechnungen", "Behörden", "a.b"):
            self.assertIsNone(folderNameError(name), name)
        for name in ("..", "../off", "a/../b", "/off", "off/", "a//b", "C:off", "a\\b", "off?", " off", "off ", "off.", "."):
            self.assertIsNotNone(folderNameError(name), name)


if __name__ == "__main__":
    unittest.main()
