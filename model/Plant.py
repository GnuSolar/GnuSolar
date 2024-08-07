#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# A Plant is one or more PV Arrays and one or more inverter, smartmeters an batteries.

class Plant:

    def __init__(self, top):
        # class members
        self._top = top
        self.constructionType = None        # "", "builton", "integrated", "facade"

        self.totalPowerDc = None
        self.totalArea = None
        self.totalPanelCount = None
        self.panelDesc = None

        self.totalPowerAc = None
        self.inverterDesc = None
        
        self.totalCost = None               # for solar note aargau

    def getTreeCaption(self):
        return "Anlage"

    def initUi(self, ui):
        pass

    # for jsonpickle to ignore
    def __getstate__(self):
        state = self.__dict__.copy()
        del state['_top']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
