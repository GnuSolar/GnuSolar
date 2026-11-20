# GnuSolar project file, version 2

Version 2 is the format GnuSolar on the branch `main` reads and writes (`formats/pvp.py`). Its successor is version 3
(`../file_format_v3/file_format.md`), which converts version 2 files when it reads them (section 15 there).

A version 2 file describes one project: one building, one plant, the dates of its progress, and the people and
offices involved. A second job at the same address, such as a battery added later, is a copy of the project folder
with a file of its own (`Heid 2.3_2` next to `Heid 2.3`). Its `base` names the folder of the project it extends.
GnuSolar creates such a project ("Erweiterung erstellen") with the `building`, `contacts`, `municipality` and
`powerCompany` of the first project; its `plant`, `progress` and `comment` start empty.

The format is the model of the program written out as plain JSON: every field of the classes in `model/` is in the
file, under the same name.

## 1. The file

| | |
|---|---|
| Name | `plant.pvp`, one per project folder |
| Project folder | `<projectRoot>/<city>/<street> <number>`, made by the project list when a project is created. `projectRoot` is a setting of the program. |
| Encoding | UTF-8, characters such as umlauts written as they are |
| Syntax | JSON (RFC 8259) |
| Formatting | 4 spaces indent, keys sorted, no line break at the end (`json.dumps(..., indent=4, sort_keys=True, ensure_ascii=False)`) |
| Writing | to `plant.pvp.tmp` first, then renamed, so a crash never leaves a half written file |
| Attachments | Not in the file. Quotes, invoices, forms and plans lie in the project folder, the file doesn't name them. |

```json
{
    "format": "gnusolar-project",
    "version": 2,
    "project": {}
}
```

| Field | Content |
|---|---|
| `format` | Always `"gnusolar-project"` |
| `version` | Always `2` |
| `project` | The project, sections 3 to 9 |

A reader refuses a file with another `version`. A file of version 1 has no `format`; it is recognised by its key
`py/state` and refused as well (section 11).

## 2. Conventions

- **Every field is always written.** A field that was never set is `null`. So the structure of the file doesn't vary:
  a version 2 file has 254 fields, more only if a contact of another role was added (section 7). Files saved
  before 20 November 2026 have fewer: 246 lack `type` and `base`, which GnuSolar reads as `"pvSystem"` and `null`;
  248 lack `formality` in the 6 contacts, which GnuSolar reads as `"formal"`. It writes them the next time it saves
  the file.
- **Values are text, as typed.** The forms of the program store what was typed, without checking it. A reader must
  expect any text in any field.
- **Empty** is `null` or `""`. Both mean the same; `""` is what a form leaves when its text is deleted.
- **Dates** are text `YYYY-MM-DD`, the day only, for example `"2015-03-21"`. A few hold other text: a year only
  (`"2021"`), two dates (`"2022-09-27/2023-06-28"`), or a word.
- **Numbers** are text as typed, with a decimal point or a comma. Their units are given per field.
- **Exceptions to text:** the ids of rows of the master data are integers (`municipality.id`, `fkFormBuilding`,
  `fkPowerCompany`, `powerCompany.id`, `zipCode`, `fkContactTag`, `fkFormTag`, `fkFormIa`), and
  `progress.constructionFixed` is `true` or `false`.
- **No ids, no lists.** Every part is an object under a fixed name; the contacts are found by their role.
- **Unknown fields are dropped.** GnuSolar reads only the fields its classes have and writes only those. A field
  another program adds is lost the next time GnuSolar saves the file.
- **Master data** (municipalities, grid operators, forms) comes from GnuSolar's database `data/master.db`. The file
  holds a copy of the values taken from it and the id of the row.

## 3. The project object

```json
"project": {
    "building": {},
    "plant": {},
    "progress": {},
    "contacts": { "contacts": { "owner": {}, "installer_ac": {} } },
    "municipality": {},
    "powerCompany": {},
    "comment": null,
    "state": null,
    "type": "pvSystem",
    "base": null
}
```

