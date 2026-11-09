#!/usr/bin/python
# -*- coding: utf-8 -*-

# Base class of the PvProject and all its parts (Building, Contact, ...)
#
# Attributes starting with "_" are runtime only (_top, _ui, _savePath, ...)
# and are never saved to the .pvp file.
#
# _top is the link from every part to the PvProject it belongs to.
# It is set when a part is created and again by link() after loading.

class ModelNode:

    # attributes without "_" which must not be saved either
    _notSaved = ()

    # for jsonpickle: what gets saved
    def __getstate__(self):
        return {k: v for k, v in self.__dict__.items()
                if not k.startswith("_") and k not in self._notSaved}

    def __setstate__(self, state):
        self.__dict__.update(state)

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
