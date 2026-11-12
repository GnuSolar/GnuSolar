#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Convert all plant.pvp files below a folder to the current file format,
# by opening and saving them, like GnuSolar does when a site is saved.
#
#   python3 tools/migrate_pvp.py <projectRoot>                    dry run, changes nothing
#   python3 tools/migrate_pvp.py <projectRoot> --write <backup.tar.gz>
#
# Checks before anything is written:
#  - the converted file loads to exactly the same site
#  - every value of the old file is still there: the site is read back
#    through the fields of the old version (site.building, site.plant,
#    site.progress, ...) and compared with the old file
# It lists what the migration could not place: values kept in
# ext.gnusolar.v2, dates that are no dates (kept in the notes) and projects
# that need a look by hand.
# With --write all plant.pvp files are first saved into the backup archive.

import os
import sys
import json
import tarfile

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(repo, "site-packages"))
sys.path.insert(0, repo)

from model.PvSite import PvSite
from formats.migrate_v2 import Report
import formats.pvp

# fields of version 2 which version 3 doesn't have on purpose
DROPPED = ("/state", "/municipality/fkPowerCompany", "/powerCompany/fkContactTag")


def find_projects(root):
    ret = []
    for dirname, dirnames, filenames in os.walk(root):
        if '.git' in dirnames:
            dirnames.remove('.git')
        if "plant.pvp" in filenames:
            ret.append(os.path.join(dirname, "plant.pvp"))
    return sorted(ret)


