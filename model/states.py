#!/usr/bin/python
# -*- coding: utf-8 -*-

# States of projects and steps (doc/file_format_v3/file_format.md, section 12),
# derived from their dates. Works on plain values, so the migration can use it
# too.

# the states of a step, in the order they are reached
STEP_STATES = ("ordered", "filled", "signed", "submitted", "approved", "paid")


# State of a project from its dates. project: field => value, quoted: True if a
# quote was sent for it.
def projectState(project, quoted=False):
    if project.get("rejected"):
        return "rejected"
    if project.get("completed") or project.get("archived"):
        return "completed"
    if project.get("inactive"):
        return "inactive"
    if project.get("commissioned"):
        return "in_operation"
    if project.get("ordered"):
        return "running"
    if quoted:
        return "quoted"
    return "inquiry"


# State of a step from its dates: the furthest state that was reached
def stepState(dates):
    dates = dates or {}
    if dates.get("rejected"):
        return "rejected"
    state = "open"
    for name in STEP_STATES:
        if dates.get(name):
            state = name
    return state
