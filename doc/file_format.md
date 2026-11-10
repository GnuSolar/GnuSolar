# GnuSolar project file, version 3

Draft. Version 2 is the current format (see `formats/pvp.py`); this document describes version 3, the next one.

A project file describes one solar project: the site, the people involved, the buildings and roofs, the devices
installed over time, and the quotes and orders that brought them there. GnuSolar reads and writes it, and any other
program can too: the format is plain JSON and documented here.

Version 2 stores the existing model (one building, one plant, one progress) as plain JSON. Version 3 changes the
model: one project holds several orders, devices with their history, roofs, quotes and plugin data. GnuSolar converts
version 2 files when it opens them (section 14).

## 1. Principles

- **One project, one file.** A project is one site, usually one building or a group of buildings at one address.
  Every order at that site, the first installation as well as a battery ten years later, lives in the same file.
- **Readable without GnuSolar.** Plain JSON, English keys, documented units. No class names, no pickled objects.
- **Complete on its own.** The file holds copies of the device types it uses and a snapshot of the master data it
  relied on (grid operator, municipality), so it can be read without a database.
- **History, not only the current state.** Devices have a start and an end date. Replaced devices stay in the file.
- **No secrets.** Passwords, tokens and access codes never go into a project file.
- **The installation, not the simulation.** The file describes what is planned and what is built. The inputs and
  results of a simulation (weather data, loss settings, hourly values, screenshots) stay in the files of the
  simulation tool, which are referenced as documents. Only their outcome, such as the expected yield, is copied.
- **Keep what you don't know.** A program that reads a project file must write back every field it doesn't know,
  unchanged. This keeps plugin data and fields of newer minor revisions safe.

## 2. The file

| | |
|---|---|
| Name | `plant.pvp`, one per project folder |
| Encoding | UTF-8, no byte order mark, characters such as umlauts written as they are |
| Syntax | JSON (RFC 8259), no comments |
| Formatting | 4 spaces indent, keys sorted, so files diff well (`json.dumps(..., indent=4, sort_keys=True, ensure_ascii=False)`) |
| Writing | to `plant.pvp.tmp` first, then renamed, so a crash never leaves a half written file |
| Attachments | Not in the file. Documents stay in the project folder and are referenced by relative path. |

### Envelope

```json
{
    "format": "gnusolar-project",
    "version": 3,
    "project": {}
}
```

| Field | Content |
|---|---|
| `format` | Always `"gnusolar-project"` |
| `version` | The format version. It changes only when existing readers can no longer read the file correctly. Adding optional fields does not change it. |
| `project` | The project, sections 4 to 12 |

A reader that finds a higher `version` than it knows refuses the file instead of guessing, so an older GnuSolar never
damages a newer file. A reader that finds a lower `version` migrates it, one version step at a time, on the plain
data (`formats/pvp.py: _migrate()`).

### The project object

```json
"project": {
    "id": "uuid",
    "created": "2026-11-10T14:00:00+01:00",
    "modified": "2026-11-10T14:00:00+01:00",
    "generator": "GnuSolar git...c96ce2c",
    "site": {},
    "contacts": [],
    "buildings": [],
    "surroundings": [],
    "types": [],
    "devices": [],
    "strings": [],
    "designs": [],
    "quotes": [],
    "orders": [],
    "notes": "",
    "plugins": [],
    "ext": {}
}
```

## 3. Conventions

### IDs and references

- Every object in a list has an `id`: a UUID (version 4) in lower case, as a string.
- IDs never change and are never reused, also not after an object is removed.
- A reference to another object is a field ending in `Id` (or `Ids` for a list), holding that object's `id`.

UUIDs let two copies of a file, for example synced with Syncthing, be merged object by object.

### Dates and times

- A date is an ISO 8601 date string: `"2026-11-10"`.
- A point in time is an ISO 8601 date-time with its offset: `"2026-11-10T14:00:00+01:00"`.

### Missing values

- A value that is not known is left out or `null`. The empty string `""` means an empty text, never "not known";
  numbers and dates are never `""`.

### Units

| Quantity | Unit | Example |
|---|---|---|
| Length, position | mm | `"width": 1134` |
| Area | m² | `"area": 98.3` |
| Cross-section of a cable | mm² | `"crossSection": 6` |
| Mass | kg | `"weight": 21.5` |
| Angle | degree | `"inclination": 30` |
| Azimuth | degree from north, clockwise (0 = north, 90 = east, 180 = south) | `"azimuth": 180` |
| Power | W | `"powerAc": 10000` |
| Apparent power | VA | `"apparentPower": 11000` |
| Energy | Wh | `"capacity": 10240` |
| Voltage | V | `"voc": 41.2` |
| Current | A | `"isc": 13.9`, `"mainFuse": 40` |
| Temperature | °C | |
| Percent | % (0–100) | `"efficiency": 21.3` |
| Money | the amount as a number, with a `currency` field (ISO 4217, default `"CHF"`) | `"amount": 18450.00` |
| Swiss coordinates | LV95 (EPSG 2056), metres | `"e": 2632561.2` |

Numbers are JSON numbers, never strings, and use a decimal point. Field names never carry a unit (`powerAc`, not
`powerAcKw`). Device values use the names of ModbusSpec's `vocabulary.yaml` where one exists.

### Values

- Enumerations are lower-case strings in `snake_case`, for example `"heat_pump"`.
- Text in the file is in the language of its users (usually German). Keys are English.

## 4. Site

The place where the system stands.

```json
"site": {
    "label": "Einfamilienhaus Muster",
    "address": { "street": "Kirchweg", "streetNumber": "26", "zip": "4314", "city": "Zeiningen", "region": null, "country": "CH" },
    "latitude": 47.5419,
    "longitude": 7.8696,
    "elevation": 330,
    "swissGrid": { "e": 2632561.2, "n": 1265432.8 },
    "plotNumber": "1060",
    "buildingIds": ["190335642"],
    "zone": { "code": "11", "name": "Wohnzonen" },
    "mainFuse": 40,
    "annualConsumption": 4500000,
    "designTemperature": { "minAmbient": -10, "maxCell": 70 },
    "horizon": [[0, 2], [90, 5], [180, 8], [270, 3]],
    "meters": [
        { "id": "uuid", "number": "12345678", "kind": "bidirectional", "from": "2015-03-21", "to": null }
    ],
    "municipality": { "taken": "2026-11-10", "code": "4264", "name": "Zeiningen", "…": "snapshot, see below" },
    "gridOperator": { "taken": "2026-11-10", "id": 402, "vseId": null, "name": "Elektra Zeiningen", "…": "snapshot, see below" }
}
```

