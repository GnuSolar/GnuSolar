#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The native GnuSolar file of a site (plant.pvp), plain JSON in UTF-8:
#
#   {"format": "gnusolar-site", "version": 3, "site": {...}}
#
#   version 3: doc/file_format.md. "site" is PvSite.toDict()
#   version 2: {"format": "gnusolar-project", "version": 2, "project": {...}}
#              one building, one plant, one progress. Migrated when read
#              (formats/migrate_v2.py) and written as version 3. The first
#              time, the version 2 file is kept next to it as plant.pvp.v2.
#   version 1: jsonpickle, no longer read. All projects were converted on
#              2026-11-09 with tools/migrate_pvp.py, see git history.
#
# A file of a newer version than this program knows is refused.

import os
import json
import shutil
from datetime import date

from formats import migrate_v2
from model import values

FILE_FORMAT = "gnusolar-site"
FILE_VERSION = 3

# format name of version 2
V2_FILE_FORMAT = "gnusolar-project"

# ending of the copy of the file before it was migrated
BACKUP_ENDING = ".v2"


# the file content of a site
def dumps(site):
    data = {"format": FILE_FORMAT, "version": FILE_VERSION, "site": site.toDict()}
    return json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False)


# Fill a site from file content. taken and files are for the migration of
# older versions: the date of the file and the files of the site folder.
def loads(site, text, taken=None, files=None, report=None):
    data = json.loads(text)
    plain, migratedFrom = _migrate(data, taken, files, report)
    site.fromDict(plain)
    site.link(site)
    # the version the file had, None for the current one
    site._migratedFrom = migratedFrom


# The plain site data of a file, migrated to the current version, and the
# version it was migrated from (None: it is current).
def _migrate(data, taken=None, files=None, report=None):
    version = data.get("version")
    if data.get("format") == FILE_FORMAT:
        if version != FILE_VERSION:
            raise Exception("File version " + str(version) + " is not supported, a newer GnuSolar is needed")
        return data.get("site"), None
    if data.get("format") == V2_FILE_FORMAT:
        if version != 2:
            raise Exception("File version " + str(version) + " of the format " + V2_FILE_FORMAT + " is not supported")
        return migrate_v2.migrate(data.get("project"), taken=taken, files=files, report=report), 2
    if "py/state" in data:
        raise Exception("Old file format (version 1), convert it with tools/migrate_pvp.py of GnuSolar commit cbb39e5")
    raise Exception("Not a GnuSolar file")


# the files of the folders with quotes and invoices, relative to the site folder
def _siteFiles(siteDir):
    ret = []
    for folder in ("off", "fin"):
        path = os.path.join(siteDir, folder)
        if os.path.isdir(path):
            ret.extend(folder + "/" + name for name in sorted(os.listdir(path)))
    return ret


# fill a site from a file
def load(site, path, report=None):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    taken = values.dayToTimestamp(date.fromtimestamp(os.path.getmtime(path)))
    loads(site, text, taken=taken, files=_siteFiles(os.path.dirname(os.path.abspath(path))), report=report)


# Write a site to a file. Writes a temporary file and renames it,
# so a crash never leaves a half written site.
def save(site, path):
    text = dumps(site)

    # keep the file of the older version, once
    if getattr(site, "_migratedFrom", None) and os.path.isfile(path):
        backupPath = path + BACKUP_ENDING
        if not os.path.exists(backupPath):
            shutil.copy2(path, backupPath)

    tmpPath = path + ".tmp"
    with open(tmpPath, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmpPath, path)
    site._migratedFrom = None
