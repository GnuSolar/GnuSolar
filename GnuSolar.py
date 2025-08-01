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

from relatorio.templates.opendocument import Template

import tempfile
from qrbill import QRBill
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

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

from Config import *
from ErrorHandler import *

# TODO: Where to put generally usefull functions?

from Usefull import *

def templateCopyReplace(src, dest, model):
    # print("templateCopyReplace: src:" + src + " dest:" + dest)
    basic = Template(source='', filepath=src)
    basic_generated = basic.generate(o=model, c=model.contacts).render()

    f = open(dest, 'wb')
    f.write(basic_generated.getvalue())
    f.close()

def createFromTemplate(templateType, savePath, model):
    global config
    templates = {
        "partial_invoice" : {
            "in_path"  : "fin" + os.sep + "partial_invoice.odt",
            "out_dir"  : "fin",
            "out_file" : config.getNextInvoiceName() + ".odt"
        },
        "final_invoice" : {
            "in_path"  : "fin" + os.sep + "final_invoice.odt",
            "out_dir"  : "fin",
            "out_file" : config.getNextInvoiceName() + ".odt"
        },
        "small_invoice" : {
            "in_path"  : "fin" + os.sep + "small_invoice.odt",
            "out_dir"  : "fin",
            "out_file" : config.getNextInvoiceName() + ".odt"
        },
        "quote" : {
            "in_path"  : "off" + os.sep + "quote.odt",
            "out_dir"  : "off",
            "out_file" : config.getNextQuoteName() + ".odt"
        },
        "documentation" : {
            "in_path"  : "doc" + os.sep + "documentation.odt",
            "out_dir"  : "doc",
            "out_file" : "Dokumentation.odt"
        },
        "mundpp" : {
            "in_path"  : "evu" + os.sep + "MP_PV_Final_20190301_de.ods",
            "out_dir"  : "evu",
            "out_file" : "MP_PV.ods"
        }
    }

    if not savePath:
        QtWidgets.QMessageBox.warning(None, templateType + ' erstellen', 'Kein Pfad')
        return

    ret = Config.getDataPath() + os.sep + "ch" + os.sep + "templates"

    template = templates[templateType]
    
    templatePath = ""
    defaultPath = Config.getDataPath() + os.sep + "ch" + os.sep + "templates" + os.sep + template["in_path"]
    localPath = config.templatePath + os.sep + template["in_path"]
    # first search template in  "local", config path
    if os.path.exists(localPath):
        templatePath = localPath

    # then default
    elif os.path.exists(defaultPath):
        templatePath = defaultPath
    else:
        QtWidgets.QMessageBox.warning(None, templateType + ' Vorlage nicht gefunden', 'def Pfad = ' + defaultPath)
        return
    
    projectDir = os.path.dirname(savePath)
    if not os.path.isdir(projectDir):
        QtWidgets.QMessageBox.warning(None, templateType + ' erstellen', 'Pfad nicht gefunden\n' + savePath)
        return

    outDir =  projectDir + os.sep + template["out_dir"]
    outPath = outDir + os.sep + template["out_file"]
    if not os.path.isdir(outDir):
        os.makedirs(outDir)

    # dot not overwrite existing files
    if os.path.exists(outPath):
        QtWidgets.QMessageBox.warning(None, templateType + ' erstellen', 'Datei existiert bereits:\n' + outPath)
        return

    model._invoiceName = config.getNextInvoiceName()
    model._quoteName = config.getNextQuoteName()
    today = date.today()
    model._todayIso = today.isoformat()
    model.owner = model.contacts.owner		# backwards compatibility
    model.config = config
    templateCopyReplace(templatePath, outPath, model)
    del model.config
    del model.owner
    del model._invoiceName
    del model._quoteName
    del model._todayIso
    
    return outPath

    