| Field | Content |
|---|---|
| `latitude`, `longitude` | WGS84, degrees. Origin of the coordinate system (section 6). |
| `elevation` | Metres above sea level |
| `swissGrid` | LV95 coordinates, metres |
| `plotNumber` | Parcel number (Parzelle) |
| `buildingIds` | Federal building IDs (EGID) |
| `zone` | Building zone (ARE): code and name |
| `mainFuse` | Rating of the house connection fuse, A |
| `annualConsumption` | Electricity the site uses per year, Wh |
| `designTemperature` | For sizing strings: `minAmbient` is the lowest ambient temperature (it gives the highest open-circuit voltage), `maxCell` the highest cell temperature (it gives the lowest MPP voltage), °C |
| `horizon` | The horizon line seen from the site, as `[azimuth, elevation]` pairs in degrees |
| `meters` | The grid operator's meters, with `from`/`to` because they get replaced. `kind` is `consumption`, `bidirectional` or `production`. Meters that belong to the system itself are devices (section 8). |

### Master data snapshots

`municipality` and `gridOperator` are copies of GnuSolar's master data (`master.db`) as they were when the project
used them, so a TAG from 2019 still shows the grid operator contact of 2019. `taken` is the date of the copy; `id`
refers to the master data row it came from. GnuSolar may refresh a snapshot, and then sets a new `taken`.

```json
"municipality": {
    "taken": "2026-11-10",
    "id": 4264, "code": "4264", "name": "Zeiningen",
    "countryCode": "CH", "stateCode": "AG", "districtCode": null,
    "website": "https://www.zeiningen.ch",
    "buildingFormId": 7,
    "mainContact": { "organization": "Gemeinde Zeiningen", "address": {}, "channels": [] },
    "buildingContact": { "organization": "Bauverwaltung", "address": {}, "channels": [] }
},
"gridOperator": {
    "taken": "2026-11-10",
    "id": 402, "vseId": null, "name": "Elektra Zeiningen",
    "address": { "street": "Kirchweg", "streetNumber": "26", "zip": "4314", "city": "Zeiningen" },
    "tagFormId": 4, "iaFormId": null,
    "mainContact": { "organization": "Elektra Zeiningen", "address": {}, "channels": [] },
    "tagContact": { "organization": "IBW Technik AG", "address": {}, "channels": [] }
}
```

The contacts inside a snapshot have the form of section 5 without `id`, `roles`, `from` and `to`.

## 5. Contacts

People and companies involved in the project, each with one or more roles.

```json
"contacts": [
    {
        "id": "uuid",
        "roles": ["owner", "client"],
        "organization": null,
        "department": null,
        "title": "Herr",
        "firstName": "Hans",
        "middleName": null,
        "lastName": "Muster",
        "nickName": null,
        "address": { "street": "Kirchweg", "streetNumber": "26", "address1": null, "address2": null, "floor": null, "room": null, "zip": "4314", "city": "Zeiningen", "country": "CH" },
        "channels": [
            { "kind": "phone", "value": "061 000 00 00" },
            { "kind": "email", "value": "hans@example.ch" }
        ],
        "bankAccounts": [
            { "owner": "Hans Muster", "bank": "Raiffeisen", "iban": "CH00 0000 0000 0000 0000 0", "iid": null, "bic": null }
        ],
        "from": null,
        "to": null
    }
]
```

| Role | Meaning |
|---|---|
| `owner` | Owner of the building or system |
| `client` | Who orders the work (Bauherr) |
| `billing` | Invoice recipient |
| `tenant` | Tenant, user of the building |
| `electrician` | Electrical installer (AC side) |
| `architect`, `planner` | Architect, planner |
| `roofer` | Roofer, tinsmith |
| `contact` | Other contact person |

`channels[].kind` is one of `phone`, `mobile`, `email`, `fax`, `web`; the order of the channels is their priority.
`from`/`to` mark a change of owner without losing the old one.

The grid operator and the municipality are not contacts: they are snapshots in `site` (section 4). The installer is
the user of the program, not a contact.

## 6. Buildings, roofs and modules

### Coordinate system

The site's `latitude`/`longitude` is the origin. Each building has its own coordinate system, placed in the site's:
`x` to the east, `y` to the north, `z` up, in mm, rotated by `azimuth`. Each roof surface has its own coordinate
system: its origin is the left end of the eave, seen from outside with the eave at the bottom; `x` runs along the eave
to the right, `y` up the slope. The roof's `x`, `y`, `z` give that origin in the building's coordinates, and with
`azimuth` and `inclination` they place the surface in space. `azimuth` is the direction the surface faces, which is
opposite to the horizontal direction of its `y` axis; this also defines the axes of a flat roof.

All positions are optional. A project without a layout has buildings and roofs with only their orientation, and
module groups with only a count.

```json
"buildings": [
    {
        "id": "uuid",
        "label": "Wohnhaus",
        "x": 0, "y": 0, "z": 0, "azimuth": 0,
        "roofs": [
            {
                "id": "uuid",
                "label": "Süddach",
                "kind": "pitched",
                "covering": "tiles",
                "x": 1200, "y": 0, "z": 7540,
                "azimuth": 185,
                "inclination": 32,
                "eaveHeight": 7540,
                "ridgeHeight": 11400,
                "margins": { "eave": 200, "ridge": 200, "left": 300, "right": 300 },
                "outline": [[0, 0], [12000, 0], [12000, 6500], [0, 6500]],
                "obstacles": [
                    { "id": "uuid", "kind": "chimney", "shape": "rect", "x": 4000, "y": 3000, "width": 600, "height": 600 },
                    { "id": "uuid", "kind": "vent", "shape": "circle", "x": 8200, "y": 4100, "radius": 90 }
                ],
                "moduleGroups": [
                    {
                        "id": "uuid",
                        "designId": "uuid",
                        "typeId": "uuid",
                        "mounting": "on_roof",
                        "mountingSystemTypeId": "uuid",
                        "orientation": "portrait",
                        "rows": 3,
                        "columns": 8,
                        "count": 24,
                        "x": 500, "y": 400,
                        "gapX": 12, "gapY": 12,
                        "panels": []
                    }
                ]
            }
        ]
    }
]
```

