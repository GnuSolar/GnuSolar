#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# The native GnuSolar project file (plant.pvp), plain JSON in UTF-8:
#
#   version 2: {"format": "gnusolar-project", "version": 2, "project": {...}}
#              "project" is PvProject.toDict()
#   version 1: jsonpickle, no longer read. All projects were converted on
#              2026-11-09 with tools/migrate_pvp.py, see git history.
#
# A future version 3 gets a migration from version 2 in _migrate(), working on
# the plain data, so older files keep opening.

import os
import json

FILE_FORMAT = "gnusolar-project"
FILE_VERSION = 2


# the file content of a project
def dumps(project):
    data = {"format": FILE_FORMAT, "version": FILE_VERSION, "project": project.toDict()}
    return json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False)


# fill a project from file content
def loads(project, text):
    project.fromDict(_migrate(json.loads(text)))
    project.link(project)


# the plain project data of a file, migrated to the current version
def _migrate(data):
    if data.get("format") == FILE_FORMAT:
        version = data.get("version")
        if version != FILE_VERSION:
            # migrations of older versions go here, one per version
            raise Exception("File version " + str(version) + " is not supported, a newer GnuSolar is needed")
        return data["project"]
    if "py/state" in data:
        raise Exception("Old file format (version 1), convert it with tools/migrate_pvp.py of GnuSolar commit cbb39e5")
    raise Exception("Not a GnuSolar project file")


# fill a project from a file
def load(project, path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    loads(project, text)


# Write a project to a file. Writes a temporary file and renames it,
# so a crash never leaves a half written project.
def save(project, path):
    text = dumps(project)
    tmpPath = path + ".tmp"
    with open(tmpPath, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmpPath, path)
