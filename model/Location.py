#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# Location / Address
import json
import requests

from model.Municipality import *

class Location:
    
    def __init__(self):
        self.addressLine1 = None
        self.addressLine2 = None
        self.street = None
        self.streetNumber = None
        self.zip = None
        self.city = None
        self.region = None
        self.country = None
        self.plotNumber = None
        self.swissGridX = None
        self.swissGridY = None
        self.municipality = Municipality()

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
        
        self.swissGridX = str(results[0]["geometry"]["x"])
        self.swissGridY = str(results[0]["geometry"]["y"])

        self.queryPlotNumber()
        
        return
        
    def queryPlotNumber(self):
        if self.plotNumber:
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

        self.plotNumber = results[0]["properties"]["number"]