| Field | Values |
|---|---|
| `roof.kind` | `pitched`, `flat`, `facade`, `ground`, `carport` |
| `roof.covering` | `tiles`, `slate`, `metal`, `standing_seam`, `trapezoidal`, `fibre_cement`, `membrane`, `gravel`, `green`, `other` |
| `roof.eaveHeight`, `ridgeHeight` | Height above ground, mm |
| `roof.margins` | Strip along each edge that stays free of modules, mm: `eave`, `ridge`, `left`, `right`. It comes from the mounting system, fire protection rules or the installer's own practice. |
| `obstacle.kind` | `chimney`, `window`, `skylight`, `dormer`, `vent`, `solar_thermal`, `blocked`, `firewall`, `tree`, `other` |
| `obstacle.shape` | `rect` (`x`, `y` = lower left corner, `width`, `height`), `circle` (`x`, `y` = centre, `radius`), `polygon` (`points`) |
| `moduleGroup.mounting` | `on_roof`, `in_roof`, `flat_roof_east_west`, `flat_roof_south`, `facade`, `ground` |
| `moduleGroup.orientation` | `portrait`, `landscape` |
| `moduleGroup.designId` | The design this group belongs to (section 10). Left out when the project has only one layout. |
| `moduleGroup.tilt`, `azimuth` | Tilt and direction of the modules themselves, where they differ from the roof: racked rows on a flat roof, east-west systems. Left out when the modules lie in the roof plane. |
| `moduleGroup.rowPitch` | Distance from one racked row to the next, mm |

A module group is a block of identical modules. `count` is the number of modules in it; `rows` and `columns` may be
missing when the arrangement isn't known. `panels` lists single modules only when they matter, for example to place
them or to record a serial number or a replaced module:

```json
"panels": [
    { "id": "uuid", "row": 0, "column": 3, "stringId": "uuid", "serial": "JA2024…", "from": "2015-03-21", "to": "2026-04-02", "replacedById": "uuid" }
]
```

A module group belongs to the order that installed it through a device of kind `pv_array` (section 8).

A dormer that carries modules is a roof of its own, and at the same time an obstacle of kind `dormer` on the roof it
sits on.

Where a roof came from (swisstopo, a laser measurement, a PV*SOL import) is plugin data in its `ext` (section 12).

### Building model

A building may point to a 3D model file in the project folder, for example a mesh from swisstopo or from a planning
tool. The roofs above stay the reference for the layout; the model is for display and shading.

```json
"model": { "path": "cad/house_geo.stl", "format": "stl", "unit": "mm",
           "origin": { "e": 2647238, "n": 1235998, "elevation": 507 }, "source": "swissBUILDINGS3D 3.0, 2026" }
```

`origin` is the point the model's coordinates count from: LV95 in metres and the height above sea level in metres.

### Surroundings

Things next to the buildings that throw shade: trees, neighbouring buildings, walls, masts. Positions are in the
site's coordinates.

```json
"surroundings": [
    { "id": "uuid", "kind": "tree", "label": "Nussbaum", "x": -6500, "y": 3000, "z": 0, "height": 12000, "radius": 3000 },
    { "id": "uuid", "kind": "building", "label": "Nachbarhaus", "outline": [[9000, -2000], [19000, -2000], [19000, 8000], [9000, 8000]], "z": 0, "height": 9000 }
]
```

`kind` is one of `tree`, `building`, `wall`, `mast`, `terrain`, `other`. A round object has `x`, `y` and `radius`, any
other an `outline`; `height` is measured from `z`.

## 7. Types

A type is a product: a module, an inverter, a battery model, a mounting system. The file holds a copy of every type
it uses, so it stays complete without a database.

```json
"types": [
    {
        "id": "uuid",
        "kind": "panel",
        "manufacturer": "JA Solar",
        "model": "JAM54D40-440/GB",
        "source": { "db": "OpenPanelDatabase", "datasheetSha256": "9f2c…", "url": "https://…" },
        "specs": {
            "power": 440, "voc": 39.1, "isc": 14.0, "vmp": 32.6, "imp": 13.5,
            "efficiency": 22.5, "width": 1134, "height": 1762, "depth": 30, "weight": 21.5,
            "bifacial": true
        }
    },
    {
        "id": "uuid",
        "kind": "mounting_system",
        "manufacturer": "novotegra",
        "model": "Ziegeldach top-fix Klemmsystem",
        "source": { "db": "manual", "url": null },
        "specs": { "moduleGap": 12, "endClampEdge": 13, "maxRailLength": 13000, "frameHeightMin": 30, "frameHeightMax": 52 }
    }
]
```

| Field | Content |
|---|---|
| `kind` | The device kind the type is for (section 8), or `panel`, `mounting_system`, `part` |
| `source.db` | Where the type came from: `OpenPanelDatabase`, `OpenInverterDatabase`, `PVSOL`, `PVsyst`, `manual` |
| `source.id`, `source.version` | The type's identifier in that source, where it has one: the GUID and version in PV*SOL, the file name (`.PAN`, `.OND`) in PVsyst |
| `source.datasheetSha256` | SHA-256 of the datasheet PDF. This identifies the type across database versions; database row numbers are not used. |
| `specs` | The specifications, in the units of section 3. Common values have the names of the table below; any other value keeps the name it has in its source. |

| Kind | Common `specs` fields |
|---|---|
| `panel` | `power` (W at STC), `voc`, `isc`, `vmp`, `imp`, `tempCoeffVoc`, `tempCoeffPower` (%/°C), `efficiency`, `width`, `height`, `depth`, `weight`, `cells`, `bifacial` |
| `inverter` | `powerAc`, `apparentPower`, `phases`, `mpptCount`, `inputsPerMppt`, `maxDcVoltage`, `mpptVoltageMin`, `mpptVoltageMax`, `maxInputCurrent`, `hybrid` |
| `battery` | `capacity`, `powerCharge`, `powerDischarge`, `voltage`, `chemistry` |
| `optimizer` | `powerDc`, `maxInputVoltage`, `maxInputCurrent`, `maxOutputCurrent` |
| `charger` | `powerAc`, `phases`, `canDischarge` |
| `heat_pump` | `powerElectric`, `powerThermal`, `cop` |
| `mounting_system` | `moduleGap`, `endClampEdge`, `maxRailLength`, `frameHeightMin`, `frameHeightMax` |

A type entered by hand has `source.db: "manual"` and only the fields that are known, often only `manufacturer` and
`model`. This is how version 2 projects are migrated: `panelDesc` and `inverterDesc` become manual types.

## 8. Devices

A device is one installed thing: an inverter, a battery, a charger. Devices make up the system's history: a device is
added by an order, and removed or replaced by a later one.

