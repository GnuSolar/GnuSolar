#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# A Building has :
#    - several roofs with/without solarpanels
#    - a physical place on earth, with coordinates
#    - a power supplier
#    - administration area
#    - municipality
#    - power meters

import json
import requests

from model.Municipality import *
from model.PowerCompany import *

from Config import Config

class Building:
    
    def __init__(self):
        self.buildingState = None       # "new" or "existing"
        self.buildingId = None          # swiss building id
        self.street = None
        self.streetNumber = None
        self.zip = None
        self.city = None
        self.region = None
        self.country = None
        self.plotNumber = None      # Parzelle Nummer
        self.swissGridX = None
        self.swissGridY = None
        self.municipalityCode = None  # Gemeinde Nummer, BFS-Nr. same as masterdata.municipality.code
        self.municipalityName = None  # Gemeinde Name
        
        self.meterNumberOld = None
        self.meterNumberNew = None
        self.mainFuseSize = None

        """
        Bauzone nach Bundesamt für Raumentwicklung(ARE):
        11 - Wohnzonen
        12 - Arbeitszonen
        13 - Mischzonen
        14 - Zentrumszonen
        15 - Zonen für öffentliche Nutzungen
        16 - eingeschränkte Bauzonen
"""        
        self.areZoneName = None         # Bauzone nach Bundesamt für Raumentwicklung(ARE)
        self.areZoneCode = None

    def coordinatesFromAddress(self):
        url = r"https://api3.geo.admin.ch/rest/services/api/MapServer/find"
        params = {
            "layer": "ch.swisstopo.amtliches-gebaeudeadressverzeichnis",
            "searchField": "zip_label",
            "searchText": self.zip,
            "layerDefs": json.dumps(
                {
                    "ch.swisstopo.amtliches-gebaeudeadressverzeichnis":"adr_number ilike '"+str(self.streetNumber)+"' and stn_label ilike '"+str(self.street)+"'"
                })
        }
        response = requests.get(url=url, params=params)

        results = response.json()["results"]
        if len(results) != 1:
            return

        self.buildingId = str(results[0]["id"])
        self.swissGridX = str(results[0]["geometry"]["x"])
        self.swissGridY = str(results[0]["geometry"]["y"])
        self.municipalityCode = str(results[0]["attributes"]["com_fosnr"])
        self.municipalityName = str(results[0]["attributes"]["com_name"])
        
        return
        
    def queryPlotNumber(self):
        x = float("2" + self.swissGridX)
        y = float("1" + self.swissGridY)
        url = r"https://api3.geo.admin.ch/rest/services/all/MapServer/identify"
        params = {
            "geometry": str(x) + "," + str(y),
            "geometryFormat": "geojson",
            "geometryType": "esriGeometryPoint",
            "imageDisplay": "1155,600,96",
            "layers": "all:ch.swisstopo-vd.amtliche-vermessung",
            "limit": "10",
            "mapExtent": str(x-30) + "," + str(y-30) + "," + str(x+30) + "," + str(y+30),
            "sr": "2056",
            "tolerance": "10"
        }

        response = requests.get(url=url, params=params)
        results = response.json()["results"]
        if len(results) != 1:
            return

        if not self.plotNumber:
            self.plotNumber = results[0]["properties"]["number"]

    def queryZoneing(self):
        x = float("2" + self.swissGridX)
        y = float("1" + self.swissGridY)
        url = r"https://api3.geo.admin.ch/rest/services/all/MapServer/identify"
        params = {
            "geometry": str(x) + "," + str(y),
            "geometryFormat": "geojson",
            "geometryType": "esriGeometryPoint",
            "imageDisplay": "1155,600,96",
            "layers": "all:ch.are.bauzonen",
            "limit": "10",
            "mapExtent": str(x-30) + "," + str(y-30) + "," + str(x+30) + "," + str(y+30),
            "sr": "2056",
            "tolerance": "10"
        }

        response = requests.get(url=url, params=params)
        results = response.json()["results"]
        if len(results) != 1:
            return

        self.areZoneCode = results[0]["properties"]["ch_code_hn"]
        self.areZoneName = results[0]["properties"]["ch_bez_d"]

    # Lookup the PowerCompany for this building.
    def getPowerCompanyId(self):

        # First check if in zip_code, city
        con = sqlite3.connect(Config.getMasterDbPath())
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT * FROM zip_code WHERE zip_code=?"
        res = cur.execute(sql, [self.zip])
        db_row = res.fetchone()

        if db_row:
            fkPowerCompany = db_row["fk_power_company"]
            if fkPowerCompany:
                return fkPowerCompany
        
        # Next in the Municipality
        sql = "SELECT * FROM municipality WHERE code=?"
        res = cur.execute(sql, [self.municipalityCode])
        db_row = res.fetchone()
        if db_row:
            fkPowerCompany = db_row["fk_power_company"]
            if fkPowerCompany:
                return fkPowerCompany
        
        return False

    # Check wheter the address of the Building ist the same as the given
    # Contact
    def identicalAddress(self, contact):
        if self.street != contact.street or \
           self.streetNumber != contact.streetNumber or \
           self.zip != contact.zip or \
           self.city != contact.city:
            return False

        return True
