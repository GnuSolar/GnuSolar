#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
import os

sitepack = os.path.join(os.path.dirname(__file__), "site-packages")
sys.path.insert(0, sitepack)

import json
import codecs
import shutil
import traceback
import time
import io
import signal

from datetime import date
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QTableWidgetItem, QMessageBox, QFileDialog, QLineEdit, QPlainTextEdit, QComboBox, QCheckBox
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QWidget
from PyQt5 import QtCore, QtGui, QtWidgets

from Ui.GnuSolar import *
from Ui.Preferences import *

from Ui.PvProject import *
from Ui.Contacts import *
from Ui.Contact import *
from Ui.Building import *
from Ui.Plant import *
from Ui.Progress import *
from Ui.PowerCompany import *
from Ui.Municipality import *

from model.PvProject import *
from gui.binding import updateUi, updateModel, resolve, storeWidget
from gui.pages import createPage
from gui.forms import Form
import gui.tree

from model.Contact import Contact, ContactList
from model.Site import Municipality, GridOperator
from model.compat import SiteView, PlantView, ProgressView

# model class => generated form of its detail page
FORMS = {
    PvProject: Ui_PvProject,
    ContactList: Ui_Contacts,
    Contact: Ui_Contact,
    SiteView: Ui_Building,
    Municipality: Ui_Municipality,
    GridOperator: Ui_PowerCompany,
    ProgressView: Ui_Progress,
    PlantView: Ui_Plant,
}

from Config import *
from ErrorHandler import *

# exit application when CTRL-C pressed in command line
signal.signal(signal.SIGINT, signal.SIG_DFL)

# TODO: Where to put generally usefull functions?

from Usefull import *

# override QMainWindow, to catch unsaved changes
class MyMainWindow(QMainWindow):
	def closeEvent(self, event):
		app.action_quit()
		event.ignore()
    
class GnuSolar(QApplication):
    def __init__(self, *args):
        global config
        global model
        
        QApplication.__init__(self, *args)
        self.window = MyMainWindow()

        self.ui = Ui_GnuSolar()
        self.ui.setupUi(self.window)

        self.ui.action_New.triggered.connect(self.action_new)
        self.ui.action_Open.triggered.connect(self.action_open)
        self.ui.action_Save.triggered.connect(self.action_save)
        self.ui.action_Save_As.triggered.connect(self.action_saveAs)
        self.ui.action_Quit.triggered.connect(self.action_quit)
        self.ui.action_Preferences.triggered.connect(self.action_preferences)
        self.ui.action_Address_Book.triggered.connect(self.action_addressBook)

        self.ui.tree.currentItemChanged.connect(self.action_treeClicked)

        # Right click on tree
        self.ui.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.tree.customContextMenuRequested.connect(self.action_treeContext)

        
        # Arguments:
        #   First argument: Path to the Pv-Project File
        self.path = ""          # path = "" means new project
