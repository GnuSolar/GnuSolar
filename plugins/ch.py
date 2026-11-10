#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Country extension for Switzerland, namespace "ch" (doc/file_format.md,
# section 13).
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
