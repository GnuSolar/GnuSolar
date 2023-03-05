#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# A Plant is one or more PV Arrays and one or more inverter, smartmeters an batteries.

class Plant:

    def __init__(self):
        # class members
        self.constructionType = None        # "", "builton", "integrated", "facade"

        self.totalPowerDc = None
        self.totalArea = None
        self.totalPanelCount = None

        self.totalPowerAc = None
        
        self.totalCost = None               # for solar note aargau