# all leaf values of a json document, with their path
def leaves(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from leaves(v, path + "/" + k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from leaves(v, path + "/" + str(i))
    else:
        yield path, node


def _norm(value):
    if value is None or value is False:
        return ""
    return str(value).strip()


# the same value, as text or as number
def same(old, new):
    old, new = _norm(old), _norm(new)
    if old == new:
        return True
    try:
        a, b = float(old.replace(",", ".")), float(new.replace(",", "."))
    except ValueError:
        return False
    return abs(a - b) <= 1e-6 * max(1, abs(a))


# The value a version 2 field has in the migrated site
def new_value(site, path):
    parts = path.strip("/").split("/")
    if parts[:2] == ["contacts", "contacts"]:
        role = {"owner": "owner", "installer_ac": "electrician"}.get(parts[2], parts[2])
        obj = site.contacts.withRole(role)
        if obj is None:
            return None
        parts = parts[3:]
    else:
        obj = site
    for part in parts:
        obj = getattr(obj, part)
    return obj


# the values of a version 2 file which the migrated site doesn't give back
def lost_values(old, site, report):
    noted = {p.replace(".", "/") for p, v in report.notes} | {p.replace(".", "/") for p, v in report.kept}
    lost = []
    for path, value in leaves(old):
        if _norm(value) == "" or path in DROPPED or path.strip("/") in noted:
            continue
        name = path.rsplit("/", 1)[-1]
        if name == "role":
            continue
        try:
            new = new_value(site, path)
        except AttributeError:
            lost.append((path, value))
            continue
        # coordinates: LV95 with 7 digits comes back as LV03 with 6
        if name in ("swissGridX", "swissGridY") and not same(value, new):
            try:
                offset = 2000000 if name == "swissGridX" else 1000000
                if same(float(str(value).strip()) - offset, new):
                    continue
            except ValueError:
                pass
        # the second phone or email moves up if there is no first
        if name in ("phone2", "email2") and not same(value, new):
            first = new_value(site, path[:-1])
            if same(value, first):
                continue
        # a quote moves up if an earlier one is missing
        if name in ("quote2Sent", "quote3Sent", "quote4Sent") and not same(value, new):
            if any(same(value, getattr(site.progress, "quote%dSent" % n)) for n in (1, 2, 3)):
                continue
        if not same(value, new):
            lost.append((path, value))
    return lost


# The values of a draft of version 3 which are not where they belong after the
# renaming (formats.pvp.fromDraft3). It only moves values: what was at
# site.x is at x, orders are projects, orderId is projectId.
def lost_draft_values(old):
    def leaves(node, path=()):
        if isinstance(node, dict):
            return [leaf for key, value in node.items() for leaf in leaves(value, path + (key,))]
        if isinstance(node, list):
            return [leaf for i, value in enumerate(node) for leaf in leaves(value, path + (i,))]
        return [(path, node)]

    def moved(path):
        if path[0] == "site":
            path = path[1:]
        elif path[0] == "orders":
            path = ("projects",) + path[1:]
        if "ext" not in path and path[-1] == "orderId":
            path = path[:-1] + ("projectId",)
        return path

    new = dict(leaves(formats.pvp.fromDraft3(old)))
    missing = object()
    return [(".".join(str(key) for key in path), value) for path, value in leaves(old)
            if new.get(moved(path), missing) != value]


def convert(path):
    old_json = open(path, encoding="utf-8").read()
    old = json.loads(old_json)
    report = Report()
    site = PvSite()
    formats.pvp.load(site, path, report=report)
    if not site._migratedFrom:
        return "current", None, [], report

    site._savePath = path
    if site._migratedFrom == 2:
        lost = lost_values(old.get("project"), site, report)
    else:
        lost = lost_draft_values(old.get("project"))
    site.prepareSave()
    new_json = formats.pvp.dumps(site)

    # the new file must load to the same site
    reloaded = PvSite()
    formats.pvp.loads(reloaded, new_json)
    if formats.pvp.dumps(reloaded) != new_json:
        raise Exception("converted file does not load to the same site")

    return "convert", new_json, lost, report


def main(args):
    if len(args) not in (1, 3) or (len(args) == 3 and args[1] != "--write"):
        print("usage: migrate_pvp.py <projectRoot> [--write <backup.tar.gz>]")
        return 2
    root = args[0]
    write = len(args) == 3
    files = find_projects(root)

    results = {}
    errors = []
    for f in files:
        try:
            results[f] = convert(f)
        except Exception as e:
            errors.append((f, "%s: %s" % (type(e).__name__, e)))

    todo = {f: r for f, r in results.items() if r[0] == "convert"}
    print("files: %d, already current: %d, to convert: %d, errors: %d" % (
        len(files), len(results) - len(todo), len(todo), len(errors)))
    for f, e in errors:
        print("  ERROR " + os.path.relpath(f, root) + ": " + e)
    lostCount = 0
    for f, (state, new_json, lost, report) in todo.items():
        name = os.path.relpath(os.path.dirname(f), root)
        for path, value in lost:
            lostCount += 1
            print("  LOST   %s: %s = %r" % (name, path, value))
        for path, value in report.manual:
            print("  CHECK  %s: %s = %r (two dates: two projects?)" % (name, path, value))
        for path, value in report.notes:
            if (path, value) not in report.manual:
                print("  NOTE   %s: %s = %r (no date, kept in the notes)" % (name, path, value))
        for path, value in report.kept:
            if path != "building.buildingState":
                print("  KEPT   %s: %s = %r (in ext.gnusolar.v2)" % (name, path, value))
    kept = sum(len(r[3].kept) for r in todo.values())
    print("lost values: %d, kept in ext.gnusolar.v2: %d (buildingState: %d)" % (
        lostCount, kept, sum(1 for r in todo.values() for p, v in r[3].kept if p == "building.buildingState")))

    if not write:
        print("dry run, nothing written")
        return 1 if errors or lostCount else 0
    if errors or lostCount:
        print("not written, fix the errors and lost values first")
        return 1

    # backup of all site files, then write
    backup = args[2]
    if os.path.exists(backup):
        print("backup exists already: " + backup)
        return 1
    with tarfile.open(backup, "w:gz") as tar:
        for f in files:
            tar.add(f, arcname=os.path.relpath(f, root))
    print("backup: %s (%d files)" % (backup, len(files)))

    for f, (state, new_json, lost, report) in todo.items():
        tmp = f + ".tmp"
        with open(tmp, "w", encoding="utf-8") as out:
            out.write(new_json)
        os.replace(tmp, f)
    print("converted: %d" % len(todo))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
