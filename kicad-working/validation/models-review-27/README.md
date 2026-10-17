# KiCad working revision 27 — mainboard pour fill and I/O outline

The first fabrication export (from revision 26) was re-imported and checked against the board files. It found two defects that a fab would have built. Revision 27 corrects them. It changes no pad, track, via, drill, net, zone outline, footprint pose, model or schematic.

**Mainboard pour fill (the two F.Cu GND zones).** Revision 26 lengthened the 27 SIP9 pads of IC14, IC15A and IC15B but kept the saved fill, which still cleared the shorter pads. As saved and plotted, the analog pour touched 23 of them. KiCad's DRC of the saved copper found 23 clearance violations at 0.000 mm (for example IC14 pad 1, net N$9) and 23 solder-mask bridges; `installation-audit.json` lists them. The revision-26 DRC passed because `run_native_checks.py` refilled the zones before checking, and the Gerber comparison checks pour outlines, not fills. `install_zone_fill_and_datum_layer.py` refills a temporary copy with KiCad's zone filler (`refill_zones.py`) and copies only the `filled_polygon` nodes of the two zones into the working file, matched by zone uuid. Every other byte of each zone, and of the board, is asserted unchanged. A second refill of the installed board reproduces the same nodes. The analog pour shrinks by 37.4 mm² around the SIP9 pads; the digital pour changes only in arc approximation.

**I/O outline.** Four 0.0254 mm lines on the original Eagle Dimension layer draw the rear-plate section: a 222.25 × 1.651 mm rectangle from (−4.064, 0.508) to (218.186, 2.159) in KiCad coordinates, 0.508 mm behind the rear edge. Blender revisions 14–15 seat the rear plate on this datum. On Edge.Cuts the lines formed a second closed board outline, and the Gerber job file reported 222.28 × 46.65 mm. The revision-25 comparison had matched them to the Eagle Dimension layer, but did not flag them as a contour. Only their layer node changes, to Dwgs.User, beside the detached datum line the importer already put there. Edge.Cuts now holds the single 213.36 × 44.45 mm outline.

Results:

- **Fresh KiCad 10.0.7 ERC/DRC:** ERC 0/0 on both boards. DRC now checks the copper as saved: the revision-11 command without `--refill-zones`. Every non-silkscreen DRC violation is identical item by item to revision 26 (whose DRC refilled the zones): 48 dangling-track warnings on the mainboard, 7 on the I/O board. Schematic parity, ignored checks and the two GND splits are unchanged. Mainboard silkscreen warnings stay at 335. I/O silkscreen-to-edge warnings drop from 46 to 31, with the datum outline gone.
- **Gerber comparison** (`fabrication-comparison/`, revision-26 scripts unchanged): every pad, track, via, drill and silkscreen item still matches the original Eagle CAM output. The I/O Edge_Cuts layer now lists the four datum lines as missing in KiCad, by design, beside the y −2.921 line, which was already on Dwgs.User. Via tenting, the NPTH stop frame and the IC25 mask corners remain as recorded.
- The DIN function proof replays unchanged (214 checks), with the I/O PCB hash carried forward (`update_function_evidence.py`). Local libraries and models resolve as in revision 26. The Blender scene is unchanged: it embeds its board meshes, and no model or placement moved. Blender revision 10 had already split the datum strip out of the I/O board's native KiCad mesh into a separate "Historical detached Dimension outline" reference collection, so the displayed board is the 213.36 × 44.45 mm outline that revision 27 now gives KiCad.
- The order packages are in `../../fabrication/revision-27/`: every file is re-imported against the board files and re-exported by gerbv, with no blocking failure.

Run from the repository root, in order:
1. `install_zone_fill_and_datum_layer.py` (already applied)
2. `run_native_checks.py`
3. `fabrication-comparison/run_comparison.py`
4. `update_function_evidence.py`
5. `verify_current_functions.py > current-function-verification.json`
6. `python3 scripts/verify_kicad_dependencies.py > local-dependencies.json`
7. `summarize_working_validation.py`
8. `write_fabrication_record.py`
9. `../../fabrication/revision-27/make_packages.py`
10. `../../fabrication/revision-27/verify_packages.py`

The comparison needs the conversion's staging XML (`../kicad-import/validation/repaired-eagle-xml`, or `X0X_EAGLE_XML`); the package verifier needs gerbv.
