# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Ui/Preferences.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Preferences(object):
    def setupUi(self, Preferences):
        Preferences.setObjectName("Preferences")
        Preferences.resize(623, 623)
        Preferences.setModal(True)
        self.formLayoutWidget = QtWidgets.QWidget(Preferences)
        self.formLayoutWidget.setGeometry(QtCore.QRect(10, 30, 581, 161))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setObjectName("formLayout")
        self.projectDirectoryLabel = QtWidgets.QLabel(self.formLayoutWidget)
        self.projectDirectoryLabel.setObjectName("projectDirectoryLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.projectDirectoryLabel)
        self.projectRoot = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.projectRoot.setObjectName("projectRoot")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.projectRoot)
        self.projectDirectoryWidget = QtWidgets.QWidget(self.formLayoutWidget)
        self.projectDirectoryWidget.setObjectName("projectDirectoryWidget")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.projectDirectoryWidget)
        self.projectDirectoryLabel_2 = QtWidgets.QLabel(self.formLayoutWidget)
        self.projectDirectoryLabel_2.setObjectName("projectDirectoryLabel_2")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.projectDirectoryLabel_2)
        self.templatePath = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.templatePath.setObjectName("templatePath")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.templatePath)
        self.projectDirectoryLabel_3 = QtWidgets.QLabel(self.formLayoutWidget)
        self.projectDirectoryLabel_3.setObjectName("projectDirectoryLabel_3")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.projectDirectoryLabel_3)
        self.projectDirectoryLabel_4 = QtWidgets.QLabel(self.formLayoutWidget)
        self.projectDirectoryLabel_4.setObjectName("projectDirectoryLabel_4")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.projectDirectoryLabel_4)
        self.nextQuoteNumber = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.nextQuoteNumber.setObjectName("nextQuoteNumber")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.nextQuoteNumber)
        self.nextInvoiceNumber = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.nextInvoiceNumber.setObjectName("nextInvoiceNumber")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.nextInvoiceNumber)
        self.buttonBox = QtWidgets.QDialogButtonBox(Preferences)
        self.buttonBox.setGeometry(QtCore.QRect(60, 560, 549, 36))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.groupBox = QtWidgets.QGroupBox(Preferences)
        self.groupBox.setGeometry(QtCore.QRect(10, 200, 601, 351))
        self.groupBox.setObjectName("groupBox")
        self.installer_company = QtWidgets.QLineEdit(self.groupBox)
        self.installer_company.setGeometry(QtCore.QRect(170, 30, 414, 27))
        self.installer_company.setObjectName("installer_company")
        self.projectDirectoryLabel_5 = QtWidgets.QLabel(self.groupBox)
        self.projectDirectoryLabel_5.setGeometry(QtCore.QRect(5, 30, 134, 27))
        self.projectDirectoryLabel_5.setObjectName("projectDirectoryLabel_5")
        self.projectDirectoryLabel_6 = QtWidgets.QLabel(self.groupBox)
        self.projectDirectoryLabel_6.setGeometry(QtCore.QRect(5, 60, 134, 27))
        self.projectDirectoryLabel_6.setObjectName("projectDirectoryLabel_6")
        self.installer_firstName = QtWidgets.QLineEdit(self.groupBox)
        self.installer_firstName.setGeometry(QtCore.QRect(170, 60, 201, 27))
        self.installer_firstName.setObjectName("installer_firstName")
        self.installer_lastName = QtWidgets.QLineEdit(self.groupBox)
        self.installer_lastName.setGeometry(QtCore.QRect(380, 60, 201, 27))
        self.installer_lastName.setObjectName("installer_lastName")
        self.projectDirectoryLabel_8 = QtWidgets.QLabel(self.groupBox)
        self.projectDirectoryLabel_8.setGeometry(QtCore.QRect(5, 90, 134, 27))
        self.projectDirectoryLabel_8.setObjectName("projectDirectoryLabel_8")
        self.installer_street = QtWidgets.QLineEdit(self.groupBox)
        self.installer_street.setGeometry(QtCore.QRect(170, 90, 271, 27))
        self.installer_street.setObjectName("installer_street")
        self.projectDirectoryLabel_9 = QtWidgets.QLabel(self.groupBox)
        self.projectDirectoryLabel_9.setGeometry(QtCore.QRect(5, 120, 134, 27))
        self.projectDirectoryLabel_9.setObjectName("projectDirectoryLabel_9")
        self.installer_zip = QtWidgets.QLineEdit(self.groupBox)
        self.installer_zip.setGeometry(QtCore.QRect(170, 120, 121, 27))
        self.installer_zip.setObjectName("installer_zip")
        self.installer_city = QtWidgets.QLineEdit(self.groupBox)
        self.installer_city.setGeometry(QtCore.QRect(300, 120, 281, 27))
        self.installer_city.setObjectName("installer_city")
        self.projectDirectoryLabel_11 = QtWidgets.QLabel(self.groupBox)
        self.projectDirectoryLabel_11.setGeometry(QtCore.QRect(5, 150, 134, 27))
        self.projectDirectoryLabel_11.setObjectName("projectDirectoryLabel_11")
        self.installer_phone = QtWidgets.QLineEdit(self.groupBox)
        self.installer_phone.setGeometry(QtCore.QRect(170, 150, 414, 27))
        self.installer_phone.setObjectName("installer_phone")
        self.installer_streetNumber = QtWidgets.QLineEdit(self.groupBox)
        self.installer_streetNumber.setGeometry(QtCore.QRect(450, 90, 131, 27))
        self.installer_streetNumber.setObjectName("installer_streetNumber")
        self.projectDirectoryLabel_12 = QtWidgets.QLabel(self.groupBox)
        self.projectDirectoryLabel_12.setGeometry(QtCore.QRect(5, 180, 134, 27))
        self.projectDirectoryLabel_12.setObjectName("projectDirectoryLabel_12")
        self.installer_email = QtWidgets.QLineEdit(self.groupBox)
        self.installer_email.setGeometry(QtCore.QRect(170, 180, 414, 27))
        self.installer_email.setObjectName("installer_email")
        self.installer_bankName = QtWidgets.QLineEdit(self.groupBox)
        self.installer_bankName.setGeometry(QtCore.QRect(170, 250, 414, 27))
        self.installer_bankName.setObjectName("installer_bankName")
        self.projectDirectoryLabel_13 = QtWidgets.QLabel(self.groupBox)
        self.projectDirectoryLabel_13.setGeometry(QtCore.QRect(5, 250, 134, 27))
        self.projectDirectoryLabel_13.setObjectName("projectDirectoryLabel_13")
        self.installer_bankIban = QtWidgets.QLineEdit(self.groupBox)
        self.installer_bankIban.setGeometry(QtCore.QRect(170, 280, 414, 27))
        self.installer_bankIban.setObjectName("installer_bankIban")
        self.projectDirectoryLabel_14 = QtWidgets.QLabel(self.groupBox)
        self.projectDirectoryLabel_14.setGeometry(QtCore.QRect(5, 280, 134, 27))
        self.projectDirectoryLabel_14.setObjectName("projectDirectoryLabel_14")
        self.installer_bankIid = QtWidgets.QLineEdit(self.groupBox)
        self.installer_bankIid.setGeometry(QtCore.QRect(170, 310, 201, 27))
        self.installer_bankIid.setObjectName("installer_bankIid")
        self.projectDirectoryLabel_15 = QtWidgets.QLabel(self.groupBox)
        self.projectDirectoryLabel_15.setGeometry(QtCore.QRect(5, 310, 161, 27))
        self.projectDirectoryLabel_15.setObjectName("projectDirectoryLabel_15")
        self.installer_bankBic = QtWidgets.QLineEdit(self.groupBox)
        self.installer_bankBic.setGeometry(QtCore.QRect(380, 310, 201, 27))
        self.installer_bankBic.setObjectName("installer_bankBic")
        self.installer_vat = QtWidgets.QLineEdit(self.groupBox)
        self.installer_vat.setGeometry(QtCore.QRect(170, 220, 414, 27))
        self.installer_vat.setObjectName("installer_vat")
        self.projectDirectoryLabel_16 = QtWidgets.QLabel(self.groupBox)
        self.projectDirectoryLabel_16.setGeometry(QtCore.QRect(5, 220, 134, 27))
        self.projectDirectoryLabel_16.setObjectName("projectDirectoryLabel_16")

        self.retranslateUi(Preferences)
        self.buttonBox.accepted.connect(Preferences.accept)
        self.buttonBox.rejected.connect(Preferences.reject)
        QtCore.QMetaObject.connectSlotsByName(Preferences)
        Preferences.setTabOrder(self.projectRoot, self.templatePath)
        Preferences.setTabOrder(self.templatePath, self.nextQuoteNumber)
        Preferences.setTabOrder(self.nextQuoteNumber, self.nextInvoiceNumber)
        Preferences.setTabOrder(self.nextInvoiceNumber, self.installer_company)
        Preferences.setTabOrder(self.installer_company, self.installer_firstName)
        Preferences.setTabOrder(self.installer_firstName, self.installer_lastName)
        Preferences.setTabOrder(self.installer_lastName, self.installer_street)
        Preferences.setTabOrder(self.installer_street, self.installer_streetNumber)
        Preferences.setTabOrder(self.installer_streetNumber, self.installer_zip)
        Preferences.setTabOrder(self.installer_zip, self.installer_city)
        Preferences.setTabOrder(self.installer_city, self.installer_phone)
        Preferences.setTabOrder(self.installer_phone, self.installer_email)

    def retranslateUi(self, Preferences):
        _translate = QtCore.QCoreApplication.translate
        Preferences.setWindowTitle(_translate("Preferences", "Preferences"))
        self.projectDirectoryLabel.setText(_translate("Preferences", "Project Directory"))
        self.projectDirectoryLabel_2.setText(_translate("Preferences", "Template Directory"))
        self.projectDirectoryLabel_3.setText(_translate("Preferences", "nextQuoteNumber"))
        self.projectDirectoryLabel_4.setText(_translate("Preferences", "nextInvoiceNumber"))
        self.groupBox.setTitle(_translate("Preferences", "Installer"))
        self.projectDirectoryLabel_5.setText(_translate("Preferences", "Company"))
        self.projectDirectoryLabel_6.setText(_translate("Preferences", "First/Last-Name"))
        self.projectDirectoryLabel_8.setText(_translate("Preferences", "Street / Nr"))
        self.projectDirectoryLabel_9.setText(_translate("Preferences", "Zip / City"))
        self.projectDirectoryLabel_11.setText(_translate("Preferences", "Phone"))
        self.projectDirectoryLabel_12.setText(_translate("Preferences", "E-Mail"))
        self.projectDirectoryLabel_13.setText(_translate("Preferences", "Bank Name"))
        self.projectDirectoryLabel_14.setText(_translate("Preferences", "Bank IBAN"))
        self.projectDirectoryLabel_15.setText(_translate("Preferences", "Bank IID/Swift-BIC"))
        self.projectDirectoryLabel_16.setText(_translate("Preferences", "MwSt. Nummer"))
