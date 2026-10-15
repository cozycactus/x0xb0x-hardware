# Working revision 13 — drawing-derived terminals

Twelve component models had bodies but no solder terminals, so 25 placed references showed nothing in their drilled holes. This revision adds terminals from each manufacturer drawing. Every fitted model now has a lead in every drilled hole, except the four Grayhill bracket holes: the drawing does not define those legs.

| Model | References | Drawing | Terminals |
| --- | --- | --- | --- |
| REAN NYS216 | HEADPHONE0, MIXIN0, MIXOUT0 | NYS216 3102 ST 22 01 rev C | 6 |
| Same Sky SDS-50J | DIN1–DIN4 | SDS-J page 3 | 7 |
| CUI MJ-3536N | CV0, GATE0 | MJ-3536N rev 1.02 | 3 |
| CUI PJ-202AH | POWER0 | PJ-202AH (2015) | 3 |
| USB-B (FCI 61729 outline) | USB0 | FCI/Amphenol 61729 | 6 |
| MC78M05, bent back | IC20 | onsemi TO-220 case 221AB | 3 |
| Micro-Ohm LPTC12T21001 | R100A0, R100B0 | none recovered; all assumed | 2 |
| CTS 290 | S2 | MC-290V rev A | 7 |
| Alpha RV112 dual | VR4, VR6 | RV112BCF-40 | 8 |
| Panasonic EVUF2L | VR2, VR3, VR5, VR7, VR8 | EVUF2L No. 8 | 5 |
| NKK B12AB | S1 | Series B, straight PC with bracket | 7 |
| Grayhill 25L | S3, S4 | Series 25L | 5 |

Ten of the drawings are the source files already retained in this repository; `terminal_spec.py` names each path. The USB drawing was read from an RS-hosted copy of the FCI 61729 drawing, which is not retained here. Amphenol CS publishes that drawing as `61729.pdf`. The original BOM's Kobiconn 154-2442-E drawing could not be retrieved, so the outline follows the footprint's PN61729 part. No mechanical data was found for the LPTC thermistor.

`terminal-quality/terminal_spec.py` holds every terminal. Positions come from the drawing dimensions in each model frame and were never moved to the PCB pads. Each section size is labelled *dimensioned*, *drawn* (measured on the drawing) or *assumed*. Thicknesses, bends and some widths are assumptions.

`terminal-quality/build_terminals.py` re-exports every previous body solid unchanged and in order, with its original colour, and appends the terminals in one tin colour. Its 197 checks confirm, for every model:

- identical vertices and topology for all original solids;
- the specified tip depth for every terminal;
- analytic volumes for the formed TO-220 and thermistor leads, so a boolean that drops a segment cannot pass;
- the colours.

The seven assembly models keep their root and named part products, and their terminals are one added `DrawingDerivedTerminals` part.

`install_terminal_models.py` changes only 25 embedded PCB model paths and the 12 matching footprint-cache model paths. It verifies that every non-model S-expression node and every model transform is identical. Original Eagle files, schematics, copper, nets, pads, drills, footprint poses and project rules are preserved. The older STEP files remain.

## Native checks

`export_native_boards.py` exports both PCBs with `kicad-cli` and records every pad with KiCad's own Python. `audit_native_terminals.py` then works on the native GLB in the board frame:

- It cuts every model at mid-board depth and requires geometry inside every drilled hole of all 491 fitted models.
- For the 25 updated references, it measures each terminal section at both board faces and at mid-depth, against the real drill.
- Each section point belongs to the pad with the nearest drill wall. Neighbouring leads at 2.0–2.5 mm pitch therefore do not count against a pad.

All leads protrude 1.2–4.7 mm through the far face, and no geometry crosses the board away from a hole.

The audit records 19 nominal interferences where a drawing and the footprint disagree. Neither source was changed to make them fit.

| Model | Pads | Worst margin | Cause |
| --- | --- | --- | --- |
| NYS216 | all 6 | −0.28 mm | drawing rows 0.35 mm from the footprint rows |
| SDS-50J | 1–5 | −0.10 mm | 1.3 mm drills; pin 1 about 0.12 mm off |
| USB | M2, P$2 | −0.24 mm | 2.4 mm shell forks in 2.2 mm holes |
| PJ-202AH | P$2, P$3 | −0.13 mm | 3.0 mm blade in a 2.8 mm hole |
| Alpha RV112 | M1, M2 | −0.52 mm | bracket tabs at ±6.5 mm, holes at ±5.5 mm |
| Panasonic EVU | M1, M2 | −0.34 mm | tabs at ±5.30 mm, holes at ±4.572 mm |

MJ-3536N, MC78M05, LPTC, CTS, NKK and Grayhill fit every hole. Grayhill MT bracket legs and SDS-50J locating pegs remain omitted. The pegs have no footprint holes.

## Electrical and dependency evidence

`run_native_checks.py` runs fresh KiCad 10.0.7 ERC and DRC for both boards, on temporary copies and with the revision-11 command lines.

- ERC reports zero errors and warnings under the retained rules.
- Both boards' DRC violations, schematic-parity findings and ignored checks exactly equal the previous fresh reports.
- The same three pads remain unconnected. For S22 pad 1 (+5V), KiCad now names a different, equivalent +5V track fragment as the other end; copper changed only in model paths.

`verify_current_functions.py` replays the 214 original-source MIDI function checks against the current I/O board. `carry_function_evidence.py` carried the revision-12 evidence forward with only that board's hash updated, after the installation audit showed the file changed in model nodes alone. The revision-12 replay is now historical at its previous PCB hash.

`local-dependencies.json` confirms that all 491 placed models resolve inside the checkout. `summarize_working_validation.py` writes the revision-13 validation summary, which records 273 core files. The GLB exports themselves are not tracked; `native-export-record.json` pins their hashes.

These are nominal model checks. They do not qualify physical assembly or fabrication readiness.
