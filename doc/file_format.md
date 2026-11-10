# GnuSolar project file, version 3

Draft. Version 2 is the current format (see `formats/pvp.py`); this document describes version 3, the next one.

A project file describes one solar project: the site, the people involved, the buildings and roofs, the devices
installed over time, and the quotes and orders that brought them there. GnuSolar reads and writes it, and any other
program can too: the format is plain JSON and documented here.

Version 2 stores the existing model (one building, one plant, one progress) as plain JSON. Version 3 changes the
model: one project holds several orders, devices with their history, roofs, quotes and plugin data. GnuSolar converts
version 2 files when it opens them (section 15).

## 1. Principles

- **One project, one file.** A project is one site, usually one building or a group of buildings at one address.
  Every order at that site, the first installation as well as a battery ten years later, lives in the same file.
- **Readable without GnuSolar.** Plain JSON, English keys, documented units. No class names, no pickled objects.
- **Complete on its own.** The file holds copies of the device types it uses and a snapshot of the master data it
  relied on (grid operator, municipality), so it can be read without a database.
- **History, not only the current state.** Devices have a start and an end date. Replaced devices stay in the file.
- **No secrets.** Passwords, tokens and access codes never go into a project file.
- **Country independent.** The fields of this document mean the same in every country. National coordinate systems,
  register numbers, classifications and the steps with a country's authorities belong to a country extension
  (section 13).
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
| `project` | The project, sections 4 to 13 |

A reader that finds a higher `version` than it knows refuses the file instead of guessing, so an older GnuSolar never
damages a newer file. A reader that finds a lower `version` migrates it, one version step at a time, on the plain
data (`formats/pvp.py: _migrate()`).

### The project object

```json
"project": {
    "id": "uuid",
    "created": 1794315600,
    "modified": 1794315600,
    "generator": "GnuSolar git...c96ce2c",
    "currency": "CHF",
    "site": {},
    "contacts": [],
    "buildings": [],
    "surroundings": [],
    "types": [],
    "devices": [],
    "strings": [],
    "connections": [],
    "designs": [],
    "quotes": [],
    "orders": [],
    "notes": "",
    "plugins": [],
    "ext": {}
}
```

`currency` is the currency of every amount in the project (ISO 4217).

## 3. Conventions

### IDs and references

- Every object in a list has an `id`: a UUID (version 4) in lower case, as a string.
- IDs never change and are never reused, also not after an object is removed.
- A reference to another object is a field ending in `Id` (or `Ids` for a list), holding that object's `id`.

UUIDs let two copies of a file, for example synced with Syncthing, be merged object by object.

### Dates and times

Every date and every point in time is a Unix timestamp: the seconds since 1970-01-01 00:00 UTC, as an integer.

- A point in time, such as `created` or `modified`, is that moment: 1794315600 is 10 November 2026, 14:00 in
  Switzerland.
- A calendar day without a time, such as the day a system went into operation, is 12:00 UTC of that day: 1794312000
  is 10 November 2026. Noon keeps the day the same in every time zone, and a reader gets the day back by taking the
  UTC date of the value.
- There are no date strings anywhere in the file. A date that is not known is `null` or left out, never 0.

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
| Date, time | Unix timestamp, seconds, integer | `"from": 1426939200` |
| Percent | % (0–100) | `"efficiency": 21.3` |
| Money | the amount as a number, in the project's `currency`. An amount in another currency carries its own `currency` field. | `"amount": 18450.00` |
| Geographic position | WGS84 latitude and longitude, degrees | `"latitude": 47.5419` |

Numbers are JSON numbers, never strings, and use a decimal point. Field names never carry a unit (`powerAc`, not
`powerAcKw`). Device values use the names of ModbusSpec's `vocabulary.yaml` where one exists.

### Values

- Enumerations are lower-case strings in `snake_case`, for example `"heat_pump"`.
- Text in the file is in the language of its users. Keys and enumeration values are English.

## 4. Site

The place where the system stands.

```json
"site": {
    "label": "Einfamilienhaus Muster",
    "address": { "street": "Kirchweg", "streetNumber": "26", "zip": "4314", "city": "Zeiningen", "region": null, "country": "CH" },
    "latitude": 47.5419,
    "longitude": 7.8696,
    "elevation": 330,
    "plotNumber": "1060",
    "supply": { "phases": 3, "voltage": 400, "frequency": 50, "earthingSystem": "tn_c_s", "mainFuse": 40 },
    "annualConsumption": 4500000,
    "designTemperature": { "minAmbient": -10, "maxCell": 70 },
    "horizon": [[0, 2], [90, 5], [180, 8], [270, 3]],
    "municipality": { "taken": 1794312000, "code": "4264", "name": "Zeiningen", "…": "snapshot, see below" },
    "gridOperator": { "taken": 1794312000, "id": 402, "name": "Elektra Zeiningen", "…": "snapshot, see below" },
    "ext": {
        "ch": { "v": 1, "lv95": { "e": 2632561.2, "n": 1265432.8 }, "egid": [190335642], "zone": { "code": "11", "name": "Wohnzonen" } }
    }
}
```

| Field | Content |
|---|---|
| `latitude`, `longitude` | WGS84, degrees. The position of the site, and the origin of the coordinate system (section 6). |
| `elevation` | Metres above sea level |
| `plotNumber` | Number of the parcel in the land register |
| `ext` | National data of the site, such as coordinates in the national grid, building register numbers and the building zone, in the country extension (section 13) |
| `supply` | The connection to the grid: number of `phases`, nominal `voltage` between the phases in V (for one phase: to neutral), `frequency` in Hz, the `earthingSystem` (section 10) and `mainFuse`, the rating of the house connection fuse in A |
| `annualConsumption` | Electricity the site uses per year, Wh |
| `designTemperature` | For sizing strings: `minAmbient` is the lowest ambient temperature (it gives the highest open-circuit voltage), `maxCell` the highest cell temperature (it gives the lowest MPP voltage), °C |
| `horizon` | The horizon line seen from the site, as `[azimuth, elevation]` pairs in degrees |

