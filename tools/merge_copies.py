#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Merge the folder of a further project at the same address ("Heid 2.3_2"
# next to "Heid 2.3") into the main site: the project of the copy becomes a
# project of the main site, with its folder pointing to the copy
# (doc/file_format.md, section 15).
#
#   python3 tools/merge_copies.py --list <projectRoot>      the copies found, changes nothing
#   python3 tools/merge_copies.py <main folder> <copy folder>            dry run, changes nothing
#   python3 tools/merge_copies.py <main folder> <copy folder> --write
#
# With --write the main plant.pvp is saved as plant.pvp.before_merge (once,
# also when several copies are merged) and then written with both projects in it; the plant.pvp of the copy is renamed to
# plant.pvp.merged, so the site is no longer listed twice. No other file
# is touched, the folder of the copy stays where it is.
#
# What is taken from the copy: its projects with designs, quotes, steps and
# invoices, devices, types, module groups, strings, connections, and contacts
# and values of the place the main site doesn't have. The address, the
# municipality and the grid operator of the main site stay.

import os
import re
import sys
import json
import shutil

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(repo, "site-packages"))
sys.path.insert(0, repo)

COPY_NAME = re.compile(r"^(.+)_(\d+)$")


# (main folder, copy folder) of all copies below root
def find_copies(root):
    ret = []
    for dirname, dirnames, filenames in os.walk(root):
        if '.git' in dirnames:
            dirnames.remove('.git')
        if "plant.pvp" not in filenames:
            continue
        m = COPY_NAME.match(os.path.basename(dirname))
        if not m:
            continue
        main = os.path.join(os.path.dirname(dirname), m.group(1))
        if os.path.isfile(os.path.join(main, "plant.pvp")):
            ret.append((main, dirname))
    return sorted(ret)


def _contact_key(contact):
    address = contact.get("address") or {}
    return tuple((contact.get(k) or "").strip().lower() for k in ("organization", "firstName", "lastName")) + \
        tuple((address.get(k) or "").strip().lower() for k in ("street", "streetNumber", "zip"))


def _type_key(deviceType):
    return json.dumps({k: v for k, v in deviceType.items() if k != "id"}, sort_keys=True)


# replace ids in plain data
def _remap(node, ids):
    if isinstance(node, dict):
        return {k: _remap(v, ids) for k, v in node.items()}
    if isinstance(node, list):
        return [_remap(v, ids) for v in node]
    if isinstance(node, str) and node in ids:
        return ids[node]
    return node


# fill the values main doesn't have from other
def _fill(main, other, path, notes):
    for key, value in other.items():
        if key in ("taken", "ext"):
            continue
        if key not in main or main[key] in (None, "", [], {}):
            main[key] = value
        elif isinstance(main[key], dict) and isinstance(value, dict):
            _fill(main[key], value, path + key + ".", notes)
        elif main[key] != value and not isinstance(value, (dict, list)):
            notes.append("differs, main site kept: %s%s = %r (copy: %r)" % (path, key, main[key], value))


# the fields of a site that describe the place
PLACE = ("label", "address", "latitude", "longitude", "elevation", "plotNumber", "supply", "annualConsumption",
         "designTemperature", "horizon", "municipality", "gridOperator")


