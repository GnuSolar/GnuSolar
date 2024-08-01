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

from model.PvProject import *
from model.Municipality import *
from model.PowerCompany import *

from Config import *
from GnuSolar import *

class Building:
    
    def __init__(self, top):
        self._top = top
        self._ui = None
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
        try:
            response = requests.get(url=url, params=params)
            results = response.json()["results"]
        except Exception:
            return
        
        if len(results) != 1:
            return

        self.buildingId = str(results[0]["id"])
        self.swissGridX = str(results[0]["geometry"]["x"])
        self.swissGridY = str(results[0]["geometry"]["y"])
        self.municipalityCode = str(results[0]["attributes"]["com_fosnr"])
        self.municipalityName = str(results[0]["attributes"]["com_name"])
        
        return
        
    def queryPlotNumber(self):
        if not self.swissGridX or not self.swissGridY:
            return
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
        if not self.swissGridX or not self.swissGridY:
            return
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

    def getTreeCaption(self):
        return "Gebäude"

    def initUi(self, ui):
        self._ui = ui
        ui.updateFromAddress.clicked.connect(self.action_updateFromAddress)
        ui.get3dModel.clicked.connect(self.action_get3dModel)

    def action_updateFromAddress(self):
        self.coordinatesFromAddress()
        self.queryPlotNumber()
        self.queryZoneing()
        
        muni = self._top.municipality
        muni.fromCode(self.municipalityCode)
        self._top.powerCompany.fromId(muni.fkPowerCompany)

        GnuSolar.updateUi(self._ui, self, "obj")

    def action_get3dModel(self):
        x = self.swissGridX
        y = self.swissGridY
        if not x or not y:
            QtWidgets.QMessageBox.warning(None, 'Get 3D Model Error', 'no coordiantes')
            return

        url = "http://amsler-solar.ch/swissbuildings3d-2-0/api.php?x=2" + str(x) + "&y=1" + str(y) + "&format=stl"
        response = requests.get(url=url)
        resp_txt = response.text
        if not resp_txt.startswith("solid"):
            QtWidgets.QMessageBox.warning(None, 'Get 3D Model Error', resp_txt)
            return
        
        cad_folder = os.path.dirname(config.pvpPath) + os.sep + "cad"
        if not os.path.isdir(cad_folder):
            os.mkdir(cad_folder)
        
        stl_file = cad_folder + os.sep + "house_geo.stl"
        if os.path.isfile(stl_file):
            QtWidgets.QMessageBox.warning(None, 'Get 3D Model Error', "File exists: " + stl_file)
            return
        
        with open(stl_file, "w") as f:
            f.write(resp_txt)

        openFolderIfExists(stl_file)

    # for jsonpickle to ignore
    def __getstate__(self):
        state = self.__dict__.copy()
        del state['_ui']
        del state['_top']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