```json
"devices": [
    {
        "id": "uuid",
        "kind": "inverter",
        "typeId": "uuid",
        "label": "WR 1",
        "count": 1,
        "serial": "HV2150123456",
        "firmware": "V100R001C10SPC140",
        "location": "Keller",
        "orderId": "uuid",
        "from": "2015-03-21",
        "to": null,
        "replacesId": null,
        "access": {
            "local": { "host": "192.168.1.40", "port": 502, "protocol": "modbus_tcp", "unitId": 1, "modbusSpec": "inverter/huawei_sun2000" },
            "cloud": { "portal": "huawei.fusionsolar", "linked": true }
        },
        "warranties": [
            { "layer": "legal", "start": "2015-03-21", "end": "2017-03-21" },
            { "layer": "manufacturer", "start": "2015-03-21", "end": "2025-03-21" },
            { "layer": "online_extension", "start": "2025-03-21", "end": "2030-03-21", "condition": "device online" }
        ],
        "ext": {}
    }
]
```

### Kinds

The kinds follow ModbusSpec's device families, plus the parts of a solar system that don't talk Modbus:

| Kind | Device |
|---|---|
| `pv_array` | The modules of an order, as one device: `moduleGroupIds` lists its module groups |
| `inverter` | PV or hybrid inverter |
| `battery` | Battery storage (with its battery inverter if separate) |
| `meter` | Energy meter, smart meter |
| `charger` | Charging station for electric vehicles |
| `heat_pump` | Heat pump |
| `heating_rod` | Heating rod, PV2Heat, Ohmpilot |
| `energy_manager` | Energy manager, controller, data logger |
| `optimizer` | Module optimizers (with `count`) |
| `switchgear` | DC switch, AC distribution, surge protection, fuses |
| `boiler`, `hvac`, `ventilation`, `pool`, `ups`, `io` | As in ModbusSpec |
| `other` | Anything else |

### Fields per kind

