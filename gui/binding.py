#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Copy values between the model and the input fields of a generated form.
#
# A field named <prefix>_a_b shows the attribute a.b of the object, e.g. with
# prefix "obj" the field obj_street shows building.street.

from PyQt5.QtWidgets import QLineEdit, QPlainTextEdit, QComboBox, QCheckBox


# Updates the User Interface from the Model
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
def updateModel(ui, obj, prefix):
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
