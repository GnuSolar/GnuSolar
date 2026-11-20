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
from gui.binding import updateUi, updateModel, comboValue
from gui.pages import createPage
import gui.tree

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
        # a document made by a button opens in another program, which then
        # has the focus; the tooltips (e.g. the template of a button) show
        # also while this window is not the active one
        self.window.setAttribute(QtCore.Qt.WA_AlwaysShowToolTips)

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
        #   --pos=X,Y: optional, place the window there (screen pixels)
        #   First other argument: Path to the Pv-Project File
        self.path = ""          # path = "" means new project
#        self.model = PvProject()       # the PvProject Model
        self.unsavedChanges = False

        argv = list(args[0])
        pos = next((a for a in argv[1:] if a.startswith("--pos=")), None)
        if pos:
            argv.remove(pos)

        if len(argv) >= 2:
            path = argv[1]
            ret = self.openFile(path)
            if not ret:
                QtWidgets.QMessageBox.warning(None, 'Datei nicht gefunden', "Datei '" + path + "' nicht gefunden.")
                exit()
        else:
            self.showModel()

        if pos:
            x, y = pos[len("--pos="):].split(",")
            self.moveWindow(int(x), int(y))
        self.window.show()

    # Place the window at x, y. It may reach past the edge of the screen, but
    # its top left part stays on it, so it can still be grabbed and moved.
    def moveWindow(self, x, y):
        screen = QApplication.screenAt(QtCore.QPoint(x, y)) or QApplication.primaryScreen()
        area = screen.availableGeometry()
        x = max(area.left(), min(x, area.right() - 200))
        y = max(area.top(), min(y, area.bottom() - 100))
        self.window.move(x, y)

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
        obj = self.currentObj

        if isinstance(el, QLineEdit):
            val = el.text()
        elif isinstance(el, QPlainTextEdit):
            val = el.toPlainText()
        elif isinstance(el, QComboBox):
            val = comboValue(el)
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
        # no item selected, e.g. while the tree is cleared
        if item is None:
            return

        obj = item.pvpObj
        class_name = type(obj).__name__

        # load the ui into the detail window
        widget = QWidget()
        klass = globals()["Ui_" + class_name]
        ui = klass()
        ui.setupUi(widget)
        self.clearDetails()
        self.currentObj = obj
        self.ui.stackedWidget.addWidget(widget)
        self.ui.stackedWidget.setCurrentWidget(widget)

        # Set the label
        label = gui.tree.caption(obj)
        if label and hasattr(ui, "groupBox"):
            ui.groupBox.setTitle(label)
       
        # the page handles the buttons, keep it as long as it is shown.
        # Created before the fields are filled, it fills the choices of
        # its combo boxes.
        self.currentPage = createPage(ui, obj, self)

        # fill it with the attributes of the object
        updateUi(ui, obj, "obj")
        
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

    # display Context Menu of the Tree, entries and actions from gui.tree
    def action_treeContext(self, event):
        item = self.ui.tree.currentItem()
        if item is None:
            return
        contextMenu = gui.tree.contextMenu(item)
        if not contextMenu:
            return

        menu = QtWidgets.QMenu(self.ui.tree)
        for key, value in contextMenu.items():
            actn = menu.addAction(value)
            actn.actionKey = key

        action = menu.exec_(self.ui.tree.mapToGlobal(event))
        if action is not None:
            gui.tree.treeAction(action.actionKey, item)

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

        if not self.askSaveChanges("Änderungen speichern, bevor ein anderes Projekt geöffnet wird?"):
            return False

        # load into a new model, so nothing of the previous project remains
        newModel = PvProject()
        newModel.open(pvpPath)
        model = newModel

        self.path = pvpPath
        self.unsavedChanges = False
        self.showModel()
        return True

    # remove the detail view of the previously selected tree item
    def clearDetails(self):
        self.currentObj = None
        self.currentPage = None
        while self.ui.stackedWidget.count():
            widget = self.ui.stackedWidget.widget(0)
            self.ui.stackedWidget.removeWidget(widget)
            widget.deleteLater()

    # show the current model: tree, details and window title
    def showModel(self):
        self.ui.tree.clear()
        self.clearDetails()
        gui.tree.buildTree(self.ui.tree, model)
        updateUi(self.ui, model, "pvp")
        self.updateWindowTitle()
    
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
    
