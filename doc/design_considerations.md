# Design considerations for the project file

`file_format.md` says what the format is. This document says why, which questions came up while defining it, what
was decided and what is still open. It records the state of 12 November 2026.

A **site** is one place with what stands there; one file is one site. A **project** is one piece of work for a
client, from the inquiry to the final invoice. Until 12 November 2026 the file called the site `project` and a
project `order` (section 4).

## 1. Purpose

The work on version 3 is about the file format, not about one program. The format exists so that

- several tools can read and write the same data, GnuSolar being one of them,
- a web viewer can show a plant to its owner,
- different people can work on the same data.

A format is therefore not measured by how much it can hold, but by how hard it is to read and to write correctly.
Detailed sections (wiring, strings, single panels) are not a burden as long as they are optional: a planning tool,
a viewer and a service tool each take the sections they need.

How GnuSolar's window presents the data is a separate matter. A new single-roof plant should be no more work to
enter than it was with version 2, whatever the file looks like underneath.

Decided earlier and kept:

- Plain JSON, readable without GnuSolar.
- Dates and times are Unix timestamps everywhere.
- The format is country independent. National coordinates, register numbers and the steps with a country's
  authorities belong to a country extension.
- External services are reached through plugins that can be enabled. A plugin stores its data in the file, in its
  own namespace.
- The installer controls the data: local files, no service that has to be asked for them. Manufacturer clouds are
  needed, the key is to have the option.

## 2. What one file represents

Version 2 never had to answer this. One folder held one file, which was one plant built in one project. With
several projects at the same address there are three things where there was one:

| Thing | What it is | In the file |
|---|---|---|
| The place | Address, plot, buildings, roofs, grid operator | fields of the site, `buildings` |
| What stands there | The devices over time | `devices`, `strings`, `connections` |
| A piece of work | From inquiry to final invoice | `projects`, with `quotes` |

The question is which of them a file, and its folder, stands for.

**State: decided on 12 November 2026.** One file is one site (variant A), and the names say so (section 4). The
variants and arguments below are kept as the record of the decision.

### A. One file per site, several projects in it

- The second project knows what is already there. A battery project sees the existing modules and inverter, which
  the connection request asks for.
- Devices have a history: the old inverter ends on the day its replacement starts.
- Address, owner, meter numbers and roofs are entered once and corrected in one place.
- There is one answer to "what stands at this address today".
- The price: a current project inside the file, folders per project, the merge of the existing copies, and the
  naming problem. It is carried by every site, also by those that never get a second project.
- Two people, or two windows, working on two projects of the same site edit the same file.

### B. One file per project, folders side by side (`Heid 2.3`, `Heid 2.3_2`)

- Simple, and how the existing data is. A project is a project, a folder is a folder.
- Each project is self-contained and can be archived on its own.
- The second project starts blind: the existing plant is typed in again, site data is copied and then drifts.
- Nothing but the folder name links the projects of one site.
- "What stands at this address today" is spread over several files.

### C. One file per project, with a real link

"New project at this site" creates the next folder and copies site, contacts, roofs and the devices in place into
it, marked as existing. The new file records which project it follows. This gives the second project its starting
knowledge without a shared file. It does not give one maintained record: after the copy the files drift again.

### Arguments for the site

- **Which can exist without the other?** A plant exists without any project of ours: one built by someone else,
  or ours after the final invoice. A project cannot exist without a site.
- **Which has a single truth?** At any moment there is exactly one answer to what is on the roof. Projects are
  separate stories that don't contradict each other when they differ.
- **Which lasts?** A project is over in months, the plant is there for thirty years. What is looked up when a
  customer calls about a fault is the address.
- **What the device model assumes.** A start date, an end date and "replaces" only make sense if the file is the
  site. If the file were one project, the format would need an "already there" marker instead.

### Arguments for the project

- The unit of daily work is the project: statuses, to-dos, quotes and invoices are all per project, and the
  project list has one row per project.
- Most sites have one project. In the real data of 11 November 2026 there are 758 project folders at 692 sites;
  648 sites (94 %) have one project, 33 have two, 7 have three, and one each has four, five, six and eight.
  (Folders named `X_2`, `X_3` next to a folder `X` were counted as further projects of `X`.)
