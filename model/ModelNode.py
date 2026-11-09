#!/usr/bin/python
# -*- coding: utf-8 -*-

# Base class of the PvProject and all its parts (Building, Contact, ...)
#
# Attributes starting with "_" are runtime only (_top, _ui, _savePath, ...)
# and are never saved to the .pvp file.
#
# _top is the link from every part to the PvProject it belongs to.
# It is set when a part is created and again by link() after loading.
#
# Loading fills in default values, see __setstate__.

class ModelNode:

    # attributes without "_" which must not be saved either
    _notSaved = ()

    # for jsonpickle: what gets saved
    def __getstate__(self):
        return {k: v for k, v in self.__dict__.items()
                if not k.startswith("_") and k not in self._notSaved}

    # for jsonpickle: loading. Starts with the defaults of a new object, so
    # attributes added to the class later get their default value, and
    # attributes removed from the class are dropped.
    def __setstate__(self, state):
        self._initDefaults()
        for key, value in state.items():
            if key not in self.__dict__:
                continue
            default = self.__dict__[key]
            # dicts (e.g. the contacts): entries of the file are added to the defaults
            if isinstance(default, dict) and isinstance(value, dict):
                merged = dict(default)
                merged.update(value)
                value = merged
            self.__dict__[key] = value

    # the values of a new object, the _top link is set later by link()
    def _initDefaults(self):
        self.__init__(None)

    # set _top of all parts below this node
    def link(self, top):
        for key, value in self.__dict__.items():
            if key.startswith("_") or key in self._notSaved:
                continue
            if isinstance(value, dict):
                children = value.values()
            elif isinstance(value, (list, tuple)):
                children = value
            else:
                children = [value]
            for child in children:
                if isinstance(child, ModelNode):
                    child._top = top
                    child.link(top)