#        self.model = PvProject()       # the PvProject Model
        self.unsavedChanges = False

        #   Second argument: id of the order to show
        if len(args[0]) >= 2:
            path = args[0][1]
            ret = self.openFile(path, args[0][2] if len(args[0]) >= 3 else None)
            if not ret:
                QtWidgets.QMessageBox.warning(None, 'Datei nicht gefunden', "Datei '" + path + "' nicht gefunden.")
                exit()
        else:
            self.showModel()

        self.window.show()

    def action_new(self):
        QtWidgets.QMessageBox.information(None, 'Not implemented', 'Not implemented')

    def action_open(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self.window, "QFileDialog.getOpenFileName()", "", "Photovoltaic Project (*.pvp)", options=options)
        
        self.openFile(fileName)

    def action_save(self):
        if not self.path:
            return self.action_saveAs()
        return self.saveFile()

    def action_saveAs(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self.window, "QFileDialog.getSaveFileName()", "", "Photovoltaic Project (*.pvp)", options=options)
        if fileName == "":
            return False
        
        self.path = fileName
        return self.saveFile()

    # Ask to save unsaved changes. Returns False if the user cancelled
    # or saving failed, then the current project must stay open.
    def askSaveChanges(self, text):
        if not self.unsavedChanges:
            return True

        msgBox = QMessageBox()
        msgBox.setText(text)
        msgBox.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        msgBox.setDefaultButton(QMessageBox.Save)
        ret = msgBox.exec_()

        if ret == QMessageBox.Save:
            return bool(self.action_save())
        return ret == QMessageBox.Discard

    def action_quit(self):
        if not self.askSaveChanges("Änderungen vor dem Beenden speichern?"):
            return
        exit()

    def action_changed(self):
        if self.unsavedChanges:
            return
        self.unsavedChanges = True
        self.updateWindowTitle()

    def action_preferences(self):
        global config
        
        config.show()

    def action_addressBook(self):
        cmd = "python3 AddressBook.py &"
        print (cmd)
        os.system(cmd)

    # Update the attribute of the model
    def action_attributeChanged(self):
        el = self.sender()
        obj, name = resolve(self.currentObj, el.objectName())
        storeWidget(el, obj, name)

        # signal something changed
        self.action_changed()

    def action_treeClicked(self, item):
        # no item selected, e.g. while the tree is cleared
        if item is None:
            return

        obj = item.pvpObj

        # forms and documents work on the order the selected item belongs to
        order = gui.tree.orderOf(item)
        if order is not None and order is not model.currentOrder:
            model.currentOrder = order
        self.markCurrentOrder()

        self.clearDetails()
        self.currentObj = obj

        # parts without a hand-made form get a page made from their fields
        if type(obj) not in FORMS:
            self.currentForm = Form(obj, onChange=self.action_formChanged,
                                    actions=gui.tree.contextMenu(item), runAction=self.runTreeAction,
                                    text=getattr(obj, "text", None))
            self.ui.stackedWidget.addWidget(self.currentForm.widget)
            self.ui.stackedWidget.setCurrentWidget(self.currentForm.widget)
            return

        # load the ui into the detail window
        widget = QWidget()
        ui = FORMS[type(obj)]()
        ui.setupUi(widget)
        self.ui.stackedWidget.addWidget(widget)
        self.ui.stackedWidget.setCurrentWidget(widget)

        # Set the label
        label = item.text(0)
        if label and hasattr(ui, "groupBox"):
            ui.groupBox.setTitle(label)
       
        # fill it with the attributes of the object
        updateUi(ui, obj, "obj")
        
        # the page handles the buttons, keep it as long as it is shown
        self.currentPage = createPage(ui, obj, self)
        
        # connect all obj_ fields with attributeChanged
        # updates the model on the fly from the ui
        for key, value in ui.__dict__.items():
            if key.startswith("obj_"):
                el = getattr(ui, key)

                if isinstance(el, QLineEdit):
                    el.textChanged.connect(self.action_attributeChanged)
                elif isinstance(el, QPlainTextEdit):
                    el.textChanged.connect(self.action_attributeChanged)
                elif isinstance(el, QComboBox):
                    el.currentIndexChanged.connect(self.action_attributeChanged)
                elif isinstance(el, QCheckBox):
                    el.toggled.connect(self.action_attributeChanged)
                else:
                    raise Exception(str(type(el)) + " not implemented")

    # a field of a generated page was changed
    def action_formChanged(self, form, field):
        self.action_changed()
        item = self.ui.tree.currentItem()
        if item is None or item.pvpObj is not form.obj:
            return
        self.updateCaptions()
        # the fields of a device and of a type depend on its kind
        if field.path == "kind" and type(form.obj).__name__ in ("Device", "DeviceType"):
            QtCore.QTimer.singleShot(0, lambda: self.showObject(form.obj))

    # captions follow the values: "Auftrag: Batterie 10 kWh"
    def updateCaptions(self):
        if self.ui.tree.topLevelItemCount() == 0:
            return
        for item in gui.tree.allItems(self.ui.tree.topLevelItem(0)):
            text = gui.tree.itemCaption(item)
            if text != item.text(0):
                item.setText(0, text)

    # the order the forms and documents work on is shown bold
    def markCurrentOrder(self):
        if self.ui.tree.topLevelItemCount() == 0:
            return
        for item in gui.tree.allItems(self.ui.tree.topLevelItem(0)):
            if type(item.pvpObj).__name__ == "Order":
                font = item.font(0)
                font.setBold(item.pvpObj is model.currentOrder and len(model.orders) > 1)
                item.setFont(0, font)

    # display Context Menu of the Tree, entries and actions from gui.tree
    def action_treeContext(self, event):
        item = self.ui.tree.currentItem()
        if item is None:
            return
        actions = gui.tree.contextMenu(item)
        if not actions:
            return

        menu = QtWidgets.QMenu(self.ui.tree)
        self.fillMenu(menu, actions)
        chosen = menu.exec_(self.ui.tree.mapToGlobal(event))
        if chosen is not None:
            self.runTreeAction(chosen.treeAction)

    def fillMenu(self, menu, actions):
        for action in actions:
            if action.entries is not None:
                if action.entries:
                    self.fillMenu(menu.addMenu(action.text), action.entries)
            else:
                menu.addAction(action.text).treeAction = action

    # run an action of gui.tree and show what it made
    def runTreeAction(self, action):
        if action.confirm:
            ret = QMessageBox.question(self.window, 'GnuSolar', action.confirm, QMessageBox.Yes | QMessageBox.No)
            if ret != QMessageBox.Yes:
                return
        try:
            result = action.func()
        except gui.tree.Message as e:
            QMessageBox.information(self.window, 'GnuSolar', str(e))
            return
        except ValueError as e:
            QMessageBox.warning(self.window, 'GnuSolar', str(e))
            return
        self.action_changed()
        self.showModel(select=result)

    # open a Project with a path
    def openFile(self, pvpPath, orderId=None):
        global model
        if not pvpPath:
            return False

        # check if path exists
        if not os.path.isfile(pvpPath):
            return False

        # expand the path
        pvpPath = os.path.abspath(pvpPath)

        if not self.askSaveChanges("Änderungen speichern, bevor ein anderes Projekt geöffnet wird?"):
            return False

        # load into a new model, so nothing of the previous project remains
        newModel = PvProject()
        newModel.open(pvpPath)
        model = newModel
        order = model.byId("orders", orderId)
        if order is not None:
            model.currentOrder = order

        self.path = pvpPath
        self.unsavedChanges = False
        self.showModel(select=order)
        return True

    # remove the detail view of the previously selected tree item
    def clearDetails(self):
        self.currentObj = None
        self.currentPage = None
        self.currentForm = None
        while self.ui.stackedWidget.count():
            widget = self.ui.stackedWidget.widget(0)
            self.ui.stackedWidget.removeWidget(widget)
            widget.deleteLater()

    # show the current model: tree, details and window title. select is
    # the part to show the page of.
    def showModel(self, select=None):
        self.ui.tree.clear()
        self.clearDetails()
        gui.tree.buildTree(self.ui.tree, model)
        updateUi(self.ui, model, "pvp")
        self.updateWindowTitle()
        self.markCurrentOrder()
        if select is not None:
            self.showObject(select)

    # select the tree item of a part
    def showObject(self, obj):
        item = gui.tree.findItem(self.ui.tree, obj)
        if item is None:
            return
        if item is self.ui.tree.currentItem():
            self.action_treeClicked(item)
        else:
            self.ui.tree.setCurrentItem(item)
    
    def saveFile(self):
        global model
        updateModel(self.ui, model, "pvp")
        ret = model.saveAs(self.path)
        if not ret:
            # saving failed
            return False
        self.unsavedChanges = False
        self.updateWindowTitle()
        return True

    def updateWindowTitle(self):
        title = "Photovoltaic Project - " + Config.getAppVersion()
        if self.path != "":
            arr = os.path.split(self.path)
            file = arr[1]
            path = arr[0]
            title = file + " - " + path + " - " + title
        else:
            title = "untitled - " + title
        if self.unsavedChanges:
            title = "*" + title
        self.window.setWindowTitle(title)


def checkEnv():
    PY2 = sys.version_info[0] == 2
    # If we are on python 3 we will verify that the environment is
    # sane at this point of reject further execution to avoid a
    # broken script.
    if not PY2:
        try:
            import locale
            fs_enc = codecs.lookup(locale.getpreferredencoding()).name
        except Exception:
           fs_enc = 'ascii'
        if fs_enc == 'ascii':
            raise RuntimeError('GnuSolar will abort further execution '
                               'because Python 3 was configured to use '
                               'ASCII as encoding for the environment. '
                               'Either switch to Python 2 or consult '
                               'http://bugs.python.org/issue13643 '
                               'for mitigation steps.')

if __name__ == "__main__":
    checkEnv()
    config.load()
    app = GnuSolar(sys.argv)
    app.exec_()
    
