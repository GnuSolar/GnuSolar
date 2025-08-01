# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Ui/AddressBook.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_AddressBook(object):
    def setupUi(self, AddressBook):
        AddressBook.setObjectName("AddressBook")
        AddressBook.resize(773, 651)
        self.centralwidget = QtWidgets.QWidget(AddressBook)
        self.centralwidget.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.splitter = QtWidgets.QSplitter(self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.widget = QtWidgets.QWidget(self.splitter)
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.newContact = QtWidgets.QPushButton(self.widget)
        self.newContact.setObjectName("newContact")
        self.verticalLayout.addWidget(self.newContact)
        self.search = QtWidgets.QLineEdit(self.widget)
        self.search.setInputMask("")
        self.search.setText("")
        self.search.setPlaceholderText("")
        self.search.setObjectName("search")
        self.verticalLayout.addWidget(self.search)
        self.contactList = QtWidgets.QListWidget(self.widget)
        self.contactList.setObjectName("contactList")
        self.verticalLayout.addWidget(self.contactList)
        self.stackedWidget = QtWidgets.QStackedWidget(self.splitter)
        self.stackedWidget.setMinimumSize(QtCore.QSize(300, 0))
        self.stackedWidget.setObjectName("stackedWidget")
        self.horizontalLayout.addWidget(self.splitter)
        AddressBook.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(AddressBook)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 773, 23))
        self.menubar.setObjectName("menubar")
        self.menu_File = QtWidgets.QMenu(self.menubar)
        self.menu_File.setObjectName("menu_File")
        AddressBook.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(AddressBook)
        self.statusbar.setObjectName("statusbar")
        AddressBook.setStatusBar(self.statusbar)
        self.action_Quit = QtWidgets.QAction(AddressBook)
        self.action_Quit.setObjectName("action_Quit")
        self.menu_File.addAction(self.action_Quit)
        self.menubar.addAction(self.menu_File.menuAction())

        self.retranslateUi(AddressBook)
        self.stackedWidget.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(AddressBook)

    def retranslateUi(self, AddressBook):
        _translate = QtCore.QCoreApplication.translate
        AddressBook.setWindowTitle(_translate("AddressBook", "Address Book"))
        self.newContact.setText(_translate("AddressBook", "Neuer Kontakt"))
        self.menu_File.setTitle(_translate("AddressBook", "&File"))
        self.action_Quit.setText(_translate("AddressBook", "&Quit"))
        self.action_Quit.setShortcut(_translate("AddressBook", "Ctrl+Q"))
