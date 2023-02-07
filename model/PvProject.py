#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# Photovoltaics Project Base Class

import jsonpickle
import subprocess
import os
import datetime

from model.Contact import *
from model.Location import *
from model.Contact import *
from model.Progress import *
from model.PowerCompany import *

class PvProject:
    
    def __init__(self, path=""):
        self._savePath = None
        self.owner = Contact()
        self.plantLocation = Location()
        self.powerCompany = PowerCompany()
        self.progress = Progress()
        self.comment = None
        
        # project state:
        #  'Request'       Anfrage
        #  'Quote'         offeriert
        #  'Wait'          wartet auf iergendwas
        #  'Order'         Zusage
        #  'Construction'  im Bau
        #  'Running'       im Betrieb
        #  'BuiltOther'    jemand anders gebaut
        self.state = None

        if path != "":
            self.open(path)

    def initFromAddress(self, street, streetNumber, zipCode, city):
        if not self.plantLocation.street:
            self.plantLocation.street = street
        if not self.plantLocation.streetNumber:
            self.plantLocation.streetNumber = streetNumber
        if not self.plantLocation.zip:
            self.plantLocation.zip = zipCode
        if not self.plantLocation.city:
            self.plantLocation.city = city
        
        # Anfrage erhalten gleich jetzt
        today = date.today()
        self.progress.inquiryReceived = today.isoformat()
        return
            
    def toJson(self):
        jsonpickle.set_preferred_backend('json')
        jsonpickle.set_encoder_options('json', sort_keys=True, indent=4)
        
        _savePath = self._savePath      # don't serialize this attribute
        del self._savePath
        
        ret = jsonpickle.encode(self)
        
        self._savePath = _savePath
        
        return ret

        
    def fromJson(self, json_str):
        ret = jsonpickle.decode(json_str)

        # loop over all attributes from self and copy them over from ret
        # makes sure if you open a file with an older model, the attributes 
        # default to default :)
        self._copyOver(self, ret)

        
    def _copyOver(self, src, dest):
        for key, value in src.__dict__.items():

            if not hasattr(dest, key):
                continue
                
            if hasattr(value, "__dict__") and isinstance(value.__dict__, dict):
                self._copyOver(src.__dict__[key], dest.__dict__[key])
            else:
                src.__dict__[key] = dest.__dict__[key]
    
    # open from disk
    def open(self, path):
        self._savePath = path
        f = open(path)
        json_str = f.read()
        f.close()
    
        self.fromJson(json_str)
    
    # save to disk as json under specified path
    def saveAs(self, path):
        self._savePath = path
        return self.save()
    
    
    # save to disk
    def save(self):
        json = self.toJson()

        f = open(self._savePath, 'w')
        f.write(json)
        f.close()


    
    