| Field | Content |
|---|---|
| `building` | The building and its place (section 4) |
| `plant` | The solar plant, summed up (section 5) |
| `progress` | The dates of the job (section 6) |
| `contacts` | The client and the electrician (section 7) |
| `municipality` | The municipality, copied from the master data (section 8) |
| `powerCompany` | The grid operator, copied from the master data (section 9) |
| `comment` | Free text: notes on the project |
| `state` | `Request`, `Quote`, `Wait`, `Order`, `Construction`, `Running` or `BuiltOther`. Not kept up to date: GnuSolar derives the state of a project from its dates (`Progress.getState()`). Most files have `null`, the others `Running`. |
| `type` | What the project builds: `pvSystem` (solar plant), `battery`, `chargingPile` (charging station) or `other` |
| `base` | The project this one extends, such as the plant a battery is added to: the folder of that project, relative to the folder of this one, with `/` between the parts (`"../Heid 2.3"`). `null` or `""` if it extends none. |

## 4. building

| Field | Content |
|---|---|
| `street`, `streetNumber`, `zip`, `city` | Address of the building |
| `region`, `country` | Not used, always `null` |
| `buildingState` | `new` or `existing` building |
| `buildingId` | Swiss federal building id (EGID) |
| `plotNumber` | Number of the parcel in the land register |
| `swissGridX`, `swissGridY` | Swiss coordinates of the building, east and north in metres: LV03 (6 digits before the point) as the federal lookup gives them, a few files LV95 (7 digits) |
| `municipalityCode`, `municipalityName` | Official number (BFS-Nr.) and name of the municipality, from the federal lookup |
| `areZoneCode`, `areZoneName` | Building zone of the Federal Office for Spatial Development (ARE) |
| `meterNumberOld`, `meterNumberNew` | Number of the grid operator's meter before and after the plant was built |
| `mainFuseSize` | Rating of the house connection fuse, A |

The button "Update von Adresse" fills `buildingId`, the coordinates, the municipality, `plotNumber` and the zone from
the federal geodata services (`api3.geo.admin.ch`).

## 5. plant

| Field | Content |
|---|---|
| `constructionType` | `builton` (on the roof), `integrated` (in the roof), `facade`, or empty |
| `totalPowerDc` | Power of the modules, kWp |
| `totalPanelCount` | Number of modules |
| `totalArea` | Area of the modules, m² |
| `panelDesc` | The modules, as text: maker and model |
| `totalPowerAc` | Power of the inverters, kW |
| `inverterDesc` | The inverters, as text |
| `totalCost` | Total cost of the plant, CHF, as needed for subsidy and permit forms |

## 6. progress

The dates of the job, in the order it goes. Every field except `constructionFixed` is a date (section 2).

| Field | Content |
|---|---|
| `inquiryReceived` | Inquiry received (Anfrage) |
| `roofMeasure`, `roofMeasured` | Roof measurement planned, done |
| `quote1Sent`, `quote2Sent`, `quote3Sent`, `quote4Sent` | Quotes sent, the first to the fourth |
| `orderReceived` | The client gave the order (Zusage) |
| `orderRejected` | The client turned it down (Absage) |
| `tagSent`, `tagReceived` | Connection request to the grid operator (TAG) sent, approved |
| `iaSent`, `iaReceived` | Installation notice to the grid operator (IA) sent, confirmed |
| `bauSent`, `bauReceived` | Solar notice or building application to the municipality sent, approved |
| `partialInvoiceSent`, `partialInvoiceReceived` | First partial invoice (Akonto) sent, paid |
| `partialInvoice2Sent`, `partialInvoice2Received` | Second partial invoice sent, paid |
| `materialOrdered`, `materialReceived` | Material ordered, delivered |
| `constructionStart` | Start of construction |
| `constructionSort` | A date only to sort the construction planning; empty means `orderReceived` |
| `constructionFixed` | `true` if the construction date can not be moved |
| `launch` | Commissioning, first day of operation (Inbetriebnahme) |
| `documentationCreated`, `documentationPlaced` | Plant documentation made, handed over |
| `finalInvoiceSent`, `finalInvoiceReceived` | Final invoice sent, paid |
| `siNaDcOrdered`, `siNaDcReceived` | Safety certificate DC (SiNa, with the measurement protocol) ordered, received |
| `siNaAcOrdered`, `siNaAcReceived` | Safety certificate AC ordered, received |
| `eivComplete`, `eivPayed` | Federal one-off remuneration (Pronovo EIV): complete, paid out |
| `archived` | Project archived: everything done |
| `inactiv` | Project inactive: nothing to do, it may or may not be built |

