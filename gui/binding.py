#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Copy values between the model and the input fields of a generated form.
#
# A field named <prefix>_a_b shows the attribute a.b of the object, e.g. with
# prefix "obj" the field obj_street shows building.street.
#
# A combo box shows the text of its items. If its items were added with
# setChoices, the value is the code of the item instead of its text.

from PyQt5.QtWidgets import QLineEdit, QPlainTextEdit, QComboBox, QCheckBox


# fill a combo box with choices, pairs of (code saved, text shown)
def setChoices(combo, choices):
    combo.clear()
    for code, text in choices:
        combo.addItem(text, code)


# the value of a combo box: the code of the chosen item, or its text
def comboValue(combo):
    code = combo.currentData()
    return combo.currentText() if code is None else code


# choose the item of a combo box with the code or text value. No value
# chooses the first item, the default of the choices.
def setComboValue(combo, value):
    if value is None:
        combo.setCurrentIndex(0 if combo.count() else -1)
        return
    index = combo.findData(value)
    if index >= 0:
        combo.setCurrentIndex(index)
    else:
        combo.setCurrentText(value)


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
                setComboValue(uiEl, modelEl)
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
            setattr(modelEl, last, comboValue(uiEl))
        elif isinstance(uiEl, QCheckBox):
            setattr(modelEl, last, uiEl.isChecked())
        else:
            raise Exception(str(type(uiEl)) + " not implemented")
