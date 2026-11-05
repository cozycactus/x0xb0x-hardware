# KiCad working revision 30 — two more SMD sites on the mainboard

Revision 30 adds two SC-59 chips to the mainboard, Q128 and Q139, next to the JFETs Q28 and Q39, on top of revision 29's four SOT-363 chips. The reasons, the changes and the limits are in [`../../smd-sites/README.md`](../../smd-sites/README.md).

Results:

- **Fresh KiCad 10.0.7 ERC/DRC** (`run_native_checks.py`, `*-erc.json`, `*-drc.json`): ERC 0/0 on both boards. DRC checks the copper as saved. It finds no copper violation, one known unconnected ground split on each board, and schematic parity of 127 on the mainboard and 45 on the I/O board, as at revision 29.
- **Comparison with the original Eagle boards** (`fabrication-comparison/`, the revision-26 scripts unchanged). On the mainboard all 1209 plated holes, all 1209 pads on each side and all 484 F.Cu track draws still match; 2767 of 2768 B.Cu draws match, and the other is the track split at revision 29. Beyond what it listed at revision 27 (mounting-hole mask size, outline details), the differences it lists are the additions: 7 drills, 30 SMD pads and their mask and paste openings, 7 vias, and 74 F.Cu and 18 B.Cu draws, two of those B.Cu draws being the pieces of the split track. Revision 30's share of that is 6 pads and 9 F.Cu draws. The I/O board's result is identical to revision 27's.
- **Fabrication packages** in [`../../fabrication/revision-30/`](../../fabrication/revision-30/README.md): every file is re-imported against the board files and re-exported by gerbv, with no blocking failure. All 35 checks pass on the mainboard. The I/O board keeps its one advisory: its saved pour differs from a fresh refill, as at revision 27.

Nothing was built or measured.

Run from the repository root, in order:
1. `python3 -I kicad-working/validation/models-review-30/run_native_checks.py`
2. `python3 -I kicad-working/validation/models-review-30/fabrication-comparison/run_comparison.py`
3. `python3 -I kicad-working/fabrication/revision-30/make_packages.py`
4. `python3 -I kicad-working/fabrication/revision-30/verify_packages.py`

The comparison needs the conversion's staging XML (`../kicad-import/validation/repaired-eagle-xml`, or `X0X_EAGLE_XML`); the package verifier needs gerbv.