## 7. contacts

```json
"contacts": {
    "contacts": {
        "owner": {},
        "installer_ac": {}
    }
}
```

`contacts.contacts` holds one contact per role. `owner` (Bauherr) is the client, `installer_ac` (Elektriker AC) the
electrician who connects the plant. Both are always there. The tree of the project window can add a contact of
another role (`test`), which is then written under that name.

Every contact in the file, also the ones of the municipality and the grid operator, has these fields:

| Field | Content |
|---|---|
| `role` | The role: `owner`, `installer_ac`, `mun_main`, `mun_building`, `pow_main`, `pow_tag`, `test`. Older files can have `null`. |
| `company`, `department` | Organisation |
| `title`, `firstName`, `middleName`, `lastName`, `nickName` | Person. `title` is the Anrede as typed: `Herr`, `Frau`, `Herr und Frau`, `Familie` |
| `formality` | How the person is addressed in letters: `formal` (Sie, the default) or `informal` (Du). Older files and contacts have none, which counts as `formal`. |
| `street`, `streetNumber`, `address1`, `address2`, `zip`, `city`, `country`, `floor`, `room` | Address |
| `email`, `email2`, `phone`, `phone2`, `mobile` | How to reach them |
| `accountOwner`, `accountBank`, `accountIban` | Bank account |
| `accountIid` | Institution identifier of the bank (Switzerland) |
| `accountBic` | Business identifier code of the bank (SWIFT) |

## 8. municipality

A copy of the municipality's row in the master data, made when the button "Update von Adresse" was used.

| Field | Content |
|---|---|
| `id` | Row in the master data (integer) |
| `code` | Official number of the municipality (BFS-Nr.) |
| `name` | Name |
| `countryCode`, `stateCode`, `districtCode` | Country (`CH`), canton and district |
| `website` | Website of the municipality |
| `mainContact` | Main address of the municipality, a contact with role `mun_main` |
| `buildingContact` | The building authority, a contact with role `mun_building` |
| `fkPowerCompany` | Row of the grid operator of the municipality in the master data (integer) |
| `fkFormBuilding` | Row of the municipality's form for the solar notice in the master data (integer) |

## 9. powerCompany

The grid operator (Elektrizitätswerk, EVU), copied from the master data in the same way.

| Field | Content |
|---|---|
| `id` | Row in the master data (integer) |
| `vseId` | Number of the grid operator at the VSE (Verband Schweizerischer Elektrizitätsunternehmen) |
| `name` | Name |
| `address1`, `address2`, `zipCode`, `city` | Address; `zipCode` is an integer |
| `mainContact` | Main address, a contact with role `pow_main` |
| `tagContact` | Who handles connection requests (TAG), a contact with role `pow_tag` |
| `fkContactTag` | Row of that contact in the master data (integer) |
| `fkFormTag`, `fkFormIa` | Rows of the grid operator's forms for the connection request and the installation notice (integers) |

## 10. Example

A project with invented data. Contacts with all fields empty are shortened to `{ … }`; GnuSolar writes every field.