- Tools that run the same paperwork work per project (below).

The 94 % is a low estimate of the future: the installed base grows and ages, so batteries, chargers, replacements
and repairs become a larger share of the work.

Whatever the file stands for, the two views can coexist: the file stores the site, the project list shows the
projects.

### What other software does

| Family | Examples | Unit |
|---|---|---|
| Design and simulation | PV\*SOL, PVsyst, Aurora, OpenSolar | One site with one planned plant, sometimes with variants. No time. |
| Process and paperwork for installers | Solarstream, ElektroForm solar | One project. A later job is a further project. |
| Service, maintenance and registers | ServiceTitan, maintenance systems, Marktstammdatenregister, Pronovo | One site that holds the equipment with its history. Jobs point to it. |

- **PV\*SOL:** one project file is one planned plant with its offer: offer number, customer data, plant address.
  No history, no second job.
- **PVsyst:** a project is one geographic site with weather data; the site is a file of its own. Inside are
  variants of the system. No customers, no jobs.
- **Aurora Solar:** one project per site, with a customer; inside are one or more designs, which are alternatives.
  For a retrofit the existing modules are marked as existing inside a new design.
- **OpenSolar:** a project is defined as a location but built for one sale: one sold date, one sold system, one
  installed system. Several systems per project are alternatives. A retrofit is a flag plus a summary of the
  existing system, without dates and without a link to the project that built it. Small work after installation
  stays in the project and is billed with standalone invoices. Contacts are records of their own, the workflow is
  defined once per company, documents are sorted by tags instead of folders. It is free of charge, not open
  source: the data lies on the vendor's servers and the programming interface is charged per project.
- **Solarstream:** a project is one job run through a workflow. Battery retrofits, service and maintenance are
  project types next to new installations. Whether projects at one address are linked is not documented.
- **ElektroForm solar:** billed and organised per project (forms of the grid operator, Pronovo registration,
  documents). Nothing on extensions or existing equipment. The same vendor's program for electricians speaks of
  objects, found by meter number.
- **ServiceTitan:** equipment belongs to the location, not to the customer or the job. Jobs are attached to
  equipment, a replaced unit is marked as replaced and kept.
- **Registers:** the Marktstammdatenregister groups units into a plant at a location, a storage added later is a
  further unit there. Pronovo records an addition as a plant with extensions.

Everyone keys on the site. The difference is time: tools that only sell or only run paperwork need no history,
tools that deal with what was built separate the lasting equipment from the passing jobs. OpenSolar shows that
selling works without a plant record, and what that costs afterwards: the truth about the plant is one project's
installed system plus whatever later projects say exists.

## 3. How a site changes over time

This describes variant A, as specified.

A project never rewrites the site. It adds devices to it and ends devices in it, each with a date. The site as it
stands on a day is calculated, not stored.

| Condition of a device | In the file |
|---|---|
| Planned | belongs to a project (`projectId`), has no `from` |
| Installed | has `from`, no `to` |
| Removed | has `to` |

The installed system on a date is every device with `from` on or before that date and `to` empty or after it.

| Step | Site part | Project part |
|---|---|---|
| Site only | Address, plot, building, roofs, grid operator, contacts. The existing meter is a device with `from`. | – |
| Lead | Roofs are measured or imported. | Project 1 with its inquiry date |
| Quote | Module groups are drawn on the roofs, marked with their design. No devices. | Designs, quotes |
| Sale | The devices of project 1 appear as planned. | Date ordered, accepted quote, steps |
| Installation | On the commissioning date the planned devices get it as `from`; the old meter gets it as `to`. | Commissioning, invoices, completion |
| Site with PV | Unchanged | Project 1 stays as history |
| Battery project | At its sale the battery appears as planned. A hybrid inverter is added as the replacement of the old one. At commissioning both start and the old inverter ends. | Project 2, like project 1 |
| Service call | Nothing, if nothing is exchanged. A replaced device is a new device that replaces the old one; a replaced module is recorded on its module group. | Project 3 of type repair |

While a project runs, its forms ask two things: what does this project install, and what was there before it.

What GnuSolar does by itself: setting the commissioning date starts the project's planned devices and ends the ones
they replace; a replacement device is created linked to the old one; the state of a project follows from its dates.

