#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The detail pages of the site window, built from the field lists of
# gui/fields.py.
#
#   form = Form(obj, onChange)
#   form.widget     the page
#   form.inputs     path of a field => its input
#
# Every change is stored in the model at once. Text that is no number, date
# or JSON, or that the model refuses, is not stored: the field turns red.

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QScrollArea, QLineEdit,
                             QPlainTextEdit, QComboBox, QCheckBox, QLabel, QPushButton)

from model.ModelNode import getPath, setPath
from model import values
from gui.fields import fieldsOf
import gui.captions

INVALID_STYLE = "background-color: #ffc0c0;"


class Form:
    # actions: the actions of the page (gui.tree.Action), shown as buttons
    # above the fields. fieldActions: path of a field => action, a button
    # beside that field. runAction(action) runs one.
    def __init__(self, obj, onChange=None, actions=None, runAction=None, text=None, fieldActions=None):
        self.obj = obj
        self.onChange = onChange
        self.runAction = runAction
        self.fieldActions = fieldActions or {}
        self.inputs = {}        # path => input widget
        self.buttons = {}       # text of an action => its button

        self.widget = QWidget()
        outer = QVBoxLayout(self.widget)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        outer.addWidget(scroll)
        inner = QWidget()
        scroll.setWidget(inner)
        layout = QVBoxLayout(inner)

        if text:
            label = QLabel(text)
            label.setWordWrap(True)
            layout.addWidget(label)
        if actions:
            # three buttons in a row, so the page doesn't get wider than the window
            rows = QtWidgets.QGridLayout()
            shown = 0
            for action in actions:
                button = QPushButton(action.text)
                if action.entries is not None:
                    if not action.entries:
                        continue
                    menu = QtWidgets.QMenu(button)
                    self._fillMenu(menu, action.entries)
                    button.setMenu(menu)
                else:
                    button.clicked.connect(lambda _, a=action: self._run(a))
                self.buttons[action.text] = button
                rows.addWidget(button, shown // 3, shown % 3)
                shown += 1
            rows.setColumnStretch(3, 1)
            layout.addLayout(rows)

        for title, fields in fieldsOf(obj):
            box = QGroupBox(title)
            form = QFormLayout(box)
            for field in fields:
                form.addRow(field.caption, self._row(field))
            layout.addWidget(box)
        layout.addStretch()

    def _run(self, action):
        if self.runAction:
            self.runAction(action)
        else:
            action.func()

    def _fillMenu(self, menu, actions):
        for action in actions:
            if action.entries is not None:
                if action.entries:
                    self._fillMenu(menu.addMenu(action.text), action.entries)
            else:
                menu.addAction(action.text).triggered.connect(lambda _, a=action: self._run(a))

    # ---- inputs -------------------------------------------------------------

    # the input of a field with its buttons: today for a date, and the
    # action of the field
    def _row(self, field):
        widget = self._input(field)
        buttons = []
        if field.type == "date":
            today = QtWidgets.QToolButton()
            today.setText("heute")
            today.clicked.connect(lambda _, w=widget: w.setText(values.dateToText(values.today())))
            buttons.append(today)
        action = self.fieldActions.get(field.path)
        if action is not None:
            button = QPushButton(action.text)
            button.clicked.connect(lambda _, a=action: self._run(a))
            self.buttons[action.text + " " + field.path] = button
            buttons.append(button)
        if not buttons:
            return widget
        row = QWidget()
        rowLayout = QHBoxLayout(row)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.addWidget(widget)
        for button in buttons:
            rowLayout.addWidget(button)
        return row

    def _input(self, field):
        value = getPath(self.obj, field.path)
        if field.type == "readonly":
            widget = QLabel(values.toText("text", value))
            self.inputs[field.path] = widget
            return widget

        if field.ref or field.choices:
            widget = QComboBox()
            widget.addItem("", None)
            for data, caption in self._choices(field):
                widget.addItem(caption, data)
            index = widget.findData(value)
            if index < 0 and value is not None:
                # a value the list doesn't have is kept
                widget.addItem(str(value), value)
                index = widget.count() - 1
            widget.setCurrentIndex(max(index, 0))
            widget.currentIndexChanged.connect(lambda _, f=field, w=widget: self._store(f, w, w.currentData()))
        elif field.type == "bool":
            widget = QCheckBox()
            widget.setChecked(bool(value))
            widget.toggled.connect(lambda checked, f=field, w=widget: self._store(f, w, True if checked else None))
        elif field.type in ("json", "multiline"):
            widget = QPlainTextEdit()
            widget.setPlainText(values.toText("json" if field.type == "json" else "text", value))
            widget.setMinimumHeight(90)
            widget.textChanged.connect(lambda f=field, w=widget: self._storeText(f, w, w.toPlainText()))
        else:
            widget = QLineEdit()
            widget.setText(values.toText(field.type, value))
            if field.hint:
                widget.setPlaceholderText(field.hint)
            widget.textChanged.connect(lambda text, f=field, w=widget: self._storeText(f, w, text))
        self.inputs[field.path] = widget
        return widget

    # (value, caption) of the entries of a drop down
    def _choices(self, field):
        if field.ref:
            name, _, kind = field.ref.partition(":")
            ret = []
            for other in self._referable(name):
                if other is self.obj:
                    continue
                if kind and kind != "None" and getattr(other, "kind", None) not in (kind, None):
                    continue
                ret.append((other.id, gui.captions.caption(other)))
            return ret
        if isinstance(field.choices, dict):
            return list(field.choices.items())
        return [(choice, str(choice)) for choice in field.choices]

    # The parts a field can point to: the list of the part itself (the quotes
    # of a project), else the one of the part it is in (the designs of the
    # project of a quote), else everything of that name at the site.
    def _referable(self, name):
        for holder in (self.obj, getattr(self.obj, "_parent", None)):
            own = getattr(holder, "__dict__", {}).get(name)
            if isinstance(own, list):
                return own
        top = getattr(self.obj, "_top", None)
        return top.collection(name) if top else []

    # ---- storing --------------------------------------------------------------

    def _storeText(self, field, widget, text):
        fieldType = "text" if field.type == "multiline" else field.type
        try:
            value = values.fromText(fieldType, text)
        except ValueError as e:
            self._invalid(widget, e)
            return
        self._store(field, widget, value)

    def _invalid(self, widget, error):
        widget.setStyleSheet(INVALID_STYLE)
        widget.setToolTip(str(error))

    def _store(self, field, widget, value):
        try:
            setPath(self.obj, field.path, value)
        except ValueError as e:
            # the names of file version 2 check their text themselves
            self._invalid(widget, e)
            return
        widget.setStyleSheet("")
        widget.setToolTip("")
        if hasattr(self.obj, "changed"):
            self.obj.changed()
        # derived values may have changed
        for path, label in self.inputs.items():
            if isinstance(label, QLabel):
                label.setText(values.toText("text", getPath(self.obj, path)))
        if self.onChange:
            self.onChange(self, field)