### Master data snapshots

`municipality` and `gridOperator` are copies of GnuSolar's master data (`master.db`) as they were when the project
used them, so a connection request from 2019 still shows the grid operator contact of 2019. `taken` is the date of the copy; `id`
refers to the master data row it came from. GnuSolar may refresh a snapshot, and then sets a new `taken`.

```json
"municipality": {
    "taken": 1794312000,
    "id": 4264, "code": "4264", "name": "Zeiningen",
    "countryCode": "CH", "stateCode": "AG", "districtCode": null,
    "website": "https://www.zeiningen.ch",
    "mainContact": { "organization": "Gemeinde Zeiningen", "address": {}, "channels": [] },
    "buildingContact": { "organization": "Bauverwaltung", "address": {}, "channels": [] },
    "ext": { "ch": { "v": 1, "buildingFormId": 7 } }
},
"gridOperator": {
    "taken": 1794312000,
    "id": 402, "name": "Elektra Zeiningen",
    "address": { "street": "Kirchweg", "streetNumber": "26", "zip": "4314", "city": "Zeiningen" },
    "mainContact": { "organization": "Elektra Zeiningen", "address": {}, "channels": [] },
    "connectionContact": { "organization": "IBW Technik AG", "address": {}, "channels": [] },
    "ext": { "ch": { "v": 1, "vseId": null, "tagFormId": 4, "iaFormId": null } }
}
```

The contacts inside a snapshot have the form of section 5 without `id`, `roles`, `from` and `to`. `code` is the
municipality's official number in its country. `connectionContact` is who handles connection requests for the grid
operator. Which forms a municipality or grid operator uses is national and sits in the country extension.

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
            { "owner": "Hans Muster", "bank": "Raiffeisen", "iban": "CH00 0000 0000 0000 0000 0", "bic": null }
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
| `moduleGroup.designId` | The design this group belongs to (section 11). Left out when the project has only one layout. |
| `moduleGroup.tilt`, `azimuth` | Tilt and direction of the modules themselves, where they differ from the roof: racked rows on a flat roof, east-west systems. Left out when the modules lie in the roof plane. |
| `moduleGroup.rowPitch` | Distance from one racked row to the next, mm |

A module group is a block of identical modules. `count` is the number of modules in it; `rows` and `columns` may be
missing when the arrangement isn't known. `panels` lists single modules only when they matter, for example to place
them or to record a serial number or a replaced module:

```json
"panels": [
    { "id": "uuid", "row": 0, "column": 3, "stringId": "uuid", "serial": "JA2024…", "from": 1426939200, "to": 1775131200, "replacedById": "uuid" }
]
```

A module group belongs to the order that installed it through a device of kind `pv_array` (section 8).

A dormer that carries modules is a roof of its own, and at the same time an obstacle of kind `dormer` on the roof it
sits on.

Where a roof came from (a public 3D building dataset, a laser measurement, a PV*SOL import) is plugin data in its `ext` (section 13).

### Building model

A building may point to a 3D model file in the project folder, for example a mesh from a public 3D building dataset or from a
planning tool. The roofs above stay the reference for the layout; the model is for display and shading.

```json
"model": { "path": "cad/house_geo.stl", "format": "stl", "unit": "mm",
           "origin": { "x": -9200, "y": -10600, "z": 0 }, "source": "swissBUILDINGS3D 3.0, 2026" }
```

