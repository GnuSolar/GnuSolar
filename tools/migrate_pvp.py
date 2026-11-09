#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Convert all plant.pvp files below a folder to the current file format,
# by opening and saving them, like GnuSolar does when a project is saved.
#
#   python3 tools/migrate_pvp.py <projectRoot>                    dry run, changes nothing
#   python3 tools/migrate_pvp.py <projectRoot> --write <backup.tar.gz>
#
# Checks before anything is written:
#  - the converted file loads to exactly the same project as the original
#  - no value of the original file is lost (lists the values that would be)
# With --write all plant.pvp files are first saved into the backup archive.

import os
import sys
import json
import tarfile

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(repo, "site-packages"))
sys.path.insert(0, repo)

from model.PvProject import PvProject


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


# the values of the old file which are not in the new one
def lost_values(old_json, new_json):
    new_values = {str(v) for p, v in leaves(json.loads(new_json))}
    lost = []
    for path, value in leaves(json.loads(old_json)):
        if value in (None, "", False, 0) or "py/" in path.rsplit("/", 1)[-1]:
            continue
        if str(value) not in new_values:
            lost.append((path, value))
    return lost


def convert(path):
    old_json = open(path).read()
    project = PvProject(path)
    new_json = project.toJson()
    if new_json == old_json:
        return "current", None, []

    # the new file must load to the same project
    reloaded = PvProject()
    reloaded._savePath = path
    reloaded.fromJson(new_json)
    if reloaded.toJson() != new_json:
        raise Exception("converted file does not load to the same project")

    return "convert", new_json, lost_values(old_json, new_json)


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
    print("projects: %d, already current: %d, to convert: %d, errors: %d" % (
        len(files), len(results) - len(todo), len(todo), len(errors)))
    for f, e in errors:
        print("  ERROR " + os.path.relpath(f, root) + ": " + e)
    for f, (state, new_json, lost) in todo.items():
        for path, value in lost:
            print("  LOST  %s: %s = %r" % (os.path.relpath(f, root), path, value))

    if not write:
        print("dry run, nothing written")
        return 1 if errors else 0
    if errors:
        print("not written, fix the errors first")
        return 1

    # backup of all project files, then write
    backup = args[2]
    if os.path.exists(backup):
        print("backup exists already: " + backup)
        return 1
    with tarfile.open(backup, "w:gz") as tar:
        for f in files:
            tar.add(f, arcname=os.path.relpath(f, root))
    print("backup: %s (%d files)" % (backup, len(files)))

    for f, (state, new_json, lost) in todo.items():
        tmp = f + ".tmp"
        with open(tmp, "w") as out:
            out.write(new_json)
        os.replace(tmp, f)
    print("converted: %d" % len(todo))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