class GnuSolar(QApplication):
    def __init__(self, *args):
        global config
        global model
        
        QApplication.__init__(self, *args)
        self.window = QMainWindow()

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

        if len(args[0]) >= 2:
            path = args[0][1]
            ret = self.openFile(path)
            if not ret:
                QtWidgets.QMessageBox.warning(None, 'Datei nicht gefunden', "Datei '" + path + "' nicht gefunden.")
                exit()


        self.unsavedChanges = False
        self.updateWindowTitle()
        GnuSolar.updateTree(self.ui, model)
        GnuSolar.updateUi(self.ui, model, "pvp")
        
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

    def action_quit(self):
        if self.unsavedChanges:
            msgBox = QMessageBox()
            msgBox.setText("Änderungen vor dem Beenden speichern?")
            msgBox.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            msgBox.setDefaultButton(QMessageBox.Save)
            ret = msgBox.exec_()

            # Check which button was clicked
            if ret == QMessageBox.Save:
                ret2 = self.action_save()
                if not ret2:
                    # if file was not saved dont quit
                    return
                exit()
            elif ret == QMessageBox.Discard:
                exit()
            elif ret == QMessageBox.Cancel:
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
        obj = self.currentObj

        if isinstance(el, QLineEdit):
            val = el.text()
        elif isinstance(el, QPlainTextEdit):
            val = el.toPlainText()
        elif isinstance(el, QComboBox):
            val = el.currentText()
        elif isinstance(el, QCheckBox):
            val = el.isChecked()
        else:
            raise Exception(str(type(el)) + " not implemented")

        att_name = el.objectName()
        att_name = att_name[4:]         # remove obj_ from the start
        obj.__dict__[att_name] = val
        
        # signal something changed
        self.action_changed()
        
    def action_treeClicked(self, item):
        obj = item.pvpObj
        class_name = type(obj).__name__
        
        # load the ui into the detail window
        widget = QWidget()
        klass = globals()["Ui_" + class_name]
        ui = klass()
        ui.setupUi(widget)
        self.currentObj = obj
        self.ui.stackedWidget.addWidget(widget)
        self.ui.stackedWidget.setCurrentWidget(widget)

        # Set the label
        try:
            label = obj.getTreeCaption()
            ui.groupBox.setTitle(label)
        except AttributeError:
            pass
       
        # fill it with the attributes of the object
        GnuSolar.updateUi(ui, obj, "obj")
        
        # hook for ui initializiation
        obj.initUi(ui)
        
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

    # display Context Menu of the Tree
    # gets them from the getTreeContextMenu
    # calls the treeAction
    def action_treeContext(self, event):
        item = self.ui.tree.currentItem()
        obj = item.pvpObj

        menu = QtWidgets.QMenu(self.ui.tree)
        try:
            contextMenu = obj.getTreeContextMenu()
        except AttributeError:
            return
            
        for key, value in contextMenu.items():
            actn = menu.addAction(value)
            actn.actionKey = key
        
        action = menu.exec_(self.ui.tree.mapToGlobal(event))
        if action is not None:
            obj.treeAction(action, item)
        
    # open a Project with a path
    def openFile(self, pvpPath):
        global model
        if not pvpPath:
            return False
            
        # check if path exists
        if not os.path.isfile(pvpPath):
            return False
        
        # expand the path
        pvpPath = os.path.abspath(pvpPath)

        # valid pvp Project?
        self.path = pvpPath
        model.open(pvpPath)
        GnuSolar.updateUi(self.ui, model, "pvp")
        self.updateWindowTitle()
        return True
    
    def saveFile(self):
        global model
        self.updateModel(self.ui, model, "pvp")
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

    # Populates the UI Tree View from the data model
    @staticmethod
    def updateTree(ui, model):
        tree = ui.tree
        tree.setColumnCount(1)
        
        # Iterate trhough the model and populate the treeview
        top = QTreeWidgetItem(None, ["PV-Anlage"])
        top.pvpObj = model
        GnuSolar.addTreeItems(model, top)
        items = [top]
        tree.addTopLevelItems(items)
        tree.expandAll()
    
    @staticmethod
    def addTreeItems(modelObj, parent):
        for key, value in modelObj.__dict__.items():
            if key == "config" or key[0]=="_":
                continue
            
            # Loop over all dictionary element
            if isinstance(value, dict):
                for k,v in value.items():
                    if hasattr(v, "__dict__") and isinstance(v.__dict__, dict):
                        el = value[k]
                        caption = str(k)
                        try:
                            caption = el.getTreeCaption()
                        except AttributeError:
                            pass
                        item = QTreeWidgetItem(None, [caption])
                        item.pvpObj = el
                        parent.addChild(item)
                        GnuSolar.addTreeItems(el, item)
            
            # recurse into child objects
            if hasattr(value, "__dict__") and isinstance(value.__dict__, dict):
                el = getattr(modelObj, key)
                caption = str(key)
                try:
                    caption = el.getTreeCaption()
                except AttributeError:
                    pass
                item = QTreeWidgetItem(None, [caption])
                item.pvpObj = el
                parent.addChild(item)
                GnuSolar.addTreeItems(el, item)

    # Updates the User Interface from the Model
    # Iterates through all widgets and searches for pvp_* named Widgets
    @staticmethod
    def updateUi(ui, obj, prefix):
        for key, value in ui.__dict__.items():
            # normal model<=>ui element?
            if key.startswith(prefix + "_"):
                attrs = key.split("_")
                attrs.pop(0)

                modelEl = obj
                for attr in attrs:
                    modelEl = getattr(modelEl, attr)
                uiEl = getattr(ui, key)

                if isinstance(uiEl, QLineEdit):
                    uiEl.setText(modelEl)
                elif isinstance(uiEl, QPlainTextEdit):
                    uiEl.setPlainText(modelEl)
                elif isinstance(uiEl, QComboBox):
                    uiEl.setCurrentText(modelEl)
                elif isinstance(uiEl, QCheckBox):
                    uiEl.setChecked(modelEl)
                else:
                    raise Exception(str(type(uiEl)) + " not implemented")

    # Updates the Data Model from the User Interface
    # Iterates through all widgets and searches for pvp_* named Widgets
    def updateModel(self, ui, obj, prefix):
        for key, value in ui.__dict__.items():
            if not key.startswith(prefix + "_"):
                continue
            
            attrs = key.split("_")
            attrs.pop(0)
            last = attrs.pop()
            
            modelEl = obj
            for attr in attrs:
                modelEl = getattr(modelEl, attr)
            uiEl = getattr(ui, key)

            if isinstance(uiEl, QLineEdit):
                setattr(modelEl, last, uiEl.text())
            elif isinstance(uiEl, QPlainTextEdit):
                setattr(modelEl, last, uiEl.toPlainText())
            elif isinstance(uiEl, QComboBox):
                setattr(modelEl, last, uiEl.currentText())
            elif isinstance(uiEl, QCheckBox):
                setattr(modelEl, last, uiEl.isChecked())
            else:
                raise Exception(str(type(uiEl)) + " not implemented")

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
    