What is done by hand: after a sale the planned devices are added on the project (the specification says the
positions of the accepted quote are copied, GnuSolar doesn't do it); a device removed without a replacement gets
its `to` by hand.

### Gaps

- **A project cancelled after the sale** leaves its planned devices behind. There is no rule for them yet.
- **Site facts have no history.** Owner, address and roof geometry are the current values. Only devices, and the
  meter as one of them, carry dates.
- **"What was there before" ignores dates** in GnuSolar: it is every installed device of other projects, so a
  finished first project sees a later battery as existing.
- **A site without a project** is valid in the file, but GnuSolar creates a first project as soon as it needs one.

## 4. Names

**State: decided on 12 November 2026.** The top level is the `site`, a piece of work is a `project`.

| | Before | Now |
|---|---|---|
| Format name | `gnusolar-project` | `gnusolar-site` |
| Top level | `project` | `site` |
| Piece of work | `orders`, `orderId` | `projects`, `projectId` |
| Address, coordinates, grid connection, municipality, grid operator | a section `site` inside the project | fields of the site itself |

Why the old names had to go:

- `order` was misleading. It suggests the moment the client signs, or an order of material from a supplier, but
  the thing exists from the first inquiry on and can end rejected.
- "Project" and "plant" were used for the same thing, as the file name `plant.pvp` shows: the name says plant, the
  extension stands for PV project. With several pieces of work in one file the top level needed a name of its own.
- A section `site` inside a site made no sense, so its fields moved up. This is the one change of structure; all
  else is names.

What was considered instead: `job` for the piece of work with the top level left as `project` (a smaller rename,
but "project" would have kept meaning the file), and `plant` for the top level.

What stays:

- The date `ordered` and the step state `ordered`: they name the one moment that is the order.
- The file name `plant.pvp`.
- The fields of version 2 that document templates and form scripts use (`orderReceived`, `orderRejected`, …).
- GnuSolar's setting `projectRoot` and its window with the list of projects, which shows one row per project.

"Project" changed its meaning rather than disappearing, so an old text that says project may mean the site.

Three real files had already been saved with the old names. They are read as before and renamed on the way
(`file_format.md`, section 15); the old file is kept next to the new one.

In the window the site is "Standort" and a project is "Projekt" (before: "PV Projekt" and "Auftrag").

## 5. Folders

Decided:

- **The format knows no folder names.** A document is a relative path. How a project folder is organised is the
  installer's matter, every installer handles it differently.
- **Folder names are a setting, not code.** GnuSolar asks for them in the preferences. A new installation gets
  written out names (Offerten, Rechnungen, …), because most installers have no Unix background. Short names
  (`off`, `fin`, `doc`, `evu`, `gov`, `cad`, `gis`, `sim`, `pic`, `etc`) remain available as a preset and are what
  an existing installation keeps.
- **The first project of a site gets no folder of its own.** Its documents lie in the project folder. With 94 % of
  the sites having one project, a subfolder for every project would separate nothing.

Open: where the documents of a later project go. GnuSolar needs some folder for them, otherwise files with fixed
names (the plant documentation, the measurement protocol) collide with those of the first project.

| | Folder side by side (`Heid 2.3_2`) | Subfolder (`Heid 2.3/2026 Batterie`) |
|---|---|---|
| Existing data | Nothing moves | The existing copies have to be moved |
| The project folder | No longer holds the whole site; paths leave it (`../Heid 2.3_2/…`) | Self-contained: can be moved, backed up or handed over as one |
| Name | `_2` says neither what nor when | Can say both |
| Site files (3D model, maps, photos) | No obvious home when seen from `_2` | Lie next to the project folders |
| Archiving one project | Easy | Only together with the site |
| Link | A naming convention | The folder structure |

Today GnuSolar suggests a subfolder such as `2026 Batterie` for every project after the first, and the tool that
merges existing copies points to them where they are (`../Heid 2.3_2`).

Still fixed in GnuSolar's code: the place of a project folder (`<root>/<city>/<street> <number>`) and the file
names of the documents it creates.

## 6. What shared use requires

Reading the format is easy: plain JSON, documented units, one rule for time. Writing is where several tools and
several people can damage a file. The format does not need to become simpler for that, it needs these rules:

| # | Rule | Why | State |
|---|---|---|---|
| 1 | A small required core, everything else explicitly optional | A simple tool must know what it can rely on | Not stated in the specification |
| 2 | Dates are the truth, derived values are marked as such | The `state` of a project follows from its dates but is also stored; a tool that changes one and not the other makes the file contradict itself | `state` is stored "for other readers", the rule is not spelled out for writers |
| 3 | Fields of one program don't belong in the core | `constructionSort`, `constructionFixed` and `folder` describe how GnuSolar plans and files things | In the core today |
| 4 | A defined part the owner may see | The file holds prices, internal notes, other contacts and invoices next to the plant; a web viewer needs a rule which sections are the plant and which the installer's business, also for documents | Open point "owner export" |
| 5 | A change marker per object | Objects have permanent ids, so two copies can be paired, but nothing says which copy of an object is newer. There is one `modified` for the whole file, and nothing detects that a file changed since it was loaded: the last save wins | Missing |
| 6 | A schema | Other tools have only the prose document to check against | Open point |

Already there: unknown fields are kept by every writer, ids are permanent, newer versions are refused instead of
guessed at, and the file is formatted so that it diffs well.

## 7. Summary

| Question | State |
|---|---|
| Purpose: a format for several tools, a web viewer and several people | Decided |
| Unix timestamps, country independence, plugins with data in the file | Decided |
| Folder names are the installer's setting; the first project gets no folder | Decided |
| What one file represents: the site | Decided |
| Names: `site` for the top level, `project` for a piece of work | Decided |
| Where a later project's documents go: folder side by side or subfolder | Open |
| The six rules for shared use | Proposed, not specified |
| Cancelled projects, history of site facts | Open, wait for a real case |

## Sources

- [Aurora Solar API: projects](https://docs.aurorasolar.com/reference/projects), [key terms](https://docs.aurorasolar.com/v2022.09/reference/key-terms), [storage retrofit projects](https://help.aurorasolar.com/hc/en-us/articles/33113633064851-PV-Storage-Retrofit-Projects)
- [OpenSolar API: projects](https://developers.opensolar.com/api/projects/), [systems](https://developers.opensolar.com/api/system/), [proposal data](https://developers.opensolar.com/api/proposal-data/), [events](https://developers.opensolar.com/api/events/), [access plans](https://developers.opensolar.com/api/api-access-plans/)
- [OpenSolar help: designing on an existing system](https://support.opensolar.com/hc/en-us/articles/13396692177551-How-to-design-on-existing-system-Retrofit), [standalone invoices](https://support.opensolar.com/hc/en-us/articles/9970132923919-Standalone-Invoices), [why OpenSolar is free](https://www.opensolar.com/free/)
- [PV\*SOL help: project data](https://help.valentin-software.com/pvsol/en/pages/project-data)
- [PVsyst terms (lefixea)](https://www.lefixea.com/article/what_is_pvsyst19)
- [pv magazine: Solarstream, start-up of the month](https://www.pv-magazine.de/2026/02/27/start-up-des-monats-solarstream-digitalisiert-die-projektabwicklung-fuer-solarinstallateure/), [Solarstream for solar installers](https://www.solarstream.ch/de-ch/for-solar-installer)
- [Brunner Informatik: ElektroForm solar](https://brunnerinformatik.ch/loesungen-und-produkte/meldewesen-m2/installateure-und-solarteure/elektroform-solar/), [Swissolar: ElektroForm solar beta](https://www.swissolar.ch/de/news/detail/elektroform-solar-beta-verfuegbar-44659)
- [ServiceTitan: installed equipment](https://help.servicetitan.com/docs/track-manage-installed-equipment)
- [Marktstammdatenregister: data structure](https://www.marktstammdatenregister.de/MaStRHilfe/files/regHilfen/MaStR-Datenstruktur_(Marktakteure_Einheiten_und_Gruppierungsobjekte)_final.pdf)
- [Pronovo: guideline on the one-off remuneration for photovoltaics](https://pronovo.ch/wp-content/uploads/2020/06/200429_Richtlinien_EVS_Photovoltaik_final.pdf)

The descriptions of other software rest on public documentation and help pages read on 12 November 2026. Several
of them publish no description of their data model, so parts are inferred from field names, examples or pricing.