```json
{
    "format": "gnusolar-project",
    "project": {
        "base": null,
        "building": {
            "areZoneCode": "11",
            "areZoneName": "Wohnzonen",
            "buildingId": "190335642",
            "buildingState": "existing",
            "city": "Musterwil",
            "country": null,
            "mainFuseSize": "40",
            "meterNumberNew": "222",
            "meterNumberOld": "111",
            "municipalityCode": "4264",
            "municipalityName": "Musterwil",
            "plotNumber": "1060",
            "region": null,
            "street": "Kirchweg",
            "streetNumber": "26",
            "swissGridX": "632561.2",
            "swissGridY": "265432.8",
            "zip": "4314"
        },
        "comment": "Hund im Garten",
        "contacts": {
            "contacts": {
                "installer_ac": { "role": "installer_ac", "company": "Elektro Beispiel AG", "…": null },
                "owner": { "role": "owner", "title": "Herr", "firstName": "Hans", "lastName": "Muster", "formality": "formal", "email": "hans@example.ch", "…": null }
            }
        },
        "municipality": {
            "buildingContact": { "role": "mun_building", "…": null },
            "code": "4264",
            "countryCode": "CH",
            "districtCode": null,
            "fkFormBuilding": 7,
            "fkPowerCompany": 402,
            "id": 4264,
            "mainContact": { "role": "mun_main", "…": null },
            "name": "Musterwil",
            "stateCode": "AG",
            "website": "https://www.example.ch"
        },
        "plant": {
            "constructionType": "builton",
            "inverterDesc": "Fronius Symo 10.0-3-M",
            "panelDesc": "JA Solar JAM54S30 440",
            "totalArea": "47.5",
            "totalCost": "18450",
            "totalPanelCount": "24",
            "totalPowerAc": "10",
            "totalPowerDc": "10.56"
        },
        "powerCompany": {
            "address1": "Kirchweg 1",
            "address2": null,
            "city": "Musterwil",
            "fkContactTag": null,
            "fkFormIa": null,
            "fkFormTag": 4,
            "id": 402,
            "mainContact": { "role": "pow_main", "…": null },
            "name": "Elektra Musterwil",
            "tagContact": { "role": "pow_tag", "…": null },
            "vseId": null,
            "zipCode": 4314
        },
        "progress": {
            "archived": null,
            "bauReceived": null,
            "bauSent": "2026-04-22",
            "constructionFixed": false,
            "constructionSort": null,
            "constructionStart": "2026-06-02",
            "documentationCreated": null,
            "documentationPlaced": null,
            "eivComplete": null,
            "eivPayed": null,
            "finalInvoiceReceived": null,
            "finalInvoiceSent": "2026-06-25",
            "iaReceived": null,
            "iaSent": "2026-05-04",
            "inactiv": null,
            "inquiryReceived": "2026-03-01",
            "launch": "2026-06-20",
            "materialOrdered": "2026-05-12",
            "materialReceived": null,
            "orderReceived": "2026-04-15",
            "orderRejected": null,
            "partialInvoice2Received": null,
            "partialInvoice2Sent": null,
            "partialInvoiceReceived": "2026-06-20",
            "partialInvoiceSent": "2026-06-01",
            "quote1Sent": "2026-03-20",
            "quote2Sent": "2026-04-02",
            "quote3Sent": null,
            "quote4Sent": null,
            "roofMeasure": null,
            "roofMeasured": "2026-03-10",
            "siNaAcOrdered": null,
            "siNaAcReceived": null,
            "siNaDcOrdered": null,
            "siNaDcReceived": null,
            "tagReceived": "2026-05-10",
            "tagSent": "2026-04-20"
        },
        "state": null,
        "type": "pvSystem"
    },
    "version": 2
}
```

## 11. Version 1

Until 9 November 2026 GnuSolar saved the objects of the program as they were, with the Python library jsonpickle:
the file held class names (`py/object`) and the state of each object (`py/state`), and changing a class could make
old files unreadable. Version 2 stores the same fields as plain data. All projects were converted on 9 November 2026
with `tools/migrate_pvp.py` of commit `cbb39e5`; reading version 1 was dropped afterwards (commit `07ee9c0`).

## 12. Implementation

| Part | Where |
|---|---|
| Reading and writing the file, refusing other versions | `formats/pvp.py` |
| Model ↔ plain data: the fields of the classes, unknown fields dropped | `model/ModelNode.py` |
| The parts of sections 4 to 9 | `model/Building.py`, `Plant.py`, `Progress.py`, `Contacts.py`, `Contact.py`, `Municipality.py`, `PowerCompany.py`, `PvProject.py` |
| Converting all files of a folder to the current version, with a dry run and a backup | `tools/migrate_pvp.py` |