# The plain data of the main site with the copy merged into it.
# folder is the folder of the copy, relative to the main site folder.
# Returns (merged site, notes for the user).
def merge(main, copy, folder):
    main = json.loads(json.dumps(main))
    copy = json.loads(json.dumps(copy))
    notes = []
    ids = {}

    # types: the same type is not added twice
    known = {_type_key(t): t["id"] for t in main.get("types", [])}
    for deviceType in copy.get("types", []):
        if _type_key(deviceType) in known:
            ids[deviceType["id"]] = known[_type_key(deviceType)]
        else:
            main.setdefault("types", []).append(deviceType)

    # the grid operator's meters with the same number are the same meter
    meters = {d.get("number"): d["id"] for d in main.get("devices", []) if d.get("kind") == "meter"}
    devices = []
    for device in copy.get("devices", []):
        if device.get("kind") == "meter" and device.get("number") in meters:
            ids[device["id"]] = meters[device["number"]]
        else:
            devices.append(device)

    # contacts: the same person gets the roles of both
    people = {_contact_key(c): c for c in main.get("contacts", [])}
    for contact in copy.get("contacts", []):
        same = people.get(_contact_key(contact))
        if same is None:
            main.setdefault("contacts", []).append(contact)
            notes.append("contact added: " + " ".join(
                str(contact.get(k)) for k in ("organization", "lastName", "firstName") if contact.get(k)))
        else:
            ids[contact["id"]] = same["id"]
            same["roles"] = same.get("roles", []) + [r for r in contact.get("roles", []) if r not in same.get("roles", [])]

    # module groups go onto the first roof of the main site
    groups = [g for b in copy.get("buildings", []) for r in b.get("roofs", []) for g in r.get("moduleGroups", [])]
    if not main.get("buildings"):
        main["buildings"] = copy.get("buildings", [])
    elif groups:
        building = main["buildings"][0]
        if not building.get("roofs"):
            building["roofs"] = [r for b in copy["buildings"] for r in b.get("roofs", [])][:1]
            building["roofs"][0]["moduleGroups"] = []
        building["roofs"][0].setdefault("moduleGroups", []).extend(groups)

    projects = copy.get("projects", [])
    for project in projects:
        project["folder"] = "/".join(part for part in (folder.replace(os.sep, "/"), project.get("folder")) if part)
        notes.append("project added: %s (%s), folder %s" % (project.get("title"), project.get("state"), project["folder"]))
    main.setdefault("projects", []).extend(projects)
    main.setdefault("devices", []).extend(devices)
    for key in ("strings", "connections", "surroundings"):
        main.setdefault(key, []).extend(copy.get(key, []))

    # documents of the copy are in its folder
    for project in projects:
        for part in project.get("quotes", []) + project.get("steps", []) + project.get("invoices", []):
            for document in part.get("documents", []):
                document["path"] = folder.replace(os.sep, "/") + "/" + document["path"]

    # the place: what the copy knows and the main site doesn't
    _fill(main, {key: copy[key] for key in PLACE if key in copy}, "", notes)

    copyNotes = (copy.get("notes") or "").strip()
    if copyNotes and copyNotes not in (main.get("notes") or ""):
        main["notes"] = ((main.get("notes") or "").rstrip() + "\n\n--- " + folder + " ---\n" + copyNotes).lstrip()

    # the plugins which have data in the merged site
    import plugins
    main["plugins"] = (main.get("plugins") or []) + [
        entry for entry in copy.get("plugins") or [] if entry not in (main.get("plugins") or [])]
    main["plugins"] = plugins.pluginList(main)

    return _remap(main, ids), notes


def _load(folder):
    from model.PvSite import PvSite
    site = PvSite(os.path.join(folder, "plant.pvp"))
    site.prepareSave()
    return site


def merge_folders(mainFolder, copyFolder, write):
    from model.PvSite import PvSite
    import formats.pvp

    mainFolder, copyFolder = os.path.abspath(mainFolder), os.path.abspath(copyFolder)
    main, copy = _load(mainFolder), _load(copyFolder)
    folder = os.path.relpath(copyFolder, mainFolder)
    merged, notes = merge(main.toDict(), copy.toDict(), folder)

    # the merged site must load and write the same again
    site = PvSite()
    site.fromDict(merged)
    site.link(site)
    site._savePath = main._savePath
    if site.toDict() != merged:
        raise Exception("merged site does not load to the same site")

    for note in notes:
        print("  " + note)
    if not write:
        return site

    mainPath = os.path.join(mainFolder, "plant.pvp")
    copyPath = os.path.join(copyFolder, "plant.pvp")
    if os.path.exists(copyPath + ".merged"):
        raise Exception("exists already: " + copyPath + ".merged")
    # with several copies the file from before the first merge is kept
    if not os.path.exists(mainPath + ".before_merge"):
        shutil.copy2(mainPath, mainPath + ".before_merge")
    site.prepareSave()
    formats.pvp.save(site, mainPath)
    os.rename(copyPath, copyPath + ".merged")
    print("  written: " + mainPath)
    return site


def main(args):
    if len(args) == 2 and args[0] == "--list":
        copies = find_copies(args[1])
        for mainFolder, copyFolder in copies:
            print(os.path.relpath(copyFolder, args[1]) + "  ->  " + os.path.relpath(mainFolder, args[1]))
            try:
                merge_folders(mainFolder, copyFolder, write=False)
            except Exception as e:
                print("  ERROR %s: %s" % (type(e).__name__, e))
        print("copies: %d, nothing written" % len(copies))
        return 0
    if len(args) not in (2, 3) or (len(args) == 3 and args[2] != "--write"):
        print("usage: merge_copies.py --list <projectRoot>")
        print("       merge_copies.py <main folder> <copy folder> [--write]")
        return 2
    merge_folders(args[0], args[1], write=len(args) == 3)
    if len(args) == 2:
        print("dry run, nothing written")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
