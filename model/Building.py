#!/usr/bin/python
# -*- coding: utf-8 -*-

# Buildings, roofs, obstacles and module groups (doc/file_format.md,
# section 6). Lengths and positions are in mm, angles in degrees, the azimuth
# counts from north clockwise.

from model.ModelNode import ModelNode

ROOF_KINDS = ("pitched", "flat", "facade", "ground", "carport")
ROOF_COVERINGS = ("tiles", "slate", "metal", "standing_seam", "trapezoidal", "fibre_cement", "membrane", "gravel",
                  "green", "other")
OBSTACLE_KINDS = ("chimney", "window", "skylight", "dormer", "vent", "solar_thermal", "blocked", "firewall",
                  "tree", "other")
OBSTACLE_SHAPES = ("rect", "circle", "polygon")
MOUNTINGS = ("on_roof", "in_roof", "flat_roof_east_west", "flat_roof_south", "facade", "ground")
ORIENTATIONS = ("portrait", "landscape")
SURROUNDING_KINDS = ("tree", "building", "wall", "mast", "terrain", "other")


# A block of identical modules on a roof
class ModuleGroup(ModelNode):

    _types = {"rows": "int", "columns": "int", "count": "int", "x": "number", "y": "number", "gapX": "number",
              "gapY": "number", "tilt": "number", "azimuth": "number", "rowPitch": "number", "panels": "json",
              "ext": "json"}

    def __init__(self, top=None):
        self._top = top
        self.id = None
        self.designId = None                # the design this group belongs to
        self.typeId = None                  # the module
        self.mounting = None                # see MOUNTINGS
        self.mountingSystemTypeId = None
        self.orientation = None             # see ORIENTATIONS
        self.rows = None
        self.columns = None
        self.count = None                   # number of modules
        self.x = None
        self.y = None
        self.gapX = None
        self.gapY = None
        self.tilt = None                    # of the modules, where it differs from the roof
        self.azimuth = None
        self.rowPitch = None
        self.panels = []                    # single modules, only where they matter
        self.ext = {}

    # the module type, None if not known
    def getType(self):
        return self._top.byId("types", self.typeId) if self._top else None

    # power of all modules in W, None if not known
    def getPower(self):
        moduleType = self.getType()
        power = moduleType.specs.get("power") if moduleType else None
        if power is None or self.count is None:
            return None
        return power * self.count


class Obstacle(ModelNode):

    _types = {"x": "number", "y": "number", "width": "number", "height": "number", "radius": "number",
              "points": "points", "ext": "json"}

    def __init__(self, top=None):
        self._top = top
        self.id = None
        self.kind = None        # see OBSTACLE_KINDS
        self.shape = None       # see OBSTACLE_SHAPES
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.radius = None
        self.points = []
        self.ext = {}


class Margins(ModelNode):

    _types = {"eave": "number", "ridge": "number", "left": "number", "right": "number"}

    def __init__(self, top=None):
        self._top = top
        self.eave = None
        self.ridge = None
        self.left = None
        self.right = None


class Roof(ModelNode):

    _parts = {"obstacles": Obstacle, "moduleGroups": ModuleGroup}
    _types = {"x": "number", "y": "number", "z": "number", "azimuth": "number", "inclination": "number",
              "eaveHeight": "number", "ridgeHeight": "number", "outline": "points", "ext": "json"}

    def __init__(self, top=None):
        self._top = top
        self.id = None
        self.label = None
        self.kind = None            # see ROOF_KINDS
        self.covering = None        # see ROOF_COVERINGS
        self.x = None               # the left end of the eave, in the building's coordinates
        self.y = None
        self.z = None
        self.azimuth = None         # the direction the surface faces
        self.inclination = None
        self.eaveHeight = None
        self.ridgeHeight = None
        self.margins = Margins(top)
        self.outline = []           # [[x, y], ...] in the roof's coordinates
        self.obstacles = []
        self.moduleGroups = []
        self.ext = {}


class Building(ModelNode):

    _parts = {"roofs": Roof}
    _types = {"x": "number", "y": "number", "z": "number", "azimuth": "number", "model": "json", "ext": "json"}

    def __init__(self, top=None):
        self._top = top
        self.id = None
        self.label = None
        self.x = None
        self.y = None
        self.z = None
        self.azimuth = None
        self.roofs = []
        self.model = {}             # a 3D model file in the site folder
        self.ext = {}


# Something next to the buildings that throws shade
class Surrounding(ModelNode):

    _types = {"x": "number", "y": "number", "z": "number", "height": "number", "radius": "number",
              "outline": "points", "ext": "json"}

    def __init__(self, top=None):
        self._top = top
        self.id = None
        self.kind = None            # see SURROUNDING_KINDS
        self.label = None
        self.x = None
        self.y = None
        self.z = None
        self.height = None
        self.radius = None
        self.outline = []
        self.ext = {}
