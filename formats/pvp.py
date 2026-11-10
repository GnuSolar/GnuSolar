#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The native GnuSolar project file (plant.pvp), plain JSON in UTF-8:
#
#   {"format": "gnusolar-project", "version": 3, "project": {...}}
#
#   version 3: doc/file_format.md. "project" is PvProject.toDict()
#   version 2: one building, one plant, one progress. Migrated when read
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

FILE_FORMAT = "gnusolar-project"
FILE_VERSION = 3

# ending of the copy of the file before it was migrated
BACKUP_ENDING = ".v2"


# the file content of a project
def dumps(project):
    data = {"format": FILE_FORMAT, "version": FILE_VERSION, "project": project.toDict()}
    return json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False)


# Fill a project from file content. taken and files are for the migration of
# older versions: the date of the file and the files of the project folder.
def loads(project, text, taken=None, files=None, report=None):
    data = json.loads(text)
    version = data.get("version")
    project.fromDict(_migrate(data, taken, files, report))
    project.link(project)
    # the version the file had, None for the current one
    project._migratedFrom = version if version != FILE_VERSION else None


# the plain project data of a file, migrated to the current version
def _migrate(data, taken=None, files=None, report=None):
    if data.get("format") == FILE_FORMAT:
        version = data.get("version")
        project = data.get("project")
        if not isinstance(version, int) or version > FILE_VERSION or version < 2:
            raise Exception("File version " + str(version) + " is not supported, a newer GnuSolar is needed")
        # one migration per version
        if version == 2:
            project = migrate_v2.migrate(project, taken=taken, files=files, report=report)
        return project
    if "py/state" in data:
        raise Exception("Old file format (version 1), convert it with tools/migrate_pvp.py of GnuSolar commit cbb39e5")
    raise Exception("Not a GnuSolar project file")


# the files of the folders with quotes and invoices, relative to the project folder
def _projectFiles(projectDir):
    ret = []
    for folder in ("off", "fin"):
        path = os.path.join(projectDir, folder)
        if os.path.isdir(path):
            ret.extend(folder + "/" + name for name in sorted(os.listdir(path)))
    return ret


# fill a project from a file
def load(project, path, report=None):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    taken = values.dayToTimestamp(date.fromtimestamp(os.path.getmtime(path)))
    loads(project, text, taken=taken, files=_projectFiles(os.path.dirname(os.path.abspath(path))), report=report)


# Write a project to a file. Writes a temporary file and renames it,
# so a crash never leaves a half written project.
def save(project, path):
    text = dumps(project)

    # keep the file of the older version, once
    if getattr(project, "_migratedFrom", None) and os.path.isfile(path):
        backupPath = path + BACKUP_ENDING
        if not os.path.exists(backupPath):
            shutil.copy2(path, backupPath)

    tmpPath = path + ".tmp"
    with open(tmpPath, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmpPath, path)
    project._migratedFrom = None
