#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Country extension for Switzerland, namespace "ch"
# (doc/file_format_v3/file_format.md, section 13).
#
#   site.ext.ch                  lv95 {e, n}, egid [..], zone {code, name}
#   municipality snapshot        buildingFormId
#   grid operator snapshot       vseId, tagFormId, iaFormId
#   bank account                 iid

ID = "ch"
NAME = "Switzerland"
VERSION = "1"

# version of the data in the namespace ("v")
DATA_VERSION = 1

# kind => caption of the steps with swiss authorities
STEP_KINDS = {
    "ch.tag": "Technisches Anschlussgesuch (TAG)",
    "ch.ia": "Installationsanzeige (IA)",
    "ch.building_permit": "Solarmeldung / Baugesuch",
    "ch.esti": "Plangenehmigung ESTI",
    "ch.pronovo": "Pronovo Einmalvergütung (EIV)",
    "ch.sina_dc": "Sicherheitsnachweis DC",
    "ch.sina_ac": "Sicherheitsnachweis AC",
}


# Coordinates as GnuSolar stored them up to file version 2 (text, LV03 with
# 6 digits or LV95 with 7) as LV95 east and north in metres.
# Returns None if they are not swiss coordinates.
def lv95FromText(x, y):
    try:
        e = float(str(x).strip().replace(",", "."))
        n = float(str(y).strip().replace(",", "."))
    except ValueError:
        return None
    if e < 2000000:
        e += 2000000
    if n < 1000000:
        n += 1000000
    if not (2480000 <= e <= 2840000 and 1070000 <= n <= 1300000):
        return None
    return round(e, 3), round(n, 3)


# WGS84 latitude and longitude of LV95 coordinates, with the approximate
# formulas of swisstopo (about 1 m).
def lv95ToWgs84(e, n):
    y = (e - 2600000) / 1000000
    x = (n - 1200000) / 1000000
    lon = 2.6779094 + 4.728982 * y + 0.791484 * y * x + 0.1306 * y * x * x - 0.0436 * y * y * y
    lat = 16.9023892 + 3.238272 * x - 0.270978 * y * y - 0.002528 * x * x - 0.0447 * y * y * x - 0.0140 * x * x * x
    return round(lat * 100 / 36, 6), round(lon * 100 / 36, 6)


# ---- lookups at geo.admin.ch ------------------------------------------------

# The building at an address: {"egid", "x", "y" (LV03), "municipalityCode",
# "municipalityName"}, None if there is not exactly one.
def findAddress(zipCode, street, streetNumber):
    import json
    import requests

    url = r"https://api3.geo.admin.ch/rest/services/api/MapServer/find"
    params = {
        "layer": "ch.swisstopo.amtliches-gebaeudeadressverzeichnis",
        "searchField": "zip_label",
        "searchText": zipCode,
        "layerDefs": json.dumps(
            {
                "ch.swisstopo.amtliches-gebaeudeadressverzeichnis":"adr_number ilike '"+str(streetNumber)+"' and stn_label ilike '"+str(street)+"'"
            })
    }
    try:
        response = requests.get(url=url, params=params)
        results = response.json()["results"]
    except Exception:
        return None

    if len(results) != 1:
        return None

    return {
        "egid": str(results[0]["id"]),
        "x": str(results[0]["geometry"]["x"]),
        "y": str(results[0]["geometry"]["y"]),
        "municipalityCode": str(results[0]["attributes"]["com_fosnr"]),
        "municipalityName": str(results[0]["attributes"]["com_name"]),
    }


# the properties of the one object of a layer at LV95 coordinates, None if
# there is not exactly one
def _identify(layer, e, n):
    import requests

    url = r"https://api3.geo.admin.ch/rest/services/all/MapServer/identify"
    params = {
        "geometry": str(e) + "," + str(n),
        "geometryFormat": "geojson",
        "geometryType": "esriGeometryPoint",
        "imageDisplay": "1155,600,96",
        "layers": "all:" + layer,
        "limit": "10",
        "mapExtent": str(e-30) + "," + str(n-30) + "," + str(e+30) + "," + str(n+30),
        "sr": "2056",
        "tolerance": "10"
    }

    response = requests.get(url=url, params=params)
    results = response.json()["results"]
    if len(results) != 1:
        return None
    return results[0]["properties"]


# number of the parcel at LV95 coordinates
def queryPlotNumber(e, n):
    properties = _identify("ch.swisstopo-vd.amtliche-vermessung", e, n)
    return properties["number"] if properties else None


# building zone (ARE) at LV95 coordinates: {"code", "name"}
def queryZone(e, n):
    properties = _identify("ch.are.bauzonen", e, n)
    if not properties:
        return None
    return {"code": properties["ch_code_hn"], "name": properties["ch_bez_d"]}
