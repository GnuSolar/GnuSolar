# Plugins and country extensions (doc/file_format.md, section 13).
#
# A plugin stores its data in the "ext" field of the object it belongs to,
# under its own id. A country extension is a plugin named by the country's
# code: it holds what exists only in that country and defines the steps with
# its authorities.
#
#   ch.py   Switzerland

import importlib

# id => module name
AVAILABLE = {
    "ch": "plugins.ch",
}


# the module of a plugin, None if GnuSolar doesn't have it
def get(pluginId):
    name = AVAILABLE.get(pluginId)
    return importlib.import_module(name) if name else None


# The modules of the plugins the user enabled ("plugins" in config.json).
# A plugin that is not enabled offers nothing in the program; its data in a
# project file is kept all the same.
def enabled():
    from Config import config
    return [get(pluginId) for pluginId in config.plugins if pluginId in AVAILABLE]


# all ext namespaces used anywhere in plain project data
def usedNamespaces(node, found=None):
    found = set() if found is None else found
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "ext" and isinstance(value, dict):
                found.update(value.keys())
            usedNamespaces(value, found)
    elif isinstance(node, list):
        for value in node:
            usedNamespaces(value, found)
    return found


# The entries of the project's "plugins" list: every plugin that has data in
# the file. Entries of plugins GnuSolar doesn't know are kept as they are.
def pluginList(projectData):
    known = {p.get("id"): p for p in projectData.get("plugins") or [] if isinstance(p, dict)}
    ret = []
    for pluginId in sorted(usedNamespaces(projectData) | set(known)):
        module = get(pluginId)
        if module:
            ret.append({"id": pluginId, "name": module.NAME, "version": module.VERSION})
        elif pluginId in known:
            ret.append(known[pluginId])
    return ret
