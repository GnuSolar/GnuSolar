#!/usr/bin/python
# -*- coding: utf-8 -*-

# Base class of the PvProject and all its parts (Building, Contact, ...)
#
# toDict() / fromDict() convert a part to plain data (dicts, strings,
# numbers, booleans, None) and back. The file format is built on top of that
# (see PvProject.toJson), the model itself knows nothing about files.
#
# Attributes starting with "_" are runtime only (_top, _ui, _savePath, ...)
# and are never saved, neither are the ones listed in _notSaved.
#
# _top is the link from every part to the PvProject it belongs to.
# It is set when a part is created and again by link() after loading.

class ModelNode:

    # attributes without "_" which must not be saved either
    _notSaved = ()

    def _isSaved(self, key):
        return not key.startswith("_") and key not in self._notSaved

    # plain data of this part and all parts below it
    def toDict(self):
        return {k: ModelNode._toPlain(v) for k, v in self.__dict__.items() if self._isSaved(k)}

    @staticmethod
    def _toPlain(value):
        if isinstance(value, ModelNode):
            return value.toDict()
        if isinstance(value, dict):
            return {k: ModelNode._toPlain(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [ModelNode._toPlain(v) for v in value]
        return value

    # Fill this part from plain data. Starts with the defaults of a new object,
    # so attributes added to the class later keep their default value, and
    # attributes the class no longer has are dropped.
    # Which class a part has comes from the defaults, not from the data.
    def fromDict(self, data):
        self._initDefaults()
        for key, value in data.items():
            if not self._isSaved(key) or key not in self.__dict__:
                continue
            default = self.__dict__[key]

            if isinstance(default, ModelNode):
                if isinstance(value, dict):
                    default.fromDict(value)
                continue

            # dict of parts (e.g. the contacts): entries of the data are
            # added to the default entries, all of the same class
            if isinstance(default, dict) and isinstance(value, dict):
                merged = dict(default)
                cls = next((type(v) for v in default.values() if isinstance(v, ModelNode)), None)
                for k, v in value.items():
                    if cls and isinstance(v, dict):
                        node = cls.__new__(cls)
                        node.fromDict(v)
                        merged[k] = node
                    else:
                        merged[k] = v
                value = merged

            self.__dict__[key] = value

    # the values of a new object, the _top link is set later by link()
    def _initDefaults(self):
        self.__init__(None)

    # set _top of all parts below this node
    def link(self, top):
        for key, value in self.__dict__.items():
            if not self._isSaved(key):
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
