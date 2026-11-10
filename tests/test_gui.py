#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The project window, without a screen: open a project, show every page,
# type into fields, save.

import os
import sys
import json
import shutil
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QLineEdit

import GnuSolar
from tests.test_project import v2_text

app = None


def window(path):
    global app
    if app is None:
        app = GnuSolar.GnuSolar(["GnuSolar.py"])
        GnuSolar.app = app
    app.unsavedChanges = False
    assert app.openFile(path)
    return app


def items(item):
    yield item
    for i in range(item.childCount()):
        yield from items(item.child(i))


def find(app, text):
    for item in items(app.ui.tree.topLevelItem(0)):
        if item.text(0).startswith(text):
            return item
    raise KeyError(text)


# the field of the page currently shown
def field(app, name):
    return app.ui.stackedWidget.currentWidget().findChild(QLineEdit, name)


class ProjectWindowTest(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.path = os.path.join(self.folder, "plant.pvp")
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(v2_text())
        self.app = window(self.path)

    def tearDown(self):
        shutil.rmtree(self.folder)

    def saved(self):
        return json.load(open(self.path, encoding="utf-8"))["project"]

    def test_every_page_opens(self):
        tree = self.app.ui.tree
        count = 0
        for item in items(tree.topLevelItem(0)):
            tree.setCurrentItem(item)
            self.assertIs(self.app.currentObj, item.pvpObj)
            count += 1
        self.assertGreaterEqual(count, 12)
        self.assertFalse(self.app.unsavedChanges)

    def test_edit_and_save(self):
        tree = self.app.ui.tree
        tree.setCurrentItem(find(self.app, "Fortschritt"))
        self.assertEqual(field(self.app, "obj_launch").text(), "2026-06-20")
        field(self.app, "obj_siNaDcOrdered").setText("2026-06-21")
        self.assertTrue(self.app.unsavedChanges)

        tree.setCurrentItem(find(self.app, "Anlage"))
        self.assertEqual(field(self.app, "obj_totalPowerDc").text(), "10.56")
        field(self.app, "obj_totalPanelCount").setText("26")

        tree.setCurrentItem(find(self.app, "Kontakt (Bauherr)"))
        field(self.app, "obj_lastName").setText("Beispiel")
        field(self.app, "obj_email2").setText("zwei@example.ch")

        tree.setCurrentItem(find(self.app, "Gebäude"))
        field(self.app, "obj_mainFuseSize").setText("63")

        self.assertTrue(self.app.action_save())
        self.assertFalse(self.app.unsavedChanges)
        saved = self.saved()
        order = saved["orders"][0]
        self.assertEqual([s["dates"] for s in order["steps"] if s["kind"] == "ch.sina_dc"], [{"ordered": 1782043200}])
        self.assertEqual(saved["buildings"][0]["roofs"][0]["moduleGroups"][0]["count"], 26)
        self.assertEqual(saved["contacts"][0]["lastName"], "Beispiel")
        self.assertEqual(saved["contacts"][0]["channels"][-1], {"kind": "email", "value": "zwei@example.ch"})
        self.assertEqual(saved["site"]["supply"]["mainFuse"], 63)
        self.assertTrue(os.path.exists(self.path + ".v2"))

    def test_invalid_text_is_not_stored(self):
        tree = self.app.ui.tree
        tree.setCurrentItem(find(self.app, "Fortschritt"))
        tag = field(self.app, "obj_tagSent")
        tag.setText("2026")
        self.assertNotEqual(tag.styleSheet(), "")
        self.assertEqual(self.app.currentObj.tagSent, "2026-04-20")
        tag.setText("2026-04-22")
        self.assertEqual(tag.styleSheet(), "")
        self.assertEqual(self.app.currentObj.tagSent, "2026-04-22")

    def test_progress_button_sets_today(self):
        from datetime import date
        tree = self.app.ui.tree
        tree.setCurrentItem(find(self.app, "Fortschritt"))
        page = self.app.ui.stackedWidget.currentWidget()
        self.app.currentPage.ui.pb_iaReceived.click()
        self.assertEqual(self.app.currentObj.iaReceived, date.today().isoformat())

    def test_contacts_menu(self):
        import gui.tree
        tree = self.app.ui.tree
        contacts = find(self.app, "Kontakte")
        before = contacts.childCount()
        self.assertEqual(list(gui.tree.contextMenu(contacts)), ["contact_add"])
        gui.tree.treeAction("contact_add", contacts)
        self.assertEqual(contacts.childCount(), before + 1)
        new = contacts.child(before)
        tree.setCurrentItem(new)
        gui.tree.treeAction("contact_delete", new)
        self.assertEqual(contacts.childCount(), before)


if __name__ == "__main__":
    unittest.main()
