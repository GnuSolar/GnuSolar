#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The site window, without a screen: open a site, show every page,
# type into fields, save.

import os
import sys
import json
import time
import shutil
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import GnuSolar
import gui.tree
import gui.pages
import documents.templates
from Config import folderPreset
from tests.test_site import v2_text

app = None

# an exception in the window must fail the test, not open a dialog
sys.excepthook = sys.__excepthook__

# message boxes would wait for a click: collect their texts instead
messages = []
GnuSolar.QMessageBox.warning = lambda parent, title, text, *args: messages.append(text)
GnuSolar.QMessageBox.information = lambda parent, title, text, *args: messages.append(text)
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


# the input of a field of the page currently shown
def field(app, path):
    return app.currentForm.inputs[path]


# click a button of the page currently shown
def click(app, text):
    app.currentForm.buttons[text].click()


# created documents are not opened
opened = []
gui.pages.openFolderIfExists = opened.append


class ProjectWindowTest(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        GnuSolar.config.configPath = os.path.join(self.folder, "config.json")
        GnuSolar.config.templatePath = ""
        GnuSolar.config.folders = folderPreset("long")
        self.path = os.path.join(self.folder, "plant.pvp")
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(v2_text())
        self.app = window(self.path)

    def tearDown(self):
        shutil.rmtree(self.folder)

    def saved(self):
        return json.load(open(self.path, encoding="utf-8"))["site"]

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
        tree.setCurrentItem(find(self.app, "Projekt: PV-Anlage"))
        self.assertEqual(field(self.app, "commissioned").text(), "2026-06-20")
        self.run_action(tree.currentItem(), "Schritt hinzufügen", "Sicherheitsnachweis DC")
        field(self.app, "dates.ordered").setText("2026-06-21")
        self.assertTrue(self.app.unsavedChanges)
        self.assertEqual(GnuSolar.model.progress.siNaDcOrdered, "2026-06-21")

        # the power for the documents follows the module group
        self.assertEqual(GnuSolar.model.plant.totalPowerDc, "10.56")
        tree.setCurrentItem(find(self.app, "Modulgruppe"))
        field(self.app, "count").setText("26")
        self.assertEqual(GnuSolar.model.plant.totalPowerDc, "11.44")

        tree.setCurrentItem(find(self.app, "Kontakt (Bauherr)"))
        field(self.app, "lastName").setText("Beispiel")
        field(self.app, "email2").setText("zwei@example.ch")

        tree.setCurrentItem(find(self.app, "Adresse und Grundstück"))
        field(self.app, "mainFuseSize").setText("63")

        self.assertTrue(self.app.action_save())
        self.assertFalse(self.app.unsavedChanges)
        saved = self.saved()
        project = saved["projects"][0]
        self.assertEqual([s["dates"] for s in project["steps"] if s["kind"] == "ch.sina_dc"], [{"ordered": 1782043200}])
        self.assertEqual(saved["buildings"][0]["roofs"][0]["moduleGroups"][0]["count"], 26)
        self.assertEqual(saved["contacts"][0]["lastName"], "Beispiel")
        self.assertEqual(saved["contacts"][0]["channels"][-1], {"kind": "email", "value": "zwei@example.ch"})
        self.assertEqual(saved["supply"]["mainFuse"], 63)
        self.assertTrue(os.path.exists(self.path + ".v2"))

    def test_invalid_text_is_not_stored(self):
        tree = self.app.ui.tree
        tree.setCurrentItem(find(self.app, "Schritt: Technisches Anschlussgesuch"))
        tag = field(self.app, "dates.submitted")
        tag.setText("2026")
        self.assertNotEqual(tag.styleSheet(), "")
        self.assertEqual(GnuSolar.model.progress.tagSent, "2026-04-20")
        tag.setText("2026-04-22")
        self.assertEqual(tag.styleSheet(), "")
        self.assertEqual(GnuSolar.model.progress.tagSent, "2026-04-22")

    def test_today_button(self):
        from datetime import date
        tree = self.app.ui.tree
        tree.setCurrentItem(find(self.app, "Schritt: Installationsanzeige"))
        today = field(self.app, "dates.approved").parent().findChildren(GnuSolar.QtWidgets.QToolButton)
        self.assertEqual([b.text() for b in today], ["heute"])
        today[0].click()
        self.assertEqual(GnuSolar.model.progress.iaReceived, date.today().isoformat())
        self.assertEqual(self.app.currentObj.state, "approved")

    def test_contacts_menu(self):
        tree = self.app.ui.tree
        contacts = find(self.app, "Kontakte")
        before = contacts.childCount()
        self.run_action(contacts, "Kontakt hinzufügen", "Architekt")
        contacts = find(self.app, "Kontakte")
        self.assertEqual(contacts.childCount(), before + 1)
        self.assertEqual(self.app.currentObj.roles, ["architect"])
        field(self.app, "roles").setText("architect, planner")
        self.assertEqual(self.app.currentObj.roles, ["architect", "planner"])
        self.run_action(tree.currentItem(), "Löschen")
        self.assertEqual(find(self.app, "Kontakte").childCount(), before)

    # ---- pages and their buttons ------------------------------------------

    # a path that is no field of the part would be stored as an unknown field
    def test_fields_exist(self):
        import gui.fields
        from model.ModelNode import ModelNode
        tree = self.app.ui.tree
        seen = set()
        for item in items(tree.topLevelItem(0)):
            obj = item.pvpObj
            seen.add(type(obj).__name__)
            for title, fields in gui.fields.fieldsOf(obj):
                for f in fields:
                    key = f.path.split(".")[0]
                    known = isinstance(getattr(type(obj), key, None), property) or \
                        (isinstance(obj, ModelNode) and key in obj.__dict__)
                    # the fields of a kind of device are no attributes
                    if type(obj).__name__ == "Device":
                        known = known or key in [k[0].split(".")[0] for k in gui.fields.Device.KIND_FIELDS.get(obj.kind, [])]
                    self.assertTrue(known, type(obj).__name__ + "." + f.path)
        self.assertLessEqual({"PvSite", "Contact", "SiteView", "Municipality", "GridOperator", "Project"},
                             seen)
        # the summaries of file version 2 have no page any more
        self.assertFalse({"ProgressView", "PlantView"} & seen)

    def test_views_and_snapshots(self):
        tree = self.app.ui.tree
        site = GnuSolar.model
        tree.setCurrentItem(find(self.app, "Adresse und Grundstück"))
        state = field(self.app, "buildingState")
        state.setCurrentIndex(state.findData("existing"))
        self.assertEqual(site.building.buildingState, "existing")
        field(self.app, "swissGridX").setText("12")
        self.assertNotEqual(field(self.app, "swissGridX").styleSheet(), "")
        field(self.app, "swissGridX").setText("645000")
        self.assertEqual(field(self.app, "swissGridX").styleSheet(), "")
        self.assertEqual(site.ext["ch"]["lv95"]["e"], 2645000)

        tree.setCurrentItem(find(self.app, "Projekt: PV-Anlage"))
        fixed = field(self.app, "constructionFixed")
        fixed.setChecked(not fixed.isChecked())
        self.assertEqual(site.progress.constructionFixed, fixed.isChecked())
        field(self.app, "totalCost").setText("19'000")
        self.assertEqual(site.plant.totalCost, "19000")

        tree.setCurrentItem(find(self.app, "Gemeinde"))
        self.assertEqual(field(self.app, "name").text(), site.municipality.name or "")
        field(self.app, "website").setText("https://www.example.ch")
        self.assertEqual(site.municipality.website, "https://www.example.ch")

        tree.setCurrentItem(find(self.app, "Stromversorger"))
        field(self.app, "connectionContact.email").setText("tag@example.ch")
        self.assertEqual(site.powerCompany.tagContact.email, "tag@example.ch")

        tree.setCurrentItem(tree.topLevelItem(0))
        field(self.app, "comment").setPlainText("")
        self.assertEqual(site.notes, "")
        field(self.app, "comment").setPlainText("Hund im Garten")
        self.assertEqual(site.notes, "Hund im Garten")

    # a module group is added to the generator of the project and leaves it
    # when deleted
    def test_module_groups(self):
        tree = self.app.ui.tree
        site = GnuSolar.model
        array = [d for d in site.devices if d.kind == "pv_array"][0]
        first = site.allModuleGroups()[0]
        group = self.run_action(find(self.app, "Dach"), "Modulgruppe hinzufügen")
        self.assertEqual(array.get("moduleGroupIds"), [first.id, group.id])
        types = field(self.app, "typeId")
        types.setCurrentIndex(types.findData(first.typeId))
        field(self.app, "count").setText("4")
        self.assertEqual((site.plant.totalPanelCount, site.plant.totalPowerDc), ("28", "12.32"))

        # a string keeps its module group
        string = site.addPart("strings", moduleGroupId=group.id)
        self.run_action(tree.currentItem(), "Löschen")
        self.assertIn("Wird noch verwendet von:\nString", messages[-1])
        self.assertIn(group, site.allModuleGroups())
        site.removePart(string)
        self.run_action(find(self.app, "Modulgruppe: 4 x"), "Löschen")
        self.assertNotIn(group, site.allModuleGroups())
        self.assertEqual(array.get("moduleGroupIds"), [first.id])
        self.assertEqual(site.plant.totalPanelCount, "24")

        # a new site: the first module group makes the generator
        new = GnuSolar.PvSite()
        roof = new.addPart("buildings").addPart("roofs")
        only = roof.addPart("moduleGroups", count=10)
        device = new.addToGenerator(only)
        self.assertEqual((device.kind, device.projectId, device.get("moduleGroupIds")),
                         ("pv_array", new.currentProject.id, [only.id]))
        self.assertEqual(new.plant.totalPanelCount, "10")

    def test_field_buttons(self):
        tree = self.app.ui.tree
        calls = []
        gui.pages.callSip = lambda number, server: calls.append(number)
        gui.pages.composeEmail = lambda sender, to, *more: calls.append(to)
        gui.pages.openFolder = calls.append
        tree.setCurrentItem(find(self.app, "Kontakt (Bauherr)"))
        field(self.app, "mobile").setText("079 000 00 00")
        field(self.app, "email").setText("eins@example.ch")
        click(self.app, "Anruf mobile")
        click(self.app, "E-Mail email")
        tree.setCurrentItem(find(self.app, "Gemeinde"))
        field(self.app, "website").setText("https://www.example.ch")
        click(self.app, "Webseite öffnen website")
        self.assertEqual(calls, ["079 000 00 00", "eins@example.ch", "https://www.example.ch"])

    # a button which changes nothing doesn't mark the site as changed
    def test_page_buttons(self):
        tree = self.app.ui.tree
        site = GnuSolar.model
        tree.setCurrentItem(tree.topLevelItem(0))
        self.assertEqual(list(self.app.currentForm.buttons), ["Ordner öffnen", "Neues Projekt", "Standort prüfen"])
        click(self.app, "Ordner öffnen")
        self.assertEqual(opened[-1], self.folder)

        # the documents of a project are made on its page
        tree.setCurrentItem(find(self.app, "Projekt: PV-Anlage"))
        self.assertEqual(list(self.app.currentForm.buttons)[:6], [
            "neue Offerte", "Anlagedoku erstellen", "Akontorechnung", "Schlussrechnung", "Kleinrechnung",
            "QR Bill erstellen"])
        gui.pages.askTexts = lambda title, captions: None
        click(self.app, "QR Bill erstellen")
        self.assertFalse(self.app.unsavedChanges)

        # the page is built anew after a lookup
        tree.setCurrentItem(find(self.app, "Adresse und Grundstück"))
        self.assertEqual(list(self.app.currentForm.buttons),
                         ["Update von Adresse", "Get 3D Model", "Get Agis Ortho", "Get Agis Survey"])

        def lookup():
            site.building.plotNumber = "1234"
        site.updateFromAddress = lookup
        click(self.app, "Update von Adresse")
        self.assertTrue(self.app.unsavedChanges)
        self.assertEqual(tree.currentItem().text(0), "Adresse und Grundstück")
        self.assertEqual(field(self.app, "plotNumber").text(), "1234")

    def test_address_book_contact(self):
        from gui.forms import Form
        from model.Contact import Contact
        contact = Contact()
        form = Form(contact, fieldActions=gui.pages.createPage(contact, None).fieldActions)
        form.inputs["lastName"].setText("Muster")
        form.inputs["phone"].setText("061 000 00 00")
        form.inputs["address.city"].setText("Aarau")
        self.assertEqual((contact.lastName, contact.phone, contact.city), ("Muster", "061 000 00 00", "Aarau"))
        calls = []
        gui.pages.callSip = lambda number, server: calls.append(number)
        form.buttons["Anruf phone"].click()
        self.assertEqual(calls, ["061 000 00 00"])

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

    def test_second_project(self):
        tree = self.app.ui.tree
        site = GnuSolar.model
        project = self.run_action(tree.topLevelItem(0), "Neues Projekt", "Batterie")
        self.assertIs(project, site.projects[1])
        self.assertIs(site.currentProject, project)
        self.input("title").setText("Batterie 10 kWh")
        self.input("folder").setText("2026_Bat")
        self.input("inquiry").setText("2026-08-01")
        self.assertEqual(tree.currentItem().text(0), "Projekt: Batterie 10 kWh")
        self.assertEqual(self.input("state").text(), "inquiry")

        step = self.run_action(find(self.app, "Projekt: Batterie"), "Schritt hinzufügen", "Technisches Anschlussgesuch (TAG)")
        self.assertEqual((step.kind, step.state), ("ch.tag", "open"))
        self.input("dates.submitted").setText("2026-08-10")
        self.assertEqual(step.state, "submitted")
        self.assertEqual(self.input("state").text(), "submitted")
        self.input("dates.submitted").setText("10.8.26")
        self.assertNotEqual(self.input("dates.submitted").styleSheet(), "")
        self.assertEqual(step.dates, {"submitted": 1786363200})

        invoice = self.run_action(find(self.app, "Projekt: Batterie"), "Rechnung hinzufügen", "Schlussrechnung")
        self.input("amount").setText("12'800.00")
        self.assertEqual(invoice.amount, 12800)

        battery = self.run_action(find(self.app, "Projekt: Batterie"), "Gerät hinzufügen", "Batterie")
        self.assertEqual((battery.kind, battery.projectId), ("battery", project.id))
        self.input("coupling").setCurrentIndex(self.input("coupling").findData("dc_link"))
        inverter = [d for d in site.devices if d.kind == "inverter"][0]
        self.input("connectedToId").setCurrentIndex(self.input("connectedToId").findData(inverter.id))
        self.assertEqual(battery.get("coupling"), "dc_link")
        self.assertEqual(site.byId("devices", battery.get("connectedToId")).kind, "inverter")

        # the pages of the first project still show the first project
        tree.setCurrentItem(find(self.app, "Projekt: PV-Anlage").child(0))
        self.assertIs(site.currentProject, site.projects[0])
        self.assertEqual((site.plant.totalPowerDc, site.progress.inquiryReceived), ("10.56", "2026-03-01"))
        tree.setCurrentItem(find(self.app, "Projekt: Batterie").child(0))
        self.assertIs(site.currentProject, project)
        self.assertEqual((site.plant.totalPowerDc, site.progress.inquiryReceived), ("", "2026-08-01"))

        self.assertTrue(self.app.action_save())
        saved = self.saved()
        self.assertEqual([o["type"] for o in saved["projects"]], ["new_system", "battery"])
        self.assertEqual(saved["projects"][1]["folder"], "2026_Bat")
        self.assertEqual(saved["projects"][1]["steps"][0]["dates"], {"submitted": 1786363200})
        self.assertEqual(saved["projects"][1]["invoices"][0]["amount"], 12800)
        self.assertEqual(saved["devices"][-1]["coupling"], "dc_link")

        # a project with devices can not be deleted
        self.run_action(find(self.app, "Projekt: Batterie"), "Löschen")
        self.assertEqual(len(site.projects), 2)
        self.assertIn("Wird noch verwendet von:\nBatterie", messages[-1])

    def test_every_kind_of_part(self):
        tree = self.app.ui.tree
        site = GnuSolar.model
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
        self.assertEqual(site.designs[0].expectedYield, {"annual": 10200000})
        self.assertTrue(self.app.action_save())
        reloaded = GnuSolar.PvSite(self.path)
        self.assertEqual(len(reloaded.devices), len(site.devices))
        self.assertEqual(reloaded.buildings[1].roofs[0].obstacles[0].kind, "chimney")

    def test_electrical_installation(self):
        tree = self.app.ui.tree
        site = GnuSolar.model
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
        inverter = [d for d in site.devices if d.kind == "inverter"][0]
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

        self.run_action(tree.topLevelItem(0), "Standort prüfen")
        self.assertEqual(messages[-1], "Nichts gefunden: Verweise und Verbindungen sind in Ordnung.")
        tree.setCurrentItem(find(self.app, "Verbindung: ac"))
        self.input("ends.0.port").setText("top")
        self.run_action(tree.topLevelItem(0), "Standort prüfen")
        self.assertIn("hat keinen Anschluss 'top' (in, out)", messages[-1])
        self.assertFalse(self.app.currentObj is None)

        # a device with a cable can not be deleted
        self.run_action(find(self.app, "Leitungsschutzschalter: F1"), "Löschen")
        self.assertIn(fuse, site.devices)
        self.run_action(find(self.app, "Verbindung: ac"), "Löschen")
        self.run_action(find(self.app, "Leitungsschutzschalter: F1"), "Löschen")
        self.assertNotIn(fuse, site.devices)

    def test_documents_go_to_the_project(self):
        tree = self.app.ui.tree
        site = GnuSolar.model
        project = self.run_action(tree.topLevelItem(0), "Neues Projekt", "Batterie")
        # the first project works in the site folder, a later one gets a folder as a suggestion
        year = time.localtime().tm_year
        self.assertEqual([o.folder for o in site.projects], ["", "%d Batterie" % year])
        self.assertEqual(site.newProjectFolder("battery"), "%d Batterie 2" % year)
        self.assertEqual(os.listdir(self.folder), ["plant.pvp"])
        self.input("folder").setText("2026_Bat")
        self.assertIs(self.app.currentObj, project)

        click(self.app, "neue Offerte")
        self.assertIs(self.app.currentObj, project)
        number = os.path.splitext(os.path.basename(opened[-1]))[0]
        self.assertTrue(os.path.isfile(os.path.join(self.folder, "2026_Bat", "Offerten", number + ".odt")))
        quote = site.quotes[-1]
        self.assertEqual((quote.number, quote.state, quote.projectId, quote.date), (number, "draft", project.id, None))
        self.assertEqual(quote.documents, [{"path": "2026_Bat/Offerten/" + number + ".odt", "kind": "quote"}])
        self.assertTrue(self.app.unsavedChanges)
        self.assertEqual(project.deriveState(), "inquiry")
        # the date it was sent comes from the progress page
        site.progress.quote1Sent = "2026-08-05"
        self.assertEqual((quote.state, quote.date, project.deriveState()), ("sent", 1785931200, "quoted"))

        click(self.app, "Akontorechnung")
        invoice = project.invoices[0]
        self.assertEqual((invoice.kind, invoice.documents[0]["path"]),
                         ("partial", "2026_Bat/Rechnungen/" + invoice.number + ".odt"))
        site.progress.partialInvoiceSent = "2026-09-01"
        self.assertEqual(invoice.date, 1788264000)

        click(self.app, "Anlagedoku erstellen")
        step = project.getStep("documentation")
        self.assertEqual((step.state, step.documents[0]["path"]), ("open", "2026_Bat/Dokumentation/Dokumentation.odt"))
        self.assertIsNotNone(find(self.app, "Schritt: Dokumentation"))

        # the page of the first project makes the documents of the first project
        first = site.projects[0]
        tree.setCurrentItem(find(self.app, "Projekt: PV-Anlage"))
        count = len(first.invoices)
        click(self.app, "Akontorechnung")
        self.assertEqual((len(first.invoices), len(project.invoices)), (count + 1, 1))
        self.assertEqual(first.invoices[-1].documents[0]["path"], "Rechnungen/" + first.invoices[-1].number + ".odt")
        self.assertIs(self.app.currentObj, first)
        # also when the site thinks of another project
        site.currentProject = project
        click(self.app, "neue Offerte")
        self.assertEqual(site.quotes[-1].projectId, first.id)

    # the folders of the documents are named by the installer (Config.FOLDERS)
    def test_folder_names(self):
        config = GnuSolar.config
        tree = self.app.ui.tree
        site = GnuSolar.model

        def newQuote():
            tree.setCurrentItem(find(self.app, "Projekt: PV-Anlage"))
            click(self.app, "neue Offerte")
            return site.quotes[-1].documents[0]["path"], site.quotes[-1].number

        config.folders = folderPreset("short")
        path, number = newQuote()
        self.assertEqual(path, "off/" + number + ".odt")
        config.folders["quotes"] = "Verkauf/Offerten"
        path, number = newQuote()
        self.assertEqual(path, "Verkauf/Offerten/" + number + ".odt")
        self.assertTrue(os.path.isfile(os.path.join(self.folder, "Verkauf", "Offerten", number + ".odt")))
        # no name: the site folder itself
        config.folders["quotes"] = ""
        path, number = newQuote()
        self.assertEqual(path, number + ".odt")
        # a name that can't be used is not used: the preset of the other names
        config.folders["quotes"] = "../Offerten"
        path, number = newQuote()
        self.assertEqual(path, "off/" + number + ".odt")
        # documents created before stay where they are
        self.assertEqual(site.quotes[-4].documents[0]["path"], "off/" + site.quotes[-4].number + ".odt")

        # the installer's own templates lie in the folder of the same name
        used = []
        create = documents.templates.templateCopyReplace
        documents.templates.templateCopyReplace = lambda src, dest, model: (used.append(src), create(src, dest, model))
        try:
            newQuote()
            self.assertEqual(used[-1], os.path.join(documents.templates.DATA_PATH, "ch", "templates", "off", "quote.odt"))
            config.templatePath = os.path.join(self.folder, "vorlagen")
            config.folders["quotes"] = "Angebote"
            os.makedirs(os.path.join(config.templatePath, "Angebote"))
            own = os.path.join(config.templatePath, "Angebote", "quote.odt")
            shutil.copy(used[-1], own)
            path, number = newQuote()
            self.assertEqual((used[-1], path), (own, "Angebote/" + number + ".odt"))
        finally:
            documents.templates.templateCopyReplace = create

    def test_preferences_folders(self):
        config = GnuSolar.config
        self.app.action_preferences()
        ui = config.ui
        self.assertEqual((ui.folder_quotes.text(), ui.folder_gridOperator.text()), ("Offerten", "Netzbetreiber"))
        ui.folderPresetShort.click()
        self.assertEqual([getattr(ui, "folder_" + kind).text() for kind in GnuSolar.FOLDERS],
                         ["off", "fin", "doc", "evu", "gov", "cad", "gis", "sim", "pic", "etc"])
        ui.folderPresetLong.click()
        self.assertEqual(ui.folder_invoices.text(), "Rechnungen")
        ui.folder_invoices.setText(" Finanzen" + os.sep + "Rechnungen" + os.sep)
        ui.folder_authorities.setText("amt")
        ui.folder_plans.setText("../cad")
        ui.folder_maps.setText("")
        ui.buttonBox.button(GnuSolar.QtWidgets.QDialogButtonBox.Ok).click()
        self.assertEqual(config.folders, {
            "quotes": "Offerten", "invoices": "Finanzen/Rechnungen", "documentation": "Dokumentation",
            "gridOperator": "Netzbetreiber", "authorities": "amt", "plans": "Pläne", "maps": "",
            "simulation": "Simulation", "pictures": "Bilder", "misc": "Diverses"})
        self.assertIn('3D Modell: "../cad"', messages[-1])
        self.assertEqual(json.load(open(config.configPath, encoding="utf-8"))["folders"], config.folders)

    def test_replacement_device(self):
        site = GnuSolar.model
        old = [d for d in site.devices if d.kind == "inverter"][0]
        new = self.run_action(find(self.app, "Wechselrichter"), "Ersatzgerät hinzufügen")
        self.assertEqual((new.kind, new.replacesId, new.typeId), ("inverter", old.id, old.typeId))


if __name__ == "__main__":
    unittest.main()