| Kind | Fields besides the common ones |
|---|---|
| `pv_array` | `moduleGroupIds` |
| `inverter` | `acCable`: the cable to the distribution board, in the form of a string's `cable` (section 9) |
| `battery` | `coupling`: `ac` (own battery inverter), `dc_generator` (between modules and inverter) or `dc_link` (on the hybrid inverter's battery input). `connectedToId`: the inverter it works with. `backup`: `none`, `socket` (emergency power socket) or `full` (the house keeps running). |
| `optimizer` | `count` and `moduleGroupIds`: the module groups whose modules carry one |
| `charger` | `connectedToId`: the device that controls it on solar surplus. `loadManagement`: true or false. |
| `heat_pump`, `heating_rod` | `connectedToId`: the device that switches it on solar surplus |
| `meter` | `role`: `production`, `consumption` or `grid`. These are the system's own meters; the grid operator's are in `site.meters`. |

### Lifetime

| Field | Content |
|---|---|
| `orderId` | The order that installed the device |
| `from` | Date the device went into operation |
| `to` | Date it was removed, `null` while it is installed |
| `replacesId` | The device this one replaces, for example a replacement inverter after a repair |

The **installed system** on a date is every device with `from` on or before that date and `to` empty or after it. A
device without `from` belongs to an order that isn't finished yet.

### Access

`access.local` describes how to reach the device on the local network:

| Field | Content |
|---|---|
| `host` | IP address or host name |
| `port` | TCP port |
| `protocol` | `modbus_tcp`, `modbus_rtu_gateway`, `sunspec`, `http`, `https`, `aurora`, `other` |
| `unitId` | Modbus unit ID or RS485 address |
| `modbusSpec` | The ModbusSpec device file, as `family/file` without extension |

`access.cloud` names the manufacturer portal and whether the device is linked. Portal-specific data, such as plant
IDs, belongs to the portal's plugin (section 12). Login data never goes into the file.

### Warranties

| `layer` | Meaning |
|---|---|
| `legal` | Statutory warranty of the installer |
| `manufacturer` | The manufacturer's standard warranty |
| `online_extension` | Extension the manufacturer grants while the device is registered or online |
| `purchased_extension` | Extension bought separately |
| `performance` | Performance guarantee, for example for modules |

`condition` describes in words what the layer requires. Documents (section 11) can hold the warranty certificate.

## 9. Strings

How modules are wired to inverters. Optional; most migrated projects have none.

```json
"strings": [
    { "id": "uuid", "inverterId": "uuid", "mppt": 1, "input": 1, "moduleGroupId": "uuid", "modulesInSeries": 12, "parallel": 1, "label": "S1",
      "cable": { "crossSection": 6, "length": 25000, "material": "copper" } }
]
```

A string draws its modules from one module group. `mppt` and `input` count from 1. A string that spans module groups
is split into one entry per group with the same `label`.

Which modules of the group belong to the string is given per module, with `stringId` in the group's `panels`
(section 6), where the strings don't simply follow the rows. `cable` is the DC cable from the string to the inverter:
cross-section in mm², one-way length in mm, `material` `copper` or `aluminium`.

## 10. Designs and quotes

### Designs

A design is one variant of what could be built: on-roof with 24 modules, in-roof, with or without a battery.
Simulation tools keep one file per variant. Here a design is a named entry that module groups and quotes point to.

```json
"designs": [
    {
        "id": "uuid",
        "label": "Aufdach 24 Module",
        "description": "",
        "expectedYield": { "annual": 10200000, "source": "PVGIS 5.3", "date": "2026-11-05" },
        "documents": [
            { "path": "cad/haus_24M.pvprj", "kind": "simulation" },
            { "path": "off/24M.png", "kind": "layout" }
        ]
    }
]
```

| Field | Content |
|---|---|
| `expectedYield` | Expected energy per year in Wh, with the tool and the date it was calculated |
| `documents` | The files of this variant: the simulation project, the layout drawing |

- A module group with a `designId` belongs to that design. A project with a single layout needs no designs, and its
  module groups have no `designId`.
- A quote names the design it offers in its `designId`.
- The file doesn't mark a design as built. The built module groups are the ones listed in the `pv_array` device of an
  order (section 8). Module groups of designs that were not built can stay as a record or be removed.
- Devices and strings exist only for orders. A design that is only quoted lists its devices as quote items.

### Quotes

A quote is a document sent to the client. Once sent it doesn't change; a new version is a new quote.

```json
"quotes": [
    {
        "id": "uuid",
        "number": "O2026-11-0042",
        "date": "2026-11-05",
        "variant": "Aufdach mit Batterie",
        "designId": "uuid",
        "validUntil": "2026-12-31",
        "state": "sent",
        "items": [
            { "id": "uuid", "kind": "device", "typeId": "uuid", "deviceKind": "panel", "count": 24, "unit": "piece", "text": "Solarmodul JA Solar 440 W", "unitPrice": 180.00 },
            { "id": "uuid", "kind": "service", "text": "Montage", "count": 1, "unitPrice": 3500.00 }
        ],
        "total": 18450.00,
        "currency": "CHF",
        "documents": [ { "path": "off/O2026-11-0042.pdf", "kind": "quote" } ]
    }
]
```

| Field | Values |
|---|---|
| `state` | `draft`, `sent`, `accepted`, `rejected`, `expired` |
| `items[].kind` | `device`, `material`, `service`, `discount`, `text` |
| `items[].unit` | `piece`, `m`, `m2`, `h`, `lump_sum`. The order of the items is their position number. |
| `variant` | Free text shown on the quote. `designId` points to the layout that goes with it. |

A migrated quote may have only a `date` (from version 2 `quoteNSent`) and no number, items or total.

## 11. Orders

An order is a job at the site: the first installation, a battery, a replacement. It has its own process steps,
documents and invoices.

```json
"orders": [
    {
        "id": "uuid",
        "type": "new_system",
        "title": "PV-Anlage 10.6 kWp",
        "state": "running",
        "quoteId": "uuid",
        "folder": "",
        "inquiry": "2026-03-01",
        "roofMeasure": null,
        "roofMeasured": "2026-03-10",
        "ordered": "2026-04-15",
        "rejected": null,
        "constructionStart": "2026-06-02",
        "constructionSort": "2026-06-02",
        "constructionFixed": false,
        "commissioned": "2026-06-20",
        "completed": null,
        "archived": null,
        "inactive": null,
        "constructionType": "on_roof",
        "totalCost": 18450.00,
        "items": [],
        "steps": [
            {
                "id": "uuid",
                "kind": "tag",
                "state": "approved",
                "dates": { "submitted": "2026-04-21", "approved": "2026-05-10" },
                "documents": [
                    { "path": "evu/2026-04-20_tag_fill.xlsx", "kind": "filled" },
                    { "path": "evu/2026-05-10_tag_bew.pdf", "kind": "approved" }
                ]
            }
        ],
        "invoices": [
            { "id": "uuid", "number": "R2026-06-0123", "kind": "partial", "date": "2026-06-01", "amount": 9000.00, "currency": "CHF", "paid": "2026-06-20", "documents": [ { "path": "fin/R2026-06-0123.pdf", "kind": "invoice" } ] }
        ],
        "notes": "",
        "ext": {}
    }
]
```

| Field | Content |
|---|---|
| `state` | `inquiry`, `quoted`, `running`, `in_operation`, `completed`, `rejected`, `inactive`. GnuSolar derives it from the dates; it is stored for other readers. |
| `folder` | The order's subfolder in the project folder, relative to it (for example `2026_Bat`). An empty string is the project folder itself, which is the case for the first installation. |
| `roofMeasure`, `roofMeasured` | Roof measurement planned, done |
| `constructionSort` | Date used only to sort the construction planning, defaults to `ordered` |
| `constructionFixed` | The construction date can not be moved |
| `commissioned` | First day of operation (Inbetriebnahme) |
| `completed` | Everything done, including subsidy payment and final invoice |
| `constructionType` | `on_roof`, `in_roof`, `facade`, `flat_roof`, `ground` |
| `totalCost` | Total cost of the order, CHF, as needed for subsidy and solar forms |

### Types of order

| `type` | Job |
|---|---|
| `new_system` | New solar system |
| `extension` | More modules on an existing system |
| `battery` | Battery added or replaced |
| `charger` | Charging station |
| `heat_pump` | Heat pump, PV2Heat, heating rod |
| `replacement` | Replacement of a device (inverter, modules, battery) |
| `repair` | Repair, damage, insurance case |
| `inspection` | Inspection, safety certificate (SiNa), measurement |
| `service` | Other work |

`items` holds the order's positions in the format of quote items. When the client accepts a quote, its items are
copied here; the quote itself stays as it was sent. Changes after the order go into `items`, never into the quote.

### Steps

A step is something done with an authority, the grid operator, a subsidy office or a supplier, usually with a form.

| `kind` | Step |
|---|---|
| `tag` | Technical connection request to the grid operator (TAG) |
| `ia` | Installation notice (Installationsanzeige) |
| `building_permit` | Solar notice or building permit |
| `esti` | ESTI approval |
| `pronovo` | Registration with Pronovo for the one-time remuneration (EIV) |
| `sina_dc`, `sina_ac` | Safety certificate (Sicherheitsnachweis), DC and AC side |
| `measurement` | Measurement and test protocol |
| `documentation` | System documentation created and handed over |
| `material` | Material ordered and delivered |
| `acceptance` | Acceptance by the client |

`state` goes through `ordered` → `filled` → `signed` → `submitted` → `approved` → `paid`, or ends in `rejected`; a step
uses only the states that apply to it. A step not yet started has state `open`; one that doesn't apply to this order
is left out. `dates` holds the date each state was reached. `documents` lists files in the order's folder:

```json
{ "path": "evu/2026-05-10_tag_bew.pdf", "kind": "approved", "date": "2026-05-10" }
```

### Invoices

| `kind` | Invoice |
|---|---|
| `partial` | Down payment (Akonto) |
| `final` | Final invoice |
| `small` | Small invoice without down payments |
| `credit` | Credit note |

`paid` is the date the payment arrived. Payments of a subsidy, such as Pronovo's, are not invoices; they are the
`paid` state of the `pronovo` step.

## 12. Plugins and extensions

Plugins connect GnuSolar to outside services: manufacturer portals, grid-operator portals, subsidy offices,
suppliers, data sources. Each plugin stores its data in the `ext` field of the object it belongs to, under its own ID.

```json
"ext": {
    "huawei.fusionsolar": { "v": 1, "plantId": "NE=33…", "deviceDn": "NE=34…" },
    "swisstopo.buildings3d": { "v": 1, "edition": 2026, "egid": 263008948, "uuid": "{DDE3…}" },
    "valentin.pvsol": { "v": 1, "file": "cad/haus_24M.pvprj", "sha256": "…", "guid": "{2F8701B0-…}" }
}
```

Every object may have an `ext` field: the project, `site`, contacts, buildings, roofs, obstacles, module groups,
types, devices, strings, quotes, orders, steps and invoices.

### Rules

1. A plugin ID is lower case, with dots for namespaces: `manufacturer.product` or the name of the service
   (`huawei.fusionsolar`, `sma.sunnyportal`, `elektroform`, `pronovo`, `swisstopo.buildings3d`).
2. A plugin writes only inside its own namespace. It changes other fields only through the program.
3. Every namespace has a version `v`, an integer. A plugin migrates its own data.
4. The content is plain JSON, in the conventions of this document. Each plugin documents its fields.
5. A program that doesn't know a plugin keeps its data unchanged, also when it saves the file.
6. No secrets in a namespace. A plugin that needs credentials stores them in the operating system's keyring and keeps
   at most a reference: `"credentialRef": "huawei.fusionsolar:installer"`.

### Plugin list

The project's `plugins` lists every plugin that wrote data to the file, so a reader without the plugin knows what the
data is:

```json
"plugins": [
    { "id": "huawei.fusionsolar", "version": "1.2", "name": "Huawei FusionSolar", "url": "https://…" }
]
```

## 13. Implementation notes

`model/ModelNode.py` turns the model into plain data and back. Version 3 needs two changes there:

- **Keep unknown fields.** `fromDict()` currently skips keys the class doesn't have, so the next save drops them. For
  version 3 it keeps them in a runtime attribute (for example `_unknown`), and `toDict()` writes them back.
- **Lists of parts.** Version 3 has lists of objects (contacts, orders, devices …). Their class comes from the field,
  not from the file, as for the dicts of parts today.

## 14. Migration from version 2

GnuSolar converts a version 2 project in `formats/pvp.py: _migrate()`, on the plain data. `tools/migrate_pvp.py`
converts all projects at once, with a dry run that lists lost values and a backup of all files.

Version 2 has one building, one plant and one progress per file. In version 3 they become the site, one building with
one roof, and one order of type `new_system`.

### Field mapping

| Version 2 | Version 3 |
|---|---|
| `building.street`, `streetNumber`, `zip`, `city`, `region`, `country` | `site.address` |
| `building.plotNumber` | `site.plotNumber` |
| `building.buildingId` | `site.buildingIds` (one entry) |
| `building.swissGridX`, `swissGridY` | `site.swissGrid.e`, `.n`; LV03 values (6 digits) get +2 000 000 / +1 000 000 |
| `building.municipalityCode`, `municipalityName` | `site.municipality.code`, `.name` |
| `building.areZoneCode`, `areZoneName` | `site.zone.code`, `.name` |
| `building.mainFuseSize` | `site.mainFuse` (number, A) |
| `building.meterNumberOld`, `meterNumberNew` | `site.meters`: the old one with `to` = order `commissioned`, the new one with `from` = it |
| `building.buildingState` | `ext.gnusolar.v2.buildingState` (kept, no v3 meaning yet) |
| `municipality.id`, `code`, `name`, `countryCode`, `stateCode`, `districtCode`, `website`, `mainContact`, `buildingContact` | `site.municipality` snapshot with the same names, `taken` = file date |
| `municipality.fkFormBuilding` | `site.municipality.buildingFormId` |
| `municipality.fkPowerCompany` | dropped: the grid operator is in `site.gridOperator` |
| `powerCompany.id`, `vseId`, `name`, `mainContact`, `tagContact` | `site.gridOperator` snapshot with the same names, `taken` = file date |
| `powerCompany.address1`, `address2`, `zipCode`, `city` | `site.gridOperator.address` (`zipCode` as text) |
| `powerCompany.fkFormTag`, `fkFormIa`, `fkContactTag` | `site.gridOperator.tagFormId`, `iaFormId`, `tagContactId` |
| `contacts.contacts.owner` | a contact with `roles: ["owner"]`, if it has any value besides `role` |
| `contacts.contacts.installer_ac` | a contact with `roles: ["electrician"]`, if it has any value besides `role` |
| contact `company` | `organization` |
| contact `street` … `country`, `address1`, `address2`, `floor`, `room` | `address` |
| contact `phone`, `phone2`, `mobile`, `email`, `email2` | `channels`, in this order |
| contact `account*` | one entry in `bankAccounts` |
| `plant.panelDesc`, `totalPanelCount`, `totalPowerDc` | a manual panel type (`model` = `panelDesc`, `power` = `totalPowerDc` / count), one roof with one module group (`count`), a `pv_array` device |
| `plant.totalArea` | the module group's `ext.gnusolar.v2.totalArea` (m²) until the roof has a real outline |
| `plant.inverterDesc`, `totalPowerAc` | a manual inverter type and an `inverter` device |
| `plant.constructionType` | order `constructionType`: `builton` → `on_roof`, `integrated` → `in_roof`, `facade` → `facade` |
| `plant.totalCost` | order `totalCost` |
| `progress.inquiryReceived`, `roofMeasure`, `roofMeasured`, `orderReceived`, `orderRejected`, `constructionStart`, `constructionSort`, `constructionFixed`, `launch`, `archived`, `inactiv` | order `inquiry`, `roofMeasure`, `roofMeasured`, `ordered`, `rejected`, `constructionStart`, `constructionSort`, `constructionFixed`, `commissioned`, `archived`, `inactive` |
| `progress.quote1Sent`, `quote2Sent`, `quote3Sent`, `quote4Sent` | one quote each, with `date` and `state: "sent"`; numbers from `off/O<date>-*.pdf` where one matches |
| `progress.tagSent`, `tagReceived` | step `tag`: `submitted`, `approved` |
| `progress.iaSent`, `iaReceived` | step `ia`: `submitted`, `approved` |
| `progress.bauSent`, `bauReceived` | step `building_permit`: `submitted`, `approved` |
| `progress.materialOrdered`, `materialReceived` | step `material`: `ordered`, `approved` (delivered) |
| `progress.documentationCreated`, `documentationPlaced` | step `documentation`: `filled`, `submitted` |
| `progress.siNaDcOrdered`, `siNaDcReceived` | step `sina_dc`: `ordered`, `approved` |
| `progress.siNaAcOrdered`, `siNaAcReceived` | step `sina_ac`: `ordered`, `approved` |
| `progress.eivComplete`, `eivPayed` | step `pronovo`: `submitted`, `paid` |
| `progress.partialInvoiceSent`, `partialInvoiceReceived` | invoice of kind `partial`, `date` and `paid` |
| `progress.partialInvoice2Sent`, `partialInvoice2Received` | a second invoice of kind `partial` |
| `progress.finalInvoiceSent`, `finalInvoiceReceived` | invoice of kind `final`; invoice numbers from `fin/R<date>-*.pdf` where one matches |
| `state` (`Running`, …) | dropped: the order `state` is derived from the dates |
| `comment` | project `notes` |

### Cleaning values

Version 2 values are text as typed. The migration converts them:

- **Numbers:** `"12,34"` and `"12.34"` become `12.34`; units are converted (`totalPowerDc` kWp × 1000 → W,
  `totalPowerAc` kW × 1000 → W). Leading and trailing white space is removed.
- **Empty strings** of numbers, dates and optional fields become `null`.
- **Dates** that are not ISO dates:
  - a year only (`"2021"`): the date `null`, the text kept in the step's or order's `notes`
  - two dates (`"2022-09-27/2023-06-28"`): the first date in the field, the whole text in `notes`; such a project
    most likely had two orders and needs a manual look (the dry run lists them)
  - other text (`"other"`): `null`, the text in `notes`
- **IDs:** every object gets a new UUID.

Nothing of a version 2 file is lost: a value that has no place in version 3 goes to `ext.gnusolar.v2` of the object
it belonged to. The dry run of `tools/migrate_pvp.py` lists every such value.

### Folder copies

Project folders that are copies of another project at the same address (`Heid 2.3_2`) are merged by a separate tool,
not by the file migration: their order becomes an order of the main project with `folder` pointing to the copy.

## 15. Reading other formats

GnuSolar can take over data from planning tools and from public data. This section records how their data maps, as
found in the example projects of PV*SOL premium 2026 (file versions 4 to 24) and PVsyst 8.1, and in swissBUILDINGS3D
3.0. None of them holds customers, orders or history. An import fills the site, buildings and roofs, one design,
types, and strings where the source has them.

| GnuSolar | PV*SOL (`.pvprj`: zip with XML and JSON) | PVsyst (`.PRJ` plus one `.VC*` per variant: text) | swissBUILDINGS3D |
|---|---|---|---|
| `site` | `ProjektdatenV1`; `Standort` in `Visu3D/ProjDaten.xml` | `pvSite` in the `.PRJ` | – |
| `buildings`, `roofs` | `VarHaus` and its roof surfaces in `Visu3D/GeometrischeDaten.xml`; `MeshObj` for imported models | `pvShdBuilding`, made of parametric shapes | roof surfaces per building (EGID), as triangles to be grouped into planes |
| `obstacles` | `BezugsFlaechenObjekt` (windows, chimneys, blocked areas), `Gaube` | – | – |
| `roof.margins` | edge distances (`RandAbst_HuellFL`) | frame of a table (`Cadre`) | – |
| `surroundings` | `Baum`, `Mauer`, other `VarHaus` | `pvShdElemObject` (trees, boxes, cylinders) | neighbouring buildings |
| `site.horizon` | `HorizontLinie` | `pvHorizon` | – |
| `designs` | one project file per variant | one variant file | – |
| `moduleGroups` | `Modulfelder` in `Project.xml`; `ModulFormation` (rows × columns with every module) and `ModulreihenFormation` (racked rows) in the 3D files | `pvShdArrayTable` (3D) and `pvMLTable` (module layout) | – |
| `types` | `DB.json`, in old files `DB.xml`: full copy with GUID and version | only the file name of the `.PAN`, `.OND` or `.BTR` | – |
| `strings` | `WRObj` with its MPP list in `Project.xml`; `Visu3D/Modul_Verschaltung.xml` | `pvSubArray` (modules in series, number of strings); string per module in `pvMLTable` | – |
| `cable` | `AllCables`, in old files `Kabel`; `Visu3D/Kabel.xml` | `WiringResistance`, AC wire fields | – |
| battery device | `Batteriesystem`: coupling, connected inverter | battery file and count in `pvSystem`; `pvGridStorage` | – |
| charger, heat pump | `ElektroAuto`, `ThermalSystem` | – | – |
| quote or order `items` | `Stueckliste` (bill of materials) | – | – |
| `expectedYield` | `SimResults.xml` | results in the variant file | – |

Conventions that differ from this format:

| | Azimuth | Angles | Lengths | Position |
|---|---|---|---|---|
| PV*SOL | 0 = north, clockwise | degrees in `Project.xml`, radians in the 3D files | metres | latitude and longitude in radians, longitude with inverted sign |
| PVsyst | 0 = south, west positive: add 180° | degrees | metres | degrees |
| swissBUILDINGS3D | from the geometry | – | metres | LV95, heights LN02 |

Rules for an import:

- The source file stays in the project folder as a document of the design. The imported objects record where they
  came from in their `ext` (`valentin.pvsol`, `pvsyst`, `swisstopo.buildings3d`): file, checksum and the object's ID
  in the source. A later import of a changed file then updates the same objects.
- Not imported: weather data, loss settings, tariffs, charge schedules, consumption and hot water profiles, and
  results other than the yield.
- PV*SOL and PVsyst both ship a component database that is not open; PVsyst's is encrypted. Types come from the copy
  inside the PV*SOL project, or from PVsyst only as a name, and are then matched by manufacturer and model to
  OpenPanelDatabase and OpenInverterDatabase.
- Old PV*SOL premium files (versions 4 to 6) keep module areas and inverters only in the 3D files; current ones also
  list them in `Project.xml`.

## 16. Example

A house with a solar system from 2015 and a battery added in 2026, written as GnuSolar writes it (keys sorted).

```json
{
    "format": "gnusolar-project",
    "project": {
        "buildings": [
            {
                "id": "0a1b2c3d-0000-4000-8000-000000000010",
                "label": "Wohnhaus",
                "roofs": [
                    {
                        "azimuth": 180,
                        "id": "0a1b2c3d-0000-4000-8000-000000000011",
                        "inclination": 30,
                        "kind": "pitched",
                        "label": "Süddach",
                        "moduleGroups": [
                            {
                                "count": 24,
                                "id": "0a1b2c3d-0000-4000-8000-000000000012",
                                "mounting": "on_roof",
                                "typeId": "0a1b2c3d-0000-4000-8000-000000000020"
                            }
                        ]
                    }
                ]
            }
        ],
        "contacts": [
            {
                "channels": [
                    {
                        "kind": "email",
                        "value": "hans@example.ch"
                    }
                ],
                "firstName": "Hans",
                "id": "0a1b2c3d-0000-4000-8000-000000000001",
                "lastName": "Muster",
                "roles": [
                    "owner",
                    "client",
                    "billing"
                ]
            }
        ],
        "created": "2015-01-10T09:00:00+01:00",
        "designs": [
            {
                "documents": [
                    {
                        "kind": "simulation",
                        "path": "2026_Bat/batterie.pvprj"
                    }
                ],
                "expectedYield": null,
                "id": "0a1b2c3d-0000-4000-8000-000000000080",
                "label": "Batterie 10 kWh"
            }
        ],
        "devices": [
            {
                "from": "2015-03-21",
                "id": "0a1b2c3d-0000-4000-8000-000000000030",
                "kind": "pv_array",
                "moduleGroupIds": [
                    "0a1b2c3d-0000-4000-8000-000000000012"
                ],
                "orderId": "0a1b2c3d-0000-4000-8000-000000000050"
            },
            {
                "from": "2015-03-21",
                "id": "0a1b2c3d-0000-4000-8000-000000000031",
                "kind": "inverter",
                "orderId": "0a1b2c3d-0000-4000-8000-000000000050",
                "to": "2026-06-20",
                "typeId": "0a1b2c3d-0000-4000-8000-000000000021"
            },
            {
                "from": "2026-06-20",
                "id": "0a1b2c3d-0000-4000-8000-000000000032",
                "kind": "inverter",
                "label": "Hybrid-WR",
                "orderId": "0a1b2c3d-0000-4000-8000-000000000051",
                "replacesId": "0a1b2c3d-0000-4000-8000-000000000031",
                "typeId": null
            },
            {
                "access": {
                    "local": {
                        "host": "192.168.1.41",
                        "port": 502,
                        "protocol": "modbus_tcp",
                        "unitId": 1
                    }
                },
                "backup": "none",
                "connectedToId": "0a1b2c3d-0000-4000-8000-000000000032",
                "coupling": "dc_link",
                "from": "2026-06-20",
                "id": "0a1b2c3d-0000-4000-8000-000000000033",
                "kind": "battery",
                "orderId": "0a1b2c3d-0000-4000-8000-000000000051",
                "typeId": "0a1b2c3d-0000-4000-8000-000000000022"
            }
        ],
        "ext": {},
        "generator": "GnuSolar git...c96ce2c",
        "id": "3f0c2a9e-6a1b-4c8e-9d3f-1b2a3c4d5e6f",
        "modified": "2026-11-10T14:00:00+01:00",
        "notes": "",
        "orders": [
            {
                "commissioned": "2015-03-21",
                "completed": "2016-08-24",
                "constructionType": "on_roof",
                "folder": "",
                "id": "0a1b2c3d-0000-4000-8000-000000000050",
                "ordered": "2014-11-12",
                "state": "completed",
                "steps": [
                    {
                        "dates": {
                            "paid": "2016-08-24",
                            "submitted": "2015-12-02"
                        },
                        "id": "0a1b2c3d-0000-4000-8000-000000000060",
                        "kind": "pronovo",
                        "state": "paid"
                    }
                ],
                "title": "PV-Anlage 6.2 kWp",
                "type": "new_system"
            },
            {
                "commissioned": "2026-06-20",
                "folder": "2026_Bat",
                "id": "0a1b2c3d-0000-4000-8000-000000000051",
                "invoices": [
                    {
                        "amount": 12800.0,
                        "currency": "CHF",
                        "date": "2026-06-25",
                        "id": "0a1b2c3d-0000-4000-8000-000000000070",
                        "kind": "final",
                        "number": "R2026-06-0123"
                    }
                ],
                "ordered": "2026-03-01",
                "quoteId": "0a1b2c3d-0000-4000-8000-000000000040",
                "state": "in_operation",
                "steps": [
                    {
                        "dates": {
                            "approved": "2026-03-20",
                            "submitted": "2026-03-05"
                        },
                        "documents": [
                            {
                                "kind": "signed",
                                "path": "2026_Bat/evu/2026-03-05_tag_us.pdf"
                            }
                        ],
                        "id": "0a1b2c3d-0000-4000-8000-000000000061",
                        "kind": "tag",
                        "state": "approved"
                    }
                ],
                "title": "Batterie 10 kWh",
                "type": "battery"
            }
        ],
        "plugins": [],
        "quotes": [
            {
                "currency": "CHF",
                "date": "2026-02-10",
                "designId": "0a1b2c3d-0000-4000-8000-000000000080",
                "documents": [
                    {
                        "kind": "quote",
                        "path": "2026_Bat/O2026-02-0011.pdf"
                    }
                ],
                "id": "0a1b2c3d-0000-4000-8000-000000000040",
                "number": "O2026-02-0011",
                "state": "accepted",
                "total": 12800.0
            }
        ],
        "site": {
            "address": {
                "city": "Zeiningen",
                "country": "CH",
                "street": "Kirchweg",
                "streetNumber": "26",
                "zip": "4314"
            },
            "gridOperator": {
                "id": 402,
                "name": "Elektra Zeiningen",
                "tagFormId": 4,
                "taken": "2026-11-10"
            },
            "mainFuse": 40,
            "municipality": {
                "code": "4264",
                "name": "Zeiningen",
                "taken": "2026-11-10"
            },
            "plotNumber": "1060"
        },
        "strings": [],
        "surroundings": [],
        "types": [
            {
                "id": "0a1b2c3d-0000-4000-8000-000000000020",
                "kind": "panel",
                "manufacturer": "JA Solar",
                "model": "JAP6-60-260/3BB",
                "source": {
                    "db": "manual"
                },
                "specs": {
                    "power": 260
                }
            },
            {
                "id": "0a1b2c3d-0000-4000-8000-000000000021",
                "kind": "inverter",
                "manufacturer": "Fronius",
                "model": "Symo 6.0-3-M",
                "source": {
                    "db": "manual"
                },
                "specs": {
                    "phases": 3,
                    "powerAc": 6000
                }
            },
            {
                "id": "0a1b2c3d-0000-4000-8000-000000000022",
                "kind": "battery",
                "manufacturer": "BYD",
                "model": "Battery-Box Premium HVS 10.2",
                "source": {
                    "db": "manual"
                },
                "specs": {
                    "capacity": 10240
                }
            }
        ]
    },
    "version": 3
}
```

## 17. Open points

- **Designs before an order:** devices and strings exist only for orders, so a quoted design has its wiring only in
  the simulation file. If string plans are needed at the quote stage, designs get their own planned devices.
- **Curved and irregular roofs** (barrel roofs, roofs that are not one plane) have no form here; they would be
  approximated by several roofs.
- **Pricing of items:** whether quotes and orders carry full positions with prices, or only the devices and a total,
  until GnuSolar calculates quotes itself.
- **Owner export:** which parts of the file an owner gets (likely everything except prices, notes and installer-only
  plugin data), and in which form.
- **Schema:** a JSON Schema for validation, kept next to this document.
- **`building.buildingState`** (new or existing building) has no field in version 3 yet; it is kept under
  `ext.gnusolar.v2` until it gets one.
