#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Copy values between the model and the input fields of a generated form.
#
# A field named <prefix>_a_b shows the attribute a.b of the object, e.g. with
# prefix "obj" the field obj_street shows building.street.
#
# The model holds numbers and dates (model/values.py), the forms text. A
# field of a model part is converted by its type (ModelNode._types); the
# properties of the version 2 views (model/compat.py) take and give text
# themselves. Text that is no number or date is not stored: the field turns
# red and the model keeps its value.

from PyQt5.QtWidgets import QLineEdit, QPlainTextEdit, QComboBox, QCheckBox

from model.ModelNode import ModelNode
from model import values

INVALID_STYLE = "background-color: #ffc0c0;"


# the object and attribute name a field name like obj_tagContact_email means
def resolve(obj, fieldName):
    attrs = fieldName.split("_")
    attrs.pop(0)
    last = attrs.pop()
    for attr in attrs:
        obj = getattr(obj, attr)
    return obj, last


# True for an attribute of a model part which holds a typed value
def _isTyped(obj, name):
    return isinstance(obj, ModelNode) and name in obj.__dict__


def getValue(obj, name):
    value = getattr(obj, name)
    if _isTyped(obj, name):
        fieldType = obj.fieldType(name)
        return bool(value) if fieldType == "bool" else values.toText(fieldType, value)
    return value


# Raises ValueError if value is text which is no number or date
def setValue(obj, name, value):
    if _isTyped(obj, name):
        fieldType = obj.fieldType(name)
        if fieldType == "bool":
            value = True if value else None
        else:
            value = values.fromText(fieldType, value)
    setattr(obj, name, value)


def widgetValue(uiEl):
    if isinstance(uiEl, QLineEdit):
        return uiEl.text()
    if isinstance(uiEl, QPlainTextEdit):
        return uiEl.toPlainText()
    if isinstance(uiEl, QComboBox):
        data = uiEl.currentData()
        return data if data is not None else uiEl.currentText()
    if isinstance(uiEl, QCheckBox):
        return uiEl.isChecked()
    raise Exception(str(type(uiEl)) + " not implemented")


def setWidgetValue(uiEl, value):
    if isinstance(uiEl, QLineEdit):
        uiEl.setText("" if value is None else str(value))
    elif isinstance(uiEl, QPlainTextEdit):
        uiEl.setPlainText("" if value is None else str(value))
    elif isinstance(uiEl, QComboBox):
        index = uiEl.findData(value) if value not in (None, "") else -1
        if index >= 0:
            uiEl.setCurrentIndex(index)
        else:
            uiEl.setCurrentText("" if value is None else str(value))
    elif isinstance(uiEl, QCheckBox):
        uiEl.setChecked(bool(value))
    else:
        raise Exception(str(type(uiEl)) + " not implemented")


# Store the value of a field in the model. Returns False, and marks the
# field, if the value is not valid.
def storeWidget(uiEl, obj, name):
    try:
        setValue(obj, name, widgetValue(uiEl))
    except ValueError as e:
        uiEl.setStyleSheet(INVALID_STYLE)
        uiEl.setToolTip(str(e))
        return False
    uiEl.setStyleSheet("")
    uiEl.setToolTip("")
    return True


# Updates the User Interface from the Model
def updateUi(ui, obj, prefix):
    for key, value in ui.__dict__.items():
        # normal model<=>ui element?
        if key.startswith(prefix + "_"):
            modelEl, last = resolve(obj, key)
            setWidgetValue(getattr(ui, key), getValue(modelEl, last))


# Updates the Data Model from the User Interface
def updateModel(ui, obj, prefix):
    for key, value in ui.__dict__.items():
        if not key.startswith(prefix + "_"):
            continue

        modelEl, last = resolve(obj, key)
        storeWidget(getattr(ui, key), modelEl, last)
