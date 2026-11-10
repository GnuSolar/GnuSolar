#!/usr/bin/python
# -*- coding: utf-8 -*-

# Base class of the PvProject and all its parts (Site, Contact, Order, ...)
#
# toDict() / fromDict() convert a part to plain data (dicts, lists, strings,
# numbers, booleans, None) and back. The file format is built on top of that
# (see formats/pvp.py), the model itself knows nothing about files.
#
# Attributes starting with "_" are runtime only (_top, _savePath, ...)
# and are never saved, neither are the ones listed in _notSaved.
#
# _top is the link from every part to the PvProject it belongs to, _parent
# the part it sits in. Both are set by link() after loading and when a part
# is added.
#
# The attribute names are the field names of the file (doc/file_format.md).
# Some of them are Python keywords ("from"): read and write those with
# get() and set().

import uuid


class ModelNode:

    # attributes without "_" which must not be saved either
    _notSaved = ()

    # field => class of the entries, for fields that hold a list of parts
    _parts = {}

    # field => type of its value: "int", "number", "date", "bool", "list".
    # Everything else is text. Dates are Unix timestamps (model/values.py).
    _types = {}

    # fields which are written also when they are empty
    _always = ()

    def _isSaved(self, key):
        return not key.startswith("_") and key not in self._notSaved

    # the type of a field, see _types
    def fieldType(self, key):
        return self._types.get(key, "text")

    # value of a field. Fields the class doesn't know are read from the
    # unknown fields of the file.
    def get(self, key, default=None):
        if key in self.__dict__:
            value = self.__dict__[key]
        else:
            value = self.__dict__.get("_unknown", {}).get(key)
        return default if value is None else value

    def set(self, key, value):
        if key in self.__dict__ or not self._isSaved(key):
            self.__dict__[key] = value
            return
        unknown = self.__dict__.setdefault("_unknown", {})
        if value is None:
            unknown.pop(key, None)
        else:
            unknown[key] = value

    # plain data of this part and all parts below it. Empty values are left
    # out, fields the class doesn't know are written back as they were read.
    def toDict(self):
        data = dict(self.__dict__.get("_unknown") or {})
        for key, value in self.__dict__.items():
            if not self._isSaved(key):
                continue
            plain = ModelNode._toPlain(value)
            if key not in self._always and (plain is None or plain == [] or plain == {}):
                data.pop(key, None)
                continue
            data[key] = plain
        return data

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
    # so attributes added to the class later keep their default value.
    # Fields the class doesn't have are kept in _unknown and written back by
    # toDict(): data of plugins and of newer revisions of the format survive.
    # Which class a part has comes from the class (the defaults and _parts),
    # not from the data.
    def fromDict(self, data):
        self._initDefaults()
        self._unknown = {}
        for key, value in data.items():
            if not self._isSaved(key) or key not in self.__dict__:
                self._unknown[key] = value
                continue
            default = self.__dict__[key]

            if isinstance(default, ModelNode):
                if isinstance(value, dict):
                    default.fromDict(value)
                continue

            # list of parts (e.g. the orders)
            if key in self._parts and isinstance(value, list):
                value = [self._newPart(self._parts[key], v) for v in value]

            # dict of parts: entries of the data are added to the default
            # entries, all of the same class
            elif isinstance(default, dict) and isinstance(value, dict):
                merged = dict(default)
                cls = next((type(v) for v in default.values() if isinstance(v, ModelNode)), None)
                for k, v in value.items():
                    merged[k] = self._newPart(cls, v) if cls else v
                value = merged

            # null means not known, the same as a missing field
            elif value is None:
                continue

            self.__dict__[key] = value

    @staticmethod
    def _newPart(cls, data):
        if not isinstance(data, dict):
            return data
        node = cls.__new__(cls)
        node.fromDict(data)
        return node

    # the values of a new object, the _top link is set later by link()
    def _initDefaults(self):
        self.__init__(None)

    # the parts directly below this node
    def children(self):
        ret = []
        for key, value in self.__dict__.items():
            if not self._isSaved(key):
                continue
            if isinstance(value, dict):
                values = value.values()
            elif isinstance(value, (list, tuple)):
                values = value
            else:
                values = [value]
            ret.extend(v for v in values if isinstance(v, ModelNode))
        return ret

    # set _top and _parent of all parts below this node
    def link(self, top):
        for child in self.children():
            child._top = top
            child._parent = self
            child.link(top)

    # A new part of class cls in the list field key, with a new id
    def addPart(self, key, cls=None, **values):
        cls = cls or self._parts[key]
        top = self.__dict__.get("_top") or self
        node = cls(top)
        if "id" in node.__dict__:
            node.id = newId()
        for k, v in values.items():
            node.set(k, v)
        node._top = top
        node._parent = self
        node.link(top)
        self.__dict__[key].append(node)
        return node

    # remove a part from the list field it is in
    def removePart(self, node):
        for key in self._parts:
            if node in self.__dict__[key]:
                self.__dict__[key].remove(node)
                return True
        return False


# a new id for an object of the file: UUID version 4, lower case
def newId():
    return str(uuid.uuid4())
