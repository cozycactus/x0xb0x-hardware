# Fabrication packages — KiCad working revision 27

These are the order packages for both x0xb0x boards: Gerbers, drills, drill maps, BOM and placement files. They were exported with KiCad 10.0.7 from `../../mainboard/mainboard.kicad_pcb` and `../../ioboard/ioboard.kicad_pcb` (revision 27, unchanged by this step). No fab house is chosen and nothing is ordered.

**Superseded by [revision 29](../revision-29/README.md).** Revision 29 changed the mainboard copper, so this mainboard package no longer matches the board file and its `verify_packages.py` now fails on the mainboard. It stays as the record of the revision that matches the original Eagle boards with nothing added.

**Status at revision 27: both packages were ready to order**, once the owner has made the choices in [mainboard/FAB-NOTES.md](mainboard/FAB-NOTES.md) and [ioboard/FAB-NOTES.md](ioboard/FAB-NOTES.md). The recommendations are 1.6 mm FR-4, 1 oz copper, lead-free HASL, green mask with white silkscreen, vias tented as exported, the fab's own electrical test, and no panelisation. A first export from revision 26 found two board defects; revision 27 corrects them (`../../validation/models-review-27/`):

- **Mainboard:** the saved ground pours predated revision 26's longer SIP9 pads and touched 23 of them. They are now refilled.
- **I/O board:** the rear-plate datum was a second outline on Edge.Cuts. It is now on Dwgs.User.

## Contents

| Path | What |
|---|---|
| `<board>/gerbers/` | Gerber X2 (F/B copper, mask, paste, silkscreen, Edge_Cuts), Gerber job file, Excellon PTH and NPTH (metric), PDF drill maps, drill report: the fab upload |
| `<board>/x0xb0x-<board>-rev27-fabrication.zip` | the same files zipped. Not in Git, like every ZIP here; `make_packages.py --zip-only` rebuilds it byte for byte from `gerbers/` (mainboard SHA-256 `4f540fa7…`, I/O `752f6585…`, see `package-record.json`) |
| `<board>/assembly/` | `<board>-bom.csv` (one row per reference: printed label, value, footprint, side, mount, notes) and `<board>-positions.csv` (kicad-cli, mm, both sides) |
| `<board>/<board>-preview-{top,bottom}.png` | gerbv renders of copper, silkscreen, outline and holes (bottom mirrored) |
| `<board>/FAB-NOTES.md` | stack-up, figures, Eagle differences, owner choices with recommendations |
| `make_packages.py` | export (kicad-cli), BOM join, ZIPs, `package-record.json` (commands, input hashes, file hashes, kicad-cli statistics) |
| `extract_board.py` | reads pads, vias, tracks, zone fills, outline and footprints with KiCad's Python (read-only) |
| `verify_packages.py` | re-imports every file and writes `verification.json` and the previews |

| | Mainboard | I/O board |
|---|---|---|
| Size | 237.49 × 180.34 mm | 213.36 × 44.45 mm |
| Layers, thickness | 2, 1.6 mm | 2, 1.6 mm |
| Holes | 1209 PTH (6 vias), 7 NPTH, no slots | 231 PTH (2 vias), no NPTH |
| Smallest track / clearance | 0.4064 / 0.254 mm | 0.381 / 0.2037 mm |
| Smallest drill / annular ring | 0.6 / 0.203 mm (vias); pads 0.8128 / 0.254 mm | 0.6 / 0.203 mm (vias); pads 0.8128 / 0.254 mm |
| Hole to hole / copper to edge | 0.984 / 0.500 mm | 1.050 / 0.500 mm |
| SMD | none | IC25 FT232BM, 32 pads, bottom |
| Parts | 417 footprints (343 top, 74 bottom; 7 mounting holes) | 82 footprints (81 top, 1 bottom) |

## Verification (`verification.json`)

`verify_packages.py` runs 35 checks per board. All pass on the mainboard. On the I/O board 34 pass, and the one advisory check reports a fill that differs slightly from a fresh refill (below).

- **Against the board files** (KiCad's Python, read-only):
  - Every copper pad is flashed at its position, with its reference, pad number, net and PCB pad size. That is 1203 pads per side on the mainboard, and 229 top and 261 bottom on the I/O board.
  - Every via, track and arc matches by ends, width and net, and the zone fill area per net is within 0.2 % of the saved fill.
  - Each mask and paste layer has one opening per pad and none for the tented vias.
  - Every PTH and NPTH hole matches by position and size.
  - Edge_Cuts is one closed contour equal to the PCB outline, and the job file states 2 layers, 1.6 mm and the PCB edge size.
- **Independent reader:** gerbv (it reports version v4.0) re-exports every non-empty Gerber and both drill files. Its output carries the same flashes, draw ends, regions (area within 0.01 %) and drill hits and sizes.
- **Same output as the Eagle comparison:** every Gerber, drill and job file has the byte size of the export that the revision-27 comparison (`validation/models-review-27/fabrication-comparison/`) checked object by object against the original Eagle 4.13 boards, with the same PCB hashes. That comparison matches every pad, track, via, drill, pour outline and silkscreen item. It records three remaining differences, which are fab-note choices: via tenting, the NPTH stop frame and the IC25 mask corners.
- **DRC of the copper as saved and plotted** (no zone refill, the board's own rules): no copper violation on either board.
- **Measured minimums:** the smallest clearance, hole clearance, hole-to-hole and copper-to-edge distances come from KiCad's DRC. The rules are raised on a temporary copy until fewer than 199 violations remain, KiCad's per-type report limit.
- **Zones:** `kicad-cli --check-zones` leaves the mainboard copper identical, so its saved fill is current. On the I/O board a refill adds about 1.9 mm² of pour in two places, near (50, 15–20) and (85, 35); the saved fill passes DRC and is not a fabrication issue (advisory).

## Regenerate

From the repository root, with KiCad 10.0.7 at `/Applications/KiCad/KiCad.app` (or `KICAD_CLI`, `KICAD_PYTHON`) and gerbv on the path (or `GERBV`):

```sh
python3 -I kicad-working/fabrication/revision-27/make_packages.py
python3 -I kicad-working/fabrication/revision-27/verify_packages.py
```

A fresh export changes only the creation dates inside the files, and with them the file and ZIP hashes in `package-record.json`. For a later revision, copy this folder to `revision-<N>` once that revision's own records exist, including its Gerber comparison, and re-run both scripts.
