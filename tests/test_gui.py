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
import gui.tree
import gui.pages
from tests.test_project import v2_text

app = None

# an exception in the window must fail the test, not open a dialog
sys.excepthook = sys.__excepthook__

# message boxes would wait for a click: collect their texts instead
messages = []
GnuSolar.QMessageBox.warning = lambda parent, title, text, *args: messages.append(text)
GnuSolar.QMessageBox.question = lambda parent, title, text, *args: GnuSolar.QMessageBox.Yes


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


# created documents are not opened
opened = []
gui.pages.openFolderIfExists = opened.append


class ProjectWindowTest(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        GnuSolar.config.configPath = os.path.join(self.folder, "config.json")
        GnuSolar.config.templatePath = ""
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

        tree.setCurrentItem(find(self.app, "Standort"))
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
        tree = self.app.ui.tree
        contacts = find(self.app, "Kontakte")
        before = contacts.childCount()
        self.run_action(contacts, "Kontakt hinzufügen", "Architekt")
        contacts = find(self.app, "Kontakte")
        self.assertEqual(contacts.childCount(), before + 1)
        self.assertEqual(self.app.currentObj.roles, ["architect"])
        field(self.app, "obj_roles").setText("architect, planner")
        self.assertEqual(self.app.currentObj.roles, ["architect", "planner"])
        self.run_action(tree.currentItem(), "Löschen")
        self.assertEqual(find(self.app, "Kontakte").childCount(), before)

    # ---- the parts new with version 3 -------------------------------------

    # run the action of a tree item with these texts (menu, entry)
    def run_action(self, item, *texts):
        actions = gui.tree.contextMenu(item)
        for text in texts:
            action = [a for a in actions if a.text == text][0]
            actions = action.entries
        action.confirm = None
        self.app.runTreeAction(action)
        return self.app.currentObj

    # the input of a field of the generated page shown
    def input(self, path):
        return self.app.currentForm.inputs[path]

    def test_second_order(self):
        tree = self.app.ui.tree
        project = GnuSolar.model
        order = self.run_action(tree.topLevelItem(0), "Neuer Auftrag", "Batterie")
        self.assertIs(order, project.orders[1])
        self.assertIs(project.currentOrder, order)
        self.input("title").setText("Batterie 10 kWh")
        self.input("folder").setText("2026_Bat")
        self.input("inquiry").setText("2026-08-01")
        self.assertEqual(tree.currentItem().text(0), "Auftrag: Batterie 10 kWh")
        self.assertEqual(self.input("state").text(), "inquiry")

        step = self.run_action(find(self.app, "Auftrag: Batterie"), "Schritt hinzufügen", "Technisches Anschlussgesuch (TAG)")
        self.assertEqual((step.kind, step.state), ("ch.tag", "open"))
        self.input("dates.submitted").setText("2026-08-10")
        self.assertEqual(step.state, "submitted")
        self.assertEqual(self.input("state").text(), "submitted")
        self.input("dates.submitted").setText("10.8.26")
        self.assertNotEqual(self.input("dates.submitted").styleSheet(), "")
        self.assertEqual(step.dates, {"submitted": 1786363200})

        invoice = self.run_action(find(self.app, "Auftrag: Batterie"), "Rechnung hinzufügen", "Schlussrechnung")
        self.input("amount").setText("12'800.00")
        self.assertEqual(invoice.amount, 12800)

        battery = self.run_action(find(self.app, "Auftrag: Batterie"), "Gerät hinzufügen", "Batterie")
        self.assertEqual((battery.kind, battery.orderId), ("battery", order.id))
        self.input("coupling").setCurrentIndex(self.input("coupling").findData("dc_link"))
        inverter = [d for d in project.devices if d.kind == "inverter"][0]
        self.input("connectedToId").setCurrentIndex(self.input("connectedToId").findData(inverter.id))
        self.assertEqual(battery.get("coupling"), "dc_link")
        self.assertEqual(project.byId("devices", battery.get("connectedToId")).kind, "inverter")

        # the pages of the first order still show the first order
        tree.setCurrentItem(find(self.app, "Auftrag: PV-Anlage").child(1))
        self.assertIs(project.currentOrder, project.orders[0])
        self.assertEqual(field(self.app, "obj_totalPowerDc").text(), "10.56")
        tree.setCurrentItem(find(self.app, "Auftrag: Batterie").child(0))
        self.assertIs(project.currentOrder, order)
        self.assertEqual(field(self.app, "obj_inquiryReceived").text(), "2026-08-01")

        self.assertTrue(self.app.action_save())
        saved = self.saved()
        self.assertEqual([o["type"] for o in saved["orders"]], ["new_system", "battery"])
        self.assertEqual(saved["orders"][1]["folder"], "2026_Bat")
        self.assertEqual(saved["orders"][1]["steps"][0]["dates"], {"submitted": 1786363200})
        self.assertEqual(saved["orders"][1]["invoices"][0]["amount"], 12800)
        self.assertEqual(saved["devices"][-1]["coupling"], "dc_link")

        # an order with devices can not be deleted
        self.run_action(find(self.app, "Auftrag: Batterie"), "Löschen")
        self.assertEqual(len(project.orders), 2)
        self.assertIn("Wird noch verwendet von:\nBatterie", messages[-1])

    def test_every_kind_of_part(self):
        tree = self.app.ui.tree
        project = GnuSolar.model
        for kind in gui.tree.DEVICE_KINDS:
            device = self.run_action(find(self.app, "Geräte"), "Gerät hinzufügen", gui.tree.DEVICE_KINDS[kind])
            self.assertEqual(device.kind, kind)
        for kind in gui.tree.TYPE_KINDS:
            self.run_action(find(self.app, "Typen"), "Typ hinzufügen", gui.tree.TYPE_KINDS[kind])
        building = self.run_action(find(self.app, "Gebäude und Dächer"), "Gebäude hinzufügen")
        roof = self.run_action(tree.currentItem(), "Dach hinzufügen")
        self.input("outline").setText("0,0; 12000,0; 12000,6500; 0,6500")
        self.input("margins.eave").setText("200")
        self.input("azimuth").setText("185")
        self.assertEqual(roof.outline, [[0, 0], [12000, 0], [12000, 6500], [0, 6500]])
        self.assertEqual(roof.margins.eave, 200)
        roofItem = tree.currentItem()
        self.assertEqual(roofItem.text(0), "Dach: 185°")
        self.run_action(roofItem, "Hindernis hinzufügen", "chimney")
        self.run_action(find(self.app, "Dach: 185°"), "Modulgruppe hinzufügen")
        self.run_action(find(self.app, "Offerten"), "Offerte hinzufügen")
        self.run_action(find(self.app, "Auslegungen"), "Auslegung hinzufügen")
        self.input("expectedYield.annual").setText("10200000")
        self.run_action(find(self.app, "Umgebung"), "Umgebung hinzufügen", "tree")
        self.run_action(find(self.app, "Strings"), "String hinzufügen")
        self.run_action(find(self.app, "Verbindungen"), "Verbindung hinzufügen", "ac")
        count = 0
        for item in list(items(tree.topLevelItem(0))):
            tree.setCurrentItem(item)
            self.assertIs(self.app.currentObj, item.pvpObj)
            count += 1
        self.assertGreater(count, 70)
        self.assertEqual(project.designs[0].expectedYield, {"annual": 10200000})
        self.assertTrue(self.app.action_save())
        reloaded = GnuSolar.PvProject(self.path)
        self.assertEqual(len(reloaded.devices), len(project.devices))
        self.assertEqual(reloaded.buildings[1].roofs[0].obstacles[0].kind, "chimney")

    def test_electrical_installation(self):
        tree = self.app.ui.tree
        project = GnuSolar.model
        board = self.run_action(find(self.app, "Geräte"), "Gerät hinzufügen", "Verteilung")
        self.input("label").setText("Hauptverteilung")
        fuse = self.run_action(tree.currentItem(), "Eingebautes Gerät hinzufügen", "Sicherung")
        self.assertEqual(fuse.parentId, board.id)
        self.assertIs(tree.currentItem().parent().pvpObj, board)
        self.input("label").setText("F1")
        self.input("ratedCurrent").setText("40")
        self.input("characteristic").setText("gG")
        self.input("form").setText("nh00")
        self.input("poles").setText("3")
        self.assertEqual((fuse.get("ratedCurrent"), fuse.get("characteristic"), fuse.get("form"), fuse.get("poles")),
                         (40, "gG", "nh00", 3))
        # changing the kind changes the fields
        self.input("kind").setCurrentIndex(self.input("kind").findData("breaker"))
        GnuSolar.QtCore.QCoreApplication.processEvents()
        self.assertIn("switchesNeutral", self.app.currentForm.inputs)
        self.input("switchesNeutral").setChecked(True)
        self.assertIs(fuse.get("switchesNeutral"), True)

        connection = self.run_action(find(self.app, "Verbindungen"), "Verbindung hinzufügen", "ac")
        inverter = [d for d in project.devices if d.kind == "inverter"][0]
        self.input("ends.0.deviceId").setCurrentIndex(self.input("ends.0.deviceId").findData(fuse.id))
        self.input("ends.0.port").setText("out")
        self.input("ends.1.deviceId").setCurrentIndex(self.input("ends.1.deviceId").findData(inverter.id))
        self.input("ends.1.port").setText("GRID")
        self.input("conductors").setText("L1, L2, L3, N, PE")
        self.input("cable.designation").setText("5G6")
        self.input("cable.crossSection").setText("6")
        self.input("cable.length").setText("8000")
        self.assertEqual(connection.toDict(), {
            "id": connection.id, "kind": "ac",
            "ends": [{"deviceId": fuse.id, "port": "out"}, {"deviceId": inverter.id, "port": "GRID"}],
            "conductors": ["L1", "L2", "L3", "N", "PE"],
            "cable": {"designation": "5G6", "crossSection": 6, "length": 8000}})
        self.assertEqual(tree.currentItem().text(0), "Verbindung: ac F1.out – Wechselrichter: Fronius Symo 10.0-3-M.GRID")

        # a device with a cable can not be deleted
        self.run_action(find(self.app, "Leitungsschutzschalter: F1"), "Löschen")
        self.assertIn(fuse, project.devices)
        self.run_action(find(self.app, "Verbindung: ac"), "Löschen")
        self.run_action(find(self.app, "Leitungsschutzschalter: F1"), "Löschen")
        self.assertNotIn(fuse, project.devices)

    def test_documents_go_to_the_order(self):
        tree = self.app.ui.tree
        project = GnuSolar.model
        order = self.run_action(tree.topLevelItem(0), "Neuer Auftrag", "Batterie")
        self.input("folder").setText("2026_Bat")
        tree.setCurrentItem(tree.topLevelItem(0))
        self.assertIs(project.currentOrder, order)

        self.app.currentPage.ui.createQuote.click()
        number = os.path.splitext(os.path.basename(opened[-1]))[0]
        self.assertTrue(os.path.isfile(os.path.join(self.folder, "2026_Bat", "off", number + ".odt")))
        quote = project.quotes[-1]
        self.assertEqual((quote.number, quote.state, quote.orderId, quote.date), (number, "draft", order.id, None))
        self.assertEqual(quote.documents, [{"path": "2026_Bat/off/" + number + ".odt", "kind": "quote"}])
        self.assertTrue(self.app.unsavedChanges)
        self.assertEqual(order.deriveState(), "inquiry")
        # the date it was sent comes from the progress page
        project.progress.quote1Sent = "2026-08-05"
        self.assertEqual((quote.state, quote.date, order.deriveState()), ("sent", 1785931200, "quoted"))

        self.app.currentPage.ui.createPartialInvoice.click()
        invoice = order.invoices[0]
        self.assertEqual((invoice.kind, invoice.documents[0]["path"]),
                         ("partial", "2026_Bat/fin/" + invoice.number + ".odt"))
        project.progress.partialInvoiceSent = "2026-09-01"
        self.assertEqual(invoice.date, 1788264000)

        self.app.currentPage.ui.createDocumentation.click()
        step = order.getStep("documentation")
        self.assertEqual((step.state, step.documents[0]["path"]), ("open", "2026_Bat/doc/Dokumentation.odt"))
        self.assertIsNotNone(find(self.app, "Schritt: Dokumentation"))

    def test_replacement_device(self):
        project = GnuSolar.model
        old = [d for d in project.devices if d.kind == "inverter"][0]
        new = self.run_action(find(self.app, "Wechselrichter"), "Ersatzgerät hinzufügen")
        self.assertEqual((new.kind, new.replacesId, new.typeId), ("inverter", old.id, old.typeId))


if __name__ == "__main__":
    unittest.main()