`origin` is the point the model's coordinates count from, in the building's coordinates.

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
| `panel` | `power` (W at STC), `voc`, `isc`, `vmp`, `imp`, `tempCoeffVoc`, `tempCoeffPower` (%/°C), `efficiency`, `width`, `height`, `depth`, `weight`, `cells`, `bifacial`, `connector` (the DC connector on its leads, as for a port in section 10), `cableLength` |
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
        "from": 1426939200,
        "to": null,
        "replacesId": null,
        "access": {
            "local": { "host": "192.168.1.40", "port": 502, "protocol": "modbus_tcp", "unitId": 1, "modbusSpec": "inverter/huawei_sun2000" },
            "cloud": { "portal": "huawei.fusionsolar", "linked": true }
        },
        "warranties": [
            { "layer": "legal", "start": 1426939200, "end": 1490097600 },
            { "layer": "manufacturer", "start": 1426939200, "end": 1742558400 },
            { "layer": "online_extension", "start": 1742558400, "end": 1900324800, "condition": "device online" }
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
| `meter` | Energy meter: the grid operator's or one of the system's own |
| `charger` | Charging station for electric vehicles |
| `heat_pump` | Heat pump |
| `heating_rod` | Heating rod, PV2Heat, Ohmpilot |
| `energy_manager` | Energy manager, controller, data logger |
| `optimizer` | Module optimizers (with `count`) |
| `grid_connection` | The point where the building is connected to the grid |
| `distribution_board` | Distribution board, meter cabinet, connection box: an enclosure for other devices |
| `fuse` | Fuse with its holder |
| `breaker` | Circuit breaker |
| `rcd` | Residual current device |
| `rcbo` | Residual current device and circuit breaker in one |
| `switch` | Hand-operated switch: isolator, DC isolator, changeover or bypass switch |
| `transfer_switch` | Automatic changeover between grid, backup supply and generator |
| `spd` | Surge protection device |
| `busbar` | Rail or terminal block where conductors of the same kind meet: phases, N, PE |
| `earth_electrode` | Foundation earth or earth rod |
| `load` | A consumer or a group of consumers |
| `generator` | Generator |
| `boiler`, `hvac`, `ventilation`, `pool`, `ups`, `io` | As in ModbusSpec |
| `other` | Anything else |

### Fields per kind

| Kind | Fields besides the common ones |
|---|---|
| `pv_array` | `moduleGroupIds` |
| `inverter` | `backup`: what it supplies when the grid fails: `none`, `socket`, `partial` (the loads on its backup output) or `whole_house`. `backupNeutralBond`: how neutral and earth are joined while it runs without the grid (section 10). |
| `battery` | `coupling`: `ac` (own battery inverter), `dc_generator` (between modules and inverter) or `dc_link` (on the hybrid inverter's battery input). `connectedToId`: the inverter it works with. `backup`, as for an inverter, where the battery unit itself supplies the house in an outage. |
| `optimizer` | `count` and `moduleGroupIds`: the module groups whose modules carry one |
| `charger` | `connectedToId`: the device that controls it on solar surplus. `loadManagement`: true or false. |
| `heat_pump`, `heating_rod` | `connectedToId`: the device that switches it on solar surplus |
| `meter` | `owner`, `number`, `role`, `measuring`, `ct`, `measures` (section 10) |
| `fuse` | `ratedCurrent`, `characteristic` (`gG`, `aM`, `gPV` …), `form`: the form factor (`nh00`, `nh1`, `d01`, `d02`, `dII`, `dIII`, `10x38`, `14x51` …), `poles`, `ratedVoltage`, `breakingCapacity` |
| `breaker` | `ratedCurrent`, `characteristic` (`B`, `C`, `D`, `K`, `Z`), `poles`, `switchesNeutral`, `breakingCapacity`, `form` (`din_rail`, `moulded_case`) |
| `rcd` | `ratedCurrent`, `residualCurrent` (0.03 for 30 mA), `rcdType` (`AC`, `A`, `F`, `B`), `selective`, `poles` |
| `rcbo` | The fields of `breaker` and of `rcd` |
| `switch` | `function`: `isolator`, `dc_isolator`, `changeover`, `bypass`. `ratedCurrent`, `poles`, `switchesNeutral`. |
| `transfer_switch` | `ratedCurrent`, `poles`, `switchesNeutral` |
| `spd` | `spdType` (`1`, `2`, `1+2`, `3`), `side`: `ac` or `dc` |
| `busbar` | `conductors`: what it carries, for example `["N"]`, `["PE"]` or `["L1", "L2", "L3"]` |
| `load` | `power`, and `backup`: true when it stays supplied in an outage |
| `generator` | `powerAc`, `phases` |

The name of a fuse or breaker as written on the board and in the diagram ("F1", "Q3") is the device's `label`.

### Lifetime

| Field | Content |
|---|---|
| `orderId` | The order that installed the device |
| `from` | Date the device went into operation |
| `to` | Date it was removed, `null` while it is installed |
| `replacesId` | The device this one replaces, for example a replacement inverter after a repair |
| `parentId` | The device this one is built into or mounted in: a breaker in a distribution board, the meter built into an inverter |

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
IDs, belongs to the portal's plugin (section 13). Login data never goes into the file.

### Warranties

| `layer` | Meaning |
|---|---|
| `legal` | Statutory warranty of the installer |
| `manufacturer` | The manufacturer's standard warranty |
| `online_extension` | Extension the manufacturer grants while the device is registered or online |
| `purchased_extension` | Extension bought separately |
| `performance` | Performance guarantee, for example for modules |

`condition` describes in words what the layer requires. Documents (section 12) can hold the warranty certificate.

## 9. Strings

How modules are wired to inverters. Optional; most migrated projects have none.

```json
"strings": [
    { "id": "uuid", "inverterId": "uuid", "mppt": 1, "input": 1, "moduleGroupId": "uuid", "modulesInSeries": 12, "parallel": 1, "label": "S1",
      "cable": { "crossSection": 6, "length": 25000, "material": "copper" }, "connector": "MC4" }
]
```

A string draws its modules from one module group. `mppt` and `input` count from 1. A string that spans module groups
is split into one entry per group with the same `label`.

Which modules of the group belong to the string is given per module, with `stringId` in the group's `panels`
(section 6), where the strings don't simply follow the rows. `cable` is the DC cable from the string to the inverter:
cross-section in mm², one-way length in mm, `material` `copper` or `aluminium`. `connector` is the plug fitted to
that cable at the inverter. All other wiring is in `connections`
(section 10).

## 10. Electrical installation

Section 8 lists every electrical component of the building that matters for the system: the grid connection, meters,
distribution boards, fuses, breakers, residual current devices, switches, busbars, loads, and the inverters,
batteries and chargers themselves. `connections` says how they are wired, for power, protective earth and signal.
Devices and connections together are the circuit diagram of the installation.

A project doesn't need this part. Without connections the devices are simply a list.

### Ports

A device is wired at its ports. A port has the name printed on the device or used in its manual: `GRID`, `BACKUP`,
`PV1`, `BAT`, `BMS`, `CT`, `COM1`. A type can list its ports in `specs.ports`:

```json
"ports": [
    { "name": "PV1", "kind": "dc", "connector": "MC4" },
    { "name": "GRID", "kind": "ac", "conductors": ["L1", "L2", "L3", "N", "PE"], "connector": "screw terminal" },
    { "name": "BACKUP", "kind": "ac", "conductors": ["L1", "L2", "L3", "N", "PE"], "connector": "screw terminal" },
    { "name": "BAT", "kind": "dc", "connector": "SUNCLIX" },
    { "name": "BMS", "kind": "signal", "connector": "RJ45" }
]
```

`connector` is the kind of connector the port has, written as its maker writes it: `MC4`, `MC4-Evo2`, `SUNCLIX`,
`H4`, `RJ45`, or `screw terminal`, `spring terminal`, `cable lug` for terminals. It says which plug the cable needs
and lets a program check that both sides fit. Mating DC connectors of different makes is a known cause of faults,
so the exact name matters there.

Simple devices have fixed port names:

| Kind | Ports |
|---|---|
| `fuse`, `breaker`, `rcd`, `rcbo`, `switch` (isolator), a `meter` wired in line | `in` (supply side), `out` (load side) |
| `switch` with `function` `changeover` or `bypass` | `common`, `a`, `b` |
| `busbar` | `bar` |
| `grid_connection` | `out` |
| `load` | `in` |
| `earth_electrode` | `pe` |
| `spd` | `line`, `pe` |

### Connections

A connection is one cable, or one set of wires, between two ports.

```json
"connections": [
    {
        "id": "uuid",
        "kind": "ac",
        "ends": [ { "deviceId": "uuid", "port": "out" }, { "deviceId": "uuid", "port": "GRID" } ],
        "conductors": ["L1", "L2", "L3", "N", "PE"],
        "cable": { "designation": "5G6", "cores": 5, "crossSection": 6, "outerDiameter": 15, "length": 8000, "material": "copper" },
        "label": "W3",
        "orderId": "uuid",
        "from": 1781956800,
        "to": null
    }
]
```

| Field | Content |
|---|---|
| `kind` | `ac`, `dc`, `pe` (protective earth and equipotential bonding), `bond` (a link that joins neutral and earth) or `signal` |
| `ends` | The two ports it joins. Where more than two cables meet, they meet at a device: a busbar, a breaker, a terminal. An end can carry `connector`, the plug fitted to the cable there, when the port doesn't say it or the plug differs from it. |
| `conductors` | What the cable carries: `L1`, `L2`, `L3`, `N`, `PE`, `PEN` for AC, `+` and `-` for DC. A single-phase device names the phase it is on. |
| `cable` | `designation` (the cable type as ordered), `cores`, `crossSection` of one conductor in mm², `outerDiameter` in mm, `length` in mm, `material`: `copper` or `aluminium` |
| `protocol` | For `signal`: `rs485`, `can`, `ethernet`, `ct` (the leads of a current transformer), `digital` (a switching contact: remote shutdown, ripple control receiver, load control), `analog`, `other` |
| `label` | The cable's name in the diagram |
| `orderId`, `from`, `to` | As for devices: the order that installed it and the time it was in place |

The strings of section 9 are the DC connections between modules and inverter. They are not repeated here.

### Neutral and earth

How neutral and protective earth are arranged decides which switches a backup supply needs, so the file records it
in four places:

- **The earthing system** of the supply is `site.supply.earthingSystem`: `tn_s`, `tn_c`, `tn_c_s`, `tt` or `it`, as
  defined in IEC 60364.
- **Busbars and the earth electrode are devices.** The N bar and the PE bar of a board are `busbar` devices, and the
  earth electrode is connected to the PE bar by a `pe` connection. Where neutral and earth are joined, as at the
  point where a PEN conductor is split, there is a connection of kind `bond` between the two bars. A board without
  that connection keeps them apart.
- **Whether a device interrupts the neutral** is its `poles` together with `switchesNeutral`. A three-pole changeover
  switch leaves the neutral connected through; a four-pole one switches it.
- **What the inverter does without the grid** is its `backupNeutralBond`: `relay` when it joins neutral and earth
  itself while it supplies the backup loads, `external` when the installation provides the bond, `none` when there
  is none.

Inverter manuals show the same inverter wired in both ways. Where neutral and earth are joined in the board, the
neutral of the grid side and the backup side stay connected and the switches have three poles. Where they are
separate, switches and residual current devices have four poles, and the inverter bonds neutral to earth while it
runs without the grid.

### Meters

Every meter is a device of kind `meter`, the grid operator's as well as the system's own.

| Field | Content |
|---|---|
| `owner` | `grid_operator` or `system` |
| `number` | The meter number, for the grid operator's meter |
| `role` | What its reading means: `grid` (at the grid connection, both directions), `production`, `consumption`, `sub` (one consumer or a part of the building) |
| `measuring` | `direct`: the current runs through the meter, which is wired with `in` and `out`. `ct`: it measures with current transformers around a cable. |
| `ct` | For `ct`: the transformer ratio as `primary` and `secondary` current in A, for example 120 and 0.04 |
| `measures` | For `ct`: the `connectionId` of the cable the transformers sit on, and `arrowTowardsId`, the device at the end their arrow points to |
| `parentId` | The inverter, for a meter built into it; the board, for one mounted there |

Where a meter sits in the circuit is given by its connections, or by `measures`. That place decides what it sees:

- A `grid` meter sits between the grid connection and the first branch, so the whole building is behind it.
- With partial backup, the loads that are not backed up branch off before the inverter. The transformers of the
  inverter's meter then sit on the cable from the grid, before that branch.
- With whole-house backup everything runs through the inverter, and its built-in meter needs no transformer at the
  grid.
- A second inverter needs its own `production` meter on its AC cable, if the system has to know its output.

### Example

A hybrid inverter with partial backup, with neutral and earth separate in the board. IDs are shortened to names here.

```json
"devices": [
    { "id": "grid", "kind": "grid_connection" },
    { "id": "F0",  "kind": "fuse", "label": "HAK", "ratedCurrent": 40, "characteristic": "gG", "form": "nh00", "poles": 3 },
    { "id": "Z1",  "kind": "meter", "owner": "grid_operator", "number": "12345678", "role": "grid", "measuring": "direct" },
    { "id": "HV",  "kind": "distribution_board", "label": "Hauptverteilung" },
    { "id": "L",   "kind": "busbar", "parentId": "HV", "conductors": ["L1", "L2", "L3", "N"] },
    { "id": "PE",  "kind": "busbar", "parentId": "HV", "conductors": ["PE"] },
    { "id": "E",   "kind": "earth_electrode" },
    { "id": "Q1",  "kind": "breaker", "parentId": "HV", "label": "Q1", "ratedCurrent": 32, "characteristic": "C", "poles": 4, "switchesNeutral": true },
    { "id": "F1",  "kind": "rcd", "parentId": "HV", "label": "F1", "ratedCurrent": 40, "residualCurrent": 0.3, "rcdType": "A", "poles": 4 },
    { "id": "INV", "kind": "inverter", "backup": "partial", "backupNeutralBond": "relay" },
    { "id": "M0",  "kind": "meter", "parentId": "INV", "owner": "system", "role": "grid", "measuring": "ct",
      "ct": { "primary": 120, "secondary": 0.04 }, "measures": { "connectionId": "W2", "arrowTowardsId": "Z1" } },
    { "id": "BAT", "kind": "battery", "coupling": "dc_link", "connectedToId": "INV" },
    { "id": "Q2",  "kind": "rcbo", "parentId": "HV", "label": "Q2", "ratedCurrent": 20, "characteristic": "C", "residualCurrent": 0.03, "rcdType": "A", "poles": 4 },
    { "id": "LB",  "kind": "load", "label": "Notstromverbraucher", "backup": true },
    { "id": "Q3",  "kind": "rcbo", "parentId": "HV", "label": "Q3", "ratedCurrent": 25, "characteristic": "C", "residualCurrent": 0.03, "rcdType": "A", "poles": 4 },
    { "id": "LN",  "kind": "load", "label": "Übrige Verbraucher", "backup": false }
],
"connections": [
    { "id": "W0",  "kind": "ac", "ends": [{ "deviceId": "grid", "port": "out" }, { "deviceId": "F0", "port": "in" }], "conductors": ["L1", "L2", "L3", "N"], "cable": { "crossSection": 16 } },
    { "id": "W1",  "kind": "ac", "ends": [{ "deviceId": "F0", "port": "out" }, { "deviceId": "Z1", "port": "in" }], "conductors": ["L1", "L2", "L3", "N"], "cable": { "crossSection": 16 } },
    { "id": "W2",  "kind": "ac", "ends": [{ "deviceId": "Z1", "port": "out" }, { "deviceId": "L", "port": "bar" }], "conductors": ["L1", "L2", "L3", "N"], "cable": { "crossSection": 16 } },
    { "id": "W3",  "kind": "ac", "ends": [{ "deviceId": "L", "port": "bar" }, { "deviceId": "Q1", "port": "in" }], "conductors": ["L1", "L2", "L3", "N"], "cable": { "crossSection": 6 } },
    { "id": "W4",  "kind": "ac", "ends": [{ "deviceId": "Q1", "port": "out" }, { "deviceId": "F1", "port": "in" }], "conductors": ["L1", "L2", "L3", "N"], "cable": { "crossSection": 6 } },
    { "id": "W5",  "kind": "ac", "ends": [{ "deviceId": "F1", "port": "out" }, { "deviceId": "INV", "port": "GRID" }], "conductors": ["L1", "L2", "L3", "N"], "cable": { "designation": "5G6", "crossSection": 6, "length": 8000 } },
    { "id": "W6",  "kind": "ac", "ends": [{ "deviceId": "INV", "port": "BACKUP" }, { "deviceId": "Q2", "port": "in" }], "conductors": ["L1", "L2", "L3", "N"], "cable": { "designation": "5G6", "crossSection": 6, "length": 8000 } },
    { "id": "W7",  "kind": "ac", "ends": [{ "deviceId": "Q2", "port": "out" }, { "deviceId": "LB", "port": "in" }], "conductors": ["L1", "L2", "L3", "N", "PE"] },
    { "id": "W8",  "kind": "ac", "ends": [{ "deviceId": "L", "port": "bar" }, { "deviceId": "Q3", "port": "in" }], "conductors": ["L1", "L2", "L3", "N"] },
    { "id": "W9",  "kind": "ac", "ends": [{ "deviceId": "Q3", "port": "out" }, { "deviceId": "LN", "port": "in" }], "conductors": ["L1", "L2", "L3", "N", "PE"] },
    { "id": "W10", "kind": "dc", "ends": [{ "deviceId": "INV", "port": "BAT" }, { "deviceId": "BAT", "port": "BAT" }], "conductors": ["+", "-"] },
    { "id": "W11", "kind": "signal", "protocol": "can", "ends": [{ "deviceId": "INV", "port": "BMS" }, { "deviceId": "BAT", "port": "BMS" }] },
    { "id": "W12", "kind": "pe", "ends": [{ "deviceId": "INV", "port": "PE" }, { "deviceId": "PE", "port": "bar" }], "conductors": ["PE"], "cable": { "crossSection": 6 } },
    { "id": "W13", "kind": "pe", "ends": [{ "deviceId": "PE", "port": "bar" }, { "deviceId": "E", "port": "pe" }], "conductors": ["PE"], "cable": { "crossSection": 16 } }
]
```

The built-in meter `M0` has its transformers on `W2`, between the grid operator's meter and the rail where the
other loads branch off, so it sees what the whole building takes from the grid. In a board where neutral and earth
are joined there would be an N bar as well, and one more connection:

```json
{ "id": "W14", "kind": "bond", "ends": [{ "deviceId": "N", "port": "bar" }, { "deviceId": "PE", "port": "bar" }] }
```

## 11. Designs and quotes

### Designs

A design is one variant of what could be built: on-roof with 24 modules, in-roof, with or without a battery.
Simulation tools keep one file per variant. Here a design is a named entry that module groups and quotes point to.

```json
"designs": [
    {
        "id": "uuid",
        "label": "Aufdach 24 Module",
        "description": "",
        "expectedYield": { "annual": 10200000, "source": "PVGIS 5.3", "date": 1793880000 },
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
        "date": 1793880000,
        "variant": "Aufdach mit Batterie",
        "designId": "uuid",
        "validUntil": 1798718400,
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

## 12. Orders

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
        "inquiry": 1772366400,
        "roofMeasure": null,
        "roofMeasured": 1773144000,
        "ordered": 1776254400,
        "rejected": null,
        "constructionStart": 1780401600,
        "constructionSort": 1780401600,
        "constructionFixed": false,
        "commissioned": 1781956800,
        "completed": null,
        "archived": null,
        "inactive": null,
        "constructionType": "on_roof",
        "totalCost": 18450.00,
        "items": [],
        "steps": [
            {
                "id": "uuid",
                "kind": "ch.tag",
                "state": "approved",
                "dates": { "submitted": 1776772800, "approved": 1778414400 },
                "documents": [
                    { "path": "evu/2026-04-20_tag_fill.xlsx", "kind": "filled" },
                    { "path": "evu/2026-05-10_tag_bew.pdf", "kind": "approved" }
                ]
            }
        ],
        "invoices": [
            { "id": "uuid", "number": "R2026-06-0123", "kind": "partial", "date": 1780315200, "amount": 9000.00, "currency": "CHF", "paid": 1781956800, "documents": [ { "path": "fin/R2026-06-0123.pdf", "kind": "invoice" } ] }
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
| `totalCost` | Total cost of the order, as needed for subsidy and permit forms |

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
| `inspection` | Inspection, safety certificate, measurement |
| `service` | Other work |

`items` holds the order's positions in the format of quote items. When the client accepts a quote, its items are
copied here; the quote itself stays as it was sent. Changes after the order go into `items`, never into the quote.

### Steps

A step is something done with an authority, the grid operator, a subsidy office or a supplier, usually with a form.

| `kind` | Step |
|---|---|
| `material` | Material ordered and delivered |
| `measurement` | Measurement and test protocol |
| `documentation` | System documentation created and handed over |
| `acceptance` | Acceptance by the client |
| `<country>.<name>` | A step with an authority, the grid operator or a subsidy office. These differ from country to country, so their kinds are defined by the country extension and carry its prefix, for example `ch.tag` (section 13). |

`state` goes through `ordered` → `filled` → `signed` → `submitted` → `approved` → `paid`, or ends in `rejected`; a step
uses only the states that apply to it. A step not yet started has state `open`; one that doesn't apply to this order
is left out. `dates` holds the date each state was reached. `documents` lists files in the order's folder:

```json
{ "path": "evu/2026-05-10_tag_bew.pdf", "kind": "approved", "date": 1778414400 }
```

### Invoices

| `kind` | Invoice |
|---|---|
| `partial` | Down payment (Akonto) |
| `final` | Final invoice |
| `small` | Small invoice without down payments |
| `credit` | Credit note |

`paid` is the date the payment arrived. Payments of a subsidy are not invoices; they are the `paid` state of the
subsidy's step.

## 13. Plugins and extensions

Plugins connect GnuSolar to outside services: manufacturer portals, grid-operator portals, subsidy offices,
suppliers, data sources. Each plugin stores its data in the `ext` field of the object it belongs to, under its own ID.

```json
"ext": {
    "huawei.fusionsolar": { "v": 1, "plantId": "NE=33…", "deviceDn": "NE=34…" },
    "ch.swisstopo.buildings3d": { "v": 1, "edition": 2026, "egid": 263008948, "uuid": "{DDE3…}" },
    "valentin.pvsol": { "v": 1, "file": "cad/haus_24M.pvprj", "sha256": "…", "guid": "{2F8701B0-…}" }
}
```

Every object may have an `ext` field: the project, `site`, contacts, buildings, roofs, obstacles, module groups,
types, devices, strings, quotes, orders, steps and invoices.

### Rules

1. A plugin ID is lower case, with dots for namespaces: `manufacturer.product` or the name of the service
   (`huawei.fusionsolar`, `sma.sunnyportal`). A plugin for a national service starts with the country's code
   (`ch.elektroform`, `ch.pronovo`, `ch.swisstopo.buildings3d`).
2. A plugin writes only inside its own namespace. It changes other fields only through the program.
3. Every namespace has a version `v`, an integer. A plugin migrates its own data.
4. The content is plain JSON, in the conventions of this document. Each plugin documents its fields.
5. A program that doesn't know a plugin keeps its data unchanged, also when it saves the file.
6. No secrets in a namespace. A plugin that needs credentials stores them in the operating system's keyring and keeps
   at most a reference: `"credentialRef": "huawei.fusionsolar:installer"`.

### Country extensions

Everything that exists only in one country is kept out of the fields of this document. It lives in an extension
named by the country's ISO 3166 code in lower case, which is a namespace in `ext` like any plugin's. A country
extension holds national coordinates, register numbers and classifications, and it defines the kinds of the steps
with that country's authorities.

The extension for Switzerland, `ch`:

| On | Field | Content |
|---|---|---|
| `site` | `lv95` | Coordinates in the national grid LV95 (EPSG 2056), `e` and `n` in metres |
| `site` | `egid` | Federal building IDs (EGID) of the buildings |
| `site` | `zone` | Building zone (ARE): `code` and `name` |
| municipality snapshot | `buildingFormId` | The form for the solar notice or building permit, in the master data |
| grid operator snapshot | `vseId`, `tagFormId`, `iaFormId` | VSE number of the grid operator; its forms for the TAG and the IA |
| bank account | `iid` | Institution ID of the bank |

| Step `kind` | Step |
|---|---|
| `ch.tag` | Technical connection request to the grid operator (TAG) |
| `ch.ia` | Installation notice (Installationsanzeige) |
| `ch.building_permit` | Solar notice (Solarmeldung) or building permit |
| `ch.esti` | Plan approval by ESTI |
| `ch.pronovo` | Registration with Pronovo for the one-time remuneration (EIV) |
| `ch.sina_dc`, `ch.sina_ac` | Safety certificate (Sicherheitsnachweis), DC and AC side |

A reader that doesn't know a country extension keeps its data and shows its steps by their `kind` and dates.

### Plugin list

The project's `plugins` lists every plugin that wrote data to the file, so a reader without the plugin knows what the
data is:

```json
"plugins": [
    { "id": "huawei.fusionsolar", "version": "1.2", "name": "Huawei FusionSolar", "url": "https://…" }
]
```

## 14. Implementation notes

`model/ModelNode.py` turns the model into plain data and back. Version 3 needs two changes there:

- **Keep unknown fields.** `fromDict()` currently skips keys the class doesn't have, so the next save drops them. For
  version 3 it keeps them in a runtime attribute (for example `_unknown`), and `toDict()` writes them back.
- **Dates as timestamps.** The model holds dates as integers. The forms show and take days in local notation, and
  `Progress` compares numbers where it compares date strings today.
- **Lists of parts.** Version 3 has lists of objects (contacts, orders, devices …). Their class comes from the field,
  not from the file, as for the dicts of parts today.

## 15. Migration from version 2

GnuSolar converts a version 2 project in `formats/pvp.py: _migrate()`, on the plain data. `tools/migrate_pvp.py`
converts all projects at once, with a dry run that lists lost values and a backup of all files.

Version 2 has one building, one plant and one progress per file. In version 3 they become the site, one building with
one roof, and one order of type `new_system`.

### Field mapping

| Version 2 | Version 3 |
|---|---|
| `building.street`, `streetNumber`, `zip`, `city`, `region`, `country` | `site.address` |
| `building.plotNumber` | `site.plotNumber` |
| `building.buildingId` | `site.ext.ch.egid` (one entry) |
| `building.swissGridX`, `swissGridY` | `site.ext.ch.lv95.e`, `.n`; LV03 values (6 digits) get +2 000 000 / +1 000 000. `site.latitude` and `longitude` are calculated from them. |
| `building.municipalityCode`, `municipalityName` | `site.municipality.code`, `.name` |
| `building.areZoneCode`, `areZoneName` | `site.ext.ch.zone.code`, `.name` |
| `building.mainFuseSize` | `site.supply.mainFuse` (number, A) |
| `building.meterNumberOld`, `meterNumberNew` | two devices of kind `meter` with `owner` `grid_operator` and the `number`: the old one with `to` = order `commissioned`, the new one with `from` = it |
| `building.buildingState` | `ext.gnusolar.v2.buildingState` (kept, no v3 meaning yet) |
| `municipality.id`, `code`, `name`, `countryCode`, `stateCode`, `districtCode`, `website`, `mainContact`, `buildingContact` | `site.municipality` snapshot with the same names, `taken` = file date |
| `municipality.fkFormBuilding` | `site.municipality.ext.ch.buildingFormId` |
| `municipality.fkPowerCompany` | dropped: the grid operator is in `site.gridOperator` |
| `powerCompany.id`, `name`, `mainContact` | `site.gridOperator` snapshot with the same names, `taken` = file date |
| `powerCompany.tagContact` | `site.gridOperator.connectionContact` |
| `powerCompany.vseId` | `site.gridOperator.ext.ch.vseId` |
| `powerCompany.address1`, `address2`, `zipCode`, `city` | `site.gridOperator.address` (`zipCode` as text) |
| `powerCompany.fkFormTag`, `fkFormIa` | `site.gridOperator.ext.ch.tagFormId`, `iaFormId` |
| `powerCompany.fkContactTag` | dropped: the contact itself is in `connectionContact` |
| `contacts.contacts.owner` | a contact with `roles: ["owner"]`, if it has any value besides `role` |
| `contacts.contacts.installer_ac` | a contact with `roles: ["electrician"]`, if it has any value besides `role` |
| contact `company` | `organization` |
| contact `street` … `country`, `address1`, `address2`, `floor`, `room` | `address` |
| contact `phone`, `phone2`, `mobile`, `email`, `email2` | `channels`, in this order |
| contact `account*` | one entry in `bankAccounts`; `accountIid` goes to its `ext.ch.iid` |
| `plant.panelDesc`, `totalPanelCount`, `totalPowerDc` | a manual panel type (`model` = `panelDesc`, `power` = `totalPowerDc` / count), one roof with one module group (`count`), a `pv_array` device |
| `plant.totalArea` | the module group's `ext.gnusolar.v2.totalArea` (m²) until the roof has a real outline |
| `plant.inverterDesc`, `totalPowerAc` | a manual inverter type and an `inverter` device |
| `plant.constructionType` | order `constructionType`: `builton` → `on_roof`, `integrated` → `in_roof`, `facade` → `facade` |
| `plant.totalCost` | order `totalCost` |
| `progress.inquiryReceived`, `roofMeasure`, `roofMeasured`, `orderReceived`, `orderRejected`, `constructionStart`, `constructionSort`, `constructionFixed`, `launch`, `archived`, `inactiv` | order `inquiry`, `roofMeasure`, `roofMeasured`, `ordered`, `rejected`, `constructionStart`, `constructionSort`, `constructionFixed`, `commissioned`, `archived`, `inactive` |
| `progress.quote1Sent`, `quote2Sent`, `quote3Sent`, `quote4Sent` | one quote each, with `date` and `state: "sent"`; numbers from `off/O<date>-*.pdf` where one matches |
| `progress.tagSent`, `tagReceived` | step `ch.tag`: `submitted`, `approved` |
| `progress.iaSent`, `iaReceived` | step `ch.ia`: `submitted`, `approved` |
| `progress.bauSent`, `bauReceived` | step `ch.building_permit`: `submitted`, `approved` |
| `progress.materialOrdered`, `materialReceived` | step `material`: `ordered`, `approved` (delivered) |
| `progress.documentationCreated`, `documentationPlaced` | step `documentation`: `filled`, `submitted` |
| `progress.siNaDcOrdered`, `siNaDcReceived` | step `ch.sina_dc`: `ordered`, `approved` |
| `progress.siNaAcOrdered`, `siNaAcReceived` | step `ch.sina_ac`: `ordered`, `approved` |
| `progress.eivComplete`, `eivPayed` | step `ch.pronovo`: `submitted`, `paid` |
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
- **Dates:** version 2 stores days as text like 2015-03-21. They become timestamps of that day (section 3).
  Values that are not such a date:
  - a year only (`"2021"`): the date `null`, the text kept in the step's or order's `notes`
  - two dates (`"2022-09-27/2023-06-28"`): the first date in the field as a timestamp, the whole text in `notes`; such a project
    most likely had two orders and needs a manual look (the dry run lists them)
  - other text (`"other"`): `null`, the text in `notes`
- **IDs:** every object gets a new UUID.

Nothing of a version 2 file is lost: a value that has no place in version 3 goes to `ext.gnusolar.v2` of the object
it belonged to. The dry run of `tools/migrate_pvp.py` lists every such value.

### Folder copies

Project folders that are copies of another project at the same address (`Heid 2.3_2`) are merged by a separate tool,
not by the file migration: their order becomes an order of the main project with `folder` pointing to the copy.

## 16. Reading other formats

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
  came from in their `ext` (`valentin.pvsol`, `pvsyst`, `ch.swisstopo.buildings3d`): file, checksum and the object's ID
  in the source. A later import of a changed file then updates the same objects.
- Not imported: weather data, loss settings, tariffs, charge schedules, consumption and hot water profiles, and
  results other than the yield.
- PV*SOL and PVsyst both ship a component database that is not open; PVsyst's is encrypted. Types come from the copy
  inside the PV*SOL project, or from PVsyst only as a name, and are then matched by manufacturer and model to
  OpenPanelDatabase and OpenInverterDatabase.
- Old PV*SOL premium files (versions 4 to 6) keep module areas and inverters only in the 3D files; current ones also
  list them in `Project.xml`.

## 17. Example

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
        "connections": [],
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
        "created": 1420876800,
        "currency": "CHF",
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
                "from": 1426939200,
                "id": "0a1b2c3d-0000-4000-8000-000000000030",
                "kind": "pv_array",
                "moduleGroupIds": [
                    "0a1b2c3d-0000-4000-8000-000000000012"
                ],
                "orderId": "0a1b2c3d-0000-4000-8000-000000000050"
            },
            {
                "from": 1426939200,
                "id": "0a1b2c3d-0000-4000-8000-000000000031",
                "kind": "inverter",
                "orderId": "0a1b2c3d-0000-4000-8000-000000000050",
                "to": 1781956800,
                "typeId": "0a1b2c3d-0000-4000-8000-000000000021"
            },
            {
                "from": 1781956800,
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
                "from": 1781956800,
                "id": "0a1b2c3d-0000-4000-8000-000000000033",
                "kind": "battery",
                "orderId": "0a1b2c3d-0000-4000-8000-000000000051",
                "typeId": "0a1b2c3d-0000-4000-8000-000000000022"
            }
        ],
        "ext": {},
        "generator": "GnuSolar git...c96ce2c",
        "id": "3f0c2a9e-6a1b-4c8e-9d3f-1b2a3c4d5e6f",
        "modified": 1794315600,
        "notes": "",
        "orders": [
            {
                "commissioned": 1426939200,
                "completed": 1472040000,
                "constructionType": "on_roof",
                "folder": "",
                "id": "0a1b2c3d-0000-4000-8000-000000000050",
                "ordered": 1415793600,
                "state": "completed",
                "steps": [
                    {
                        "dates": {
                            "paid": 1472040000,
                            "submitted": 1449057600
                        },
                        "id": "0a1b2c3d-0000-4000-8000-000000000060",
                        "kind": "ch.pronovo",
                        "state": "paid"
                    }
                ],
                "title": "PV-Anlage 6.2 kWp",
                "type": "new_system"
            },
            {
                "commissioned": 1781956800,
                "folder": "2026_Bat",
                "id": "0a1b2c3d-0000-4000-8000-000000000051",
                "invoices": [
                    {
                        "amount": 12800.0,
                        "currency": "CHF",
                        "date": 1782388800,
                        "id": "0a1b2c3d-0000-4000-8000-000000000070",
                        "kind": "final",
                        "number": "R2026-06-0123"
                    }
                ],
                "ordered": 1772366400,
                "quoteId": "0a1b2c3d-0000-4000-8000-000000000040",
                "state": "in_operation",
                "steps": [
                    {
                        "dates": {
                            "approved": 1774008000,
                            "submitted": 1772712000
                        },
                        "documents": [
                            {
                                "kind": "signed",
                                "path": "2026_Bat/evu/2026-03-05_tag_us.pdf"
                            }
                        ],
                        "id": "0a1b2c3d-0000-4000-8000-000000000061",
                        "kind": "ch.tag",
                        "state": "approved"
                    }
                ],
                "title": "Batterie 10 kWh",
                "type": "battery"
            }
        ],
        "plugins": [
            {
                "id": "ch",
                "name": "Switzerland",
                "version": "1"
            }
        ],
        "quotes": [
            {
                "currency": "CHF",
                "date": 1770724800,
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
            "ext": {
                "ch": {
                    "lv95": {
                        "e": 2632561.2,
                        "n": 1265432.8
                    },
                    "v": 1
                }
            },
            "gridOperator": {
                "ext": {
                    "ch": {
                        "tagFormId": 4,
                        "v": 1
                    }
                },
                "id": 402,
                "name": "Elektra Zeiningen",
                "taken": 1794312000
            },
            "latitude": 47.5419,
            "longitude": 7.8696,
            "municipality": {
                "code": "4264",
                "name": "Zeiningen",
                "taken": 1794312000
            },
            "plotNumber": "1060",
            "supply": {
                "earthingSystem": "tn_c_s",
                "frequency": 50,
                "mainFuse": 40,
                "phases": 3,
                "voltage": 400
            }
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

## 18. Open points

- **Designs before an order:** devices and strings exist only for orders, so a quoted design has its wiring only in
  the simulation file. If string plans are needed at the quote stage, designs get their own planned devices.
- **Terminals inside a device:** a connection ends at a port, not at a single terminal. Terminal numbers, and which
  core of a cable goes to which terminal, are not recorded.
- **Where devices and cables are in the building:** a device has a `location` text and a parent, a cable a length,
  but neither has a position or a route in space yet.
- **Curved and irregular roofs** (barrel roofs, roofs that are not one plane) have no form here; they would be
  approximated by several roofs.
- **Pricing of items:** whether quotes and orders carry full positions with prices, or only the devices and a total,
  until GnuSolar calculates quotes itself.
- **Owner export:** which parts of the file an owner gets (likely everything except prices, notes and installer-only
  plugin data), and in which form.
- **Schema:** a JSON Schema for validation, kept next to this document.
- **`building.buildingState`** (new or existing building) has no field in version 3 yet; it is kept under
  `ext.gnusolar.v2` until it gets one.
