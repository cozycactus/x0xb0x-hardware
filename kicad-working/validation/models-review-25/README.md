# KiCad working revision 25 — fabrication comparison and switch strips

Revision 25 compares both boards' fabrication outputs with the original Eagle 4.13 boards and settles the three connection gaps recorded since revision 11. The full report, with every difference and its location, is in `fabrication-comparison/README.md`.

The comparison regenerates Gerbers and Excellon drills with KiCad 10.0.7 and matches them object by object against the Eagle geometry evaluated with Eagle 4.13 CAM rules. That geometry comes from the conversion's staging XML, which `fabrication-comparison/source_crosscheck.py` confirms against an independent read of `original-eagle/`. Drills, all copper tracks and arcs, all vias and every other pad, the pour outlines, paste and all non-text silkscreen are identical. Recorded differences are left unchanged:

- the 27 SIP9 pads of IC14/IC15A/IC15B are 1.400 × 2.032 mm instead of Eagle's 1.408 × 2.816 mm;
- 445 name labels sit at library default positions instead of the smashed positions (the production I/O photograph shows the smashed ones), and 11 references carry a trailing 0;
- KiCad tents the vias, opens the seven NPTH holes without Eagle's stop frame and rounds the IC25 mask corners.

All three gaps are the only airwires stored in the original boards:

- **+5V (S22 pad 1).** The two +5V copper islands are joined inside the B3F-40XX switches S19 and S22, whose pins 1–2 form one strip in the original symbol. This is the only path from the supply entry (J3.3/J3.4) to the 74HC595 LED drivers. `install_switch_jumper_groups.py` declares the strips as KiCad jumper pad groups on the 23 B3F-40XX placements and the library footprint; DRC now finds +5V connected.
- **GND (mainboard IC9 pad 8 and the I/O MIXOUT sleeve).** These are the original's drawn ground splits (analog/digital pours on the mainboard, a separate jack-ground pour on the I/O board). The J3–J7 wiring joins the four islands into one loop-free ground, so the copper is unchanged.

`installation-audit.json` shows that only the 24 inserted nodes changed (byte equality after removing them); copper, pads, drills, nets, zones, placement and models are unchanged and the I/O project is untouched. Fresh KiCad 10.0.7 ERC reports 0 errors/0 warnings on both boards; DRC violations, parity and ignored checks equal revision 24; the remaining unconnected items are the two GND splits. The 214 DIN function checks replay unchanged (`verify_current_functions.py`), and all local libraries and models resolve. See `../working-validation-summary-revision-25.json`.

Run from the repository root, in order: `install_switch_jumper_groups.py` (already applied), `run_native_checks.py`, `fabrication-comparison/run_comparison.py`, `verify_current_functions.py > current-function-verification.json`, `summarize_working_validation.py`. The comparison needs KiCad 10.0.7 and the conversion workspace (`../kicad-import/validation/`); its input hashes are recorded in each report.
