#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# Power Company, Power Supplier, EVU, EW, Elektrizit�tsversorgunsunternehmen, Elektrizit�tswerk, 

import json

from model.Contact import *

class PowerCompany:
    
    def __init__(self):
        self.name = None
        self.mainContact = Contact()        # Address of the Headquarters

 
