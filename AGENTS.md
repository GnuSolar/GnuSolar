# GnuSolar: instructions for agents

The software for installers of solar systems: planning, building, maintaining and upgrading a system, and its
finances and orders. `doc/file_format_v2/file_format.md` describes the file format this branch reads and
writes. `doc/file_format_v3/` describes the next version, which the branch `file-format-v3` implements.

Read `../Harness/MAP.md` and `../Harness/RULES.md` first, if they are there: the map of the projects that belong
together and the rules that hold in all of them. The first of those rules: edit only this project. A change
needed in another project is not made from here; it is written into `../Harness/REQUESTS.md`.

## This project

- Owns: the program and its file format.
- Reads, never edits: ModbusSpec's vocabulary and device kinds; OpenSolarPanelDatabase and
  OpenSolarInverterDatabase for panel and inverter data.

## Rules here

- `~/amslersolar` is the company's live business data, and this checkout is the program that runs on it. Never
  write there unless the user asks for exactly that write. Try things on copies, with the program pointed at a
  scratch folder.
- A half-finished change in this working tree can be started on real data. Do larger changes in a separate git
  worktree and bring them in when they are whole.
- The folder layout of a project is a setting of each installer, not fixed in the code.
- Device values use the names of ModbusSpec's `vocabulary.yaml` where one exists.
- Push only when asked.

## Check your work

This branch has no automated tests; they are on the branch `file-format-v3`. Start the program with its home
folder pointed at a scratch folder, so it reads and writes `.gnusolar/config.json` there, and set the folder of
the projects in its preferences to a copy of the data:

```sh
HOME=/tmp/gnusolar-test python3 GnuSolar.py
```
