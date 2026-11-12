#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The native GnuSolar file of a site (plant.pvp), plain JSON in UTF-8:
#
#   {"format": "gnusolar-site", "version": 3, "site": {...}}
#
#   version 3: doc/file_format.md. "site" is PvSite.toDict()
#   version 3 draft: {"format": "gnusolar-project", "version": 3, "project":
#              {...}}, written by GnuSolar until 2026-11-12: the site was
#              called project, a project order, and address and grid
#              connection were a section "site" of their own. Renamed when
#              read (fromDraft3), the file is kept as plant.pvp.v3-draft.
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

# format name of version 2 and of the draft of version 3
OLD_FILE_FORMAT = "gnusolar-project"
DRAFT_3 = "3-draft"

# what a file was migrated from => ending of the copy that is kept of it
BACKUP_ENDINGS = {2: ".v2", DRAFT_3: ".v3-draft"}


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
    # what the file was, None for the current version
    site._migratedFrom = migratedFrom


# The plain site data of a file, migrated to the current version, and what
# it was migrated from (None: nothing).
def _migrate(data, taken=None, files=None, report=None):
    version = data.get("version")
    if data.get("format") == FILE_FORMAT:
        if not isinstance(version, int) or version > FILE_VERSION or version < FILE_VERSION:
            raise Exception("File version " + str(version) + " is not supported, a newer GnuSolar is needed")
        return data.get("site"), None
    if data.get("format") == OLD_FILE_FORMAT:
        if version == 2:
            return migrate_v2.migrate(data.get("project"), taken=taken, files=files, report=report), 2
        if version == 3:
            return fromDraft3(data.get("project")), DRAFT_3
        raise Exception("File version " + str(version) + " is not supported, a newer GnuSolar is needed")
    if "py/state" in data:
        raise Exception("Old file format (version 1), convert it with tools/migrate_pvp.py of GnuSolar commit cbb39e5")
    raise Exception("Not a GnuSolar file")


# The site of a draft of version 3: "orders" are "projects", "orderId" is
# "projectId", and the fields of the section "site" are fields of the site
# itself. Data of plugins (ext) is not looked into.
def fromDraft3(old):
    def rename(node):
        if isinstance(node, list):
            return [rename(v) for v in node]
        if not isinstance(node, dict):
            return node
        return {{"orderId": "projectId"}.get(key, key): value if key == "ext" else rename(value)
                for key, value in node.items()}

    new = rename(old or {})
    if "orders" in new:
        new["projects"] = new.pop("orders")
    place = new.pop("site", None) or {}
    for key, value in place.items():
        if key != "ext":
            new[key] = value
    # both had an ext: one namespace per plugin, their fields put together
    _fill(new.setdefault("ext", {}), place.get("ext") or {})
    return new


# add the values of other which main doesn't have, dict by dict
def _fill(main, other):
    for key, value in other.items():
        if isinstance(value, dict) and isinstance(main.get(key), dict):
            _fill(main[key], value)
        else:
            main.setdefault(key, value)


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
    migratedFrom = getattr(site, "_migratedFrom", None)
    if migratedFrom and os.path.isfile(path):
        backupPath = path + BACKUP_ENDINGS[migratedFrom]
        if not os.path.exists(backupPath):
            shutil.copy2(path, backupPath)

    tmpPath = path + ".tmp"
    with open(tmpPath, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmpPath, path)
    site._migratedFrom = None
