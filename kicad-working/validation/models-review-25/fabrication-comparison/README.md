# Fabrication outputs compared with the original Eagle boards

`run_comparison.py` exports Gerbers and Excellon drills for both boards with KiCad 10.0.7 (`kicad-cli`, board plot settings, into a temporary folder) and compares them object by object with the original Eagle 4.13 boards. Results: `gerber-comparison.json` (every difference with its location), `connection-gap-review.json` and `source-decode-crosscheck.json`.

**Eagle side.** No Eagle installation or original Gerbers exist (the download page publishes only the `.brd`/`.sch` files and two schematic snapshots). `eagle_model.py` reads the staging XML that the conversion decoded from the binary files (`../kicad-import/validation/repaired-eagle-xml/`, outside this repository; hashes in each report) and applies Eagle 4.13 CAM rules: pad restring (25 % of drill, 0.254–0.508 mm), long-pad elongation 100 % of the restrung width, via restring (0.2032–0.508 mm), 0.1016 mm stop frame, and element transforms (rotate, then mirror). `source_crosscheck.py` reads `original-eagle/*.brd` independently with `kicad-import/validation/inspect_eagle_source.py` and confirms that the XML carries exactly the binary's wire records, vias, pads, SMDs, holes and element placements. Silkscreen follows Eagle's standard CAM job: tPlace + tNames (top), bPlace + bNames (bottom).

Coordinates below are Gerber/Eagle millimetres (y up); KiCad's editor shows the same x and −y.

## Result per layer

| Layer | Mainboard | I/O board |
|---|---|---|
| Drills (PTH/NPTH) | 1209/7 holes, all matched; sizes equal at Excellon 0.001 mm; max position error 0.0006 mm | 231/0, all matched; max error 0.0004 mm |
| Copper tracks/arcs | F 484/484, B 2768/2768 identical (ends, width, arc centre) | F 48/48, B 458/458 identical |
| Pads and vias | 1182/1209 identical; **27 SIP9 pads differ** (below) | 231 top, 263 bottom, all identical |
| Copper pours | 2 GND polygons → 2 zones; outlines within 0.090 mm (half the 0.127 mm polygon width); same connectivity | 3 GND polygons → 3 zones; within 0.052 mm; same connectivity |
| Solder mask | 1176/1210 identical; 27 SIP9 openings follow their pads; 7 NPTH openings smaller | 229 top identical; 32 SMD openings same size, rounded corners |
| Paste | none on either side (THT only) | 32 bottom SMD apertures identical |
| Silkscreen geometry | top 1781 lines/arcs, 227 circles, 70 filled shapes; bottom 1342, 131, 92: all identical | top 825, 42, 34; bottom 4, 1, 0: all identical |
| Silkscreen text | every remaining stroke is KiCad text; 372 name labels at library default positions; 4 renamed | 73 name labels at default positions; 7 renamed |
| Outline | same rectangle; Eagle's 0.23 mm stubs at (0, 0) dropped | same rectangle; detached Dimension strip excluded |

## Differences and their locations

1. **SIP9 pads (copper and mask), mainboard IC14, IC15A, IC15B — 27 pads.** The library pads are "long" with a 1.016 mm diameter and 0.9 mm drill. Eagle 4.13 first restrings the diameter to 1.408 mm, then elongates it 100 % → 1.408 × 2.816 mm. The KiCad importer elongated the library value instead → 1.400 × 2.032 mm (mask 1.603 × 2.235 instead of 1.611 × 3.019). Rows: IC14 at y 148.158, x 3.353–23.673 (pitch 2.54); IC15A at x 39.878, y 107.442–127.762; IC15B at x 34.646, y 107.493–127.813. Drills and positions are identical; the annular ring across the pad is the same. KiCad's pads are 0.78 mm shorter.
2. **NPTH stop-mask openings, mainboard U$2, U$23–U$25, U$27–U$29.** These are the seven 3.302 mm mounting holes at (228.041, 21.285), (228.041, 167.386), (9.449, 167.386), (9.449, 21.285), (118.745, 21.285), (73.025, 167.386), (164.465, 167.386). Eagle adds the stop frame (3.505 mm opening); KiCad opens exactly 3.302 mm.
3. **SMD mask corners, I/O IC25 (FT232BM, 32 pads, bottom).** The openings have the same 0.603 × 1.803 mm size but 0.1016 mm corner radii; Eagle's are square.
4. **Vias (mainboard 6, I/O 2).** All 0.6 mm drill / 1.006 mm copper, identical. KiCad tents them. Eagle 4.13 exposes vias whose drill exceeds the design-rule "Limit", which was not decoded from the binary (Eagle's default exposes all vias). Mainboard: (199.898, 175.895), (75.692, 74.422), (59.436, 3.81), (83.058, 3.81), (105.156, 3.81), (73.076, 72.822). I/O: (80.01, 39.37), (78.232, 41.148).
5. **Name labels.** The binary stores smashed name records for 381 mainboard and 80 I/O parts. KiCad placed every reference at the library `>NAME` position instead. The result is 445 moved labels (322 by more than 2 mm, up to 29 mm at S4; listed per part in `gerber-comparison.json`). The photographed production I/O board (`validation/models-review-10/heatsink-fit-research/sources/ioboard_done.jpg`) shows the smashed positions, e.g. J3 above header pins 6–7 and R164 vertical at (38.1, 5.3). KiCad would put them left of pin 1 and at y 10.3. The same photo prints some designators that differ from the board file (for example "R23" where the file's R28 label sits), consistent with the download page's "out of sync" note.
6. **Renamed references.** KiCad requires a trailing number, so the silkscreen prints IC15A0, IC15B0, R100A0, R100B0 (mainboard) and CV0, GATE0, POWER0, USB0, MIXOUT0, MIXIN0, HEADPHONE0 (I/O) instead of the Eagle names.
7. **Outline.** Mainboard Eagle bottom edge runs to x −0.0254 with spurs from (−0.2286, 0) and up to (−0.0254, 0.1778); KiCad closes the rectangle at (0, 0) (`kicad-import` outline repair). I/O Eagle Dimension lines have zero width (KiCad 0.05 mm), and the detached 0.025 mm strip from (−3.937, −2.921) to (220.345, −2.921), the rear-plate datum, is on Dwgs.User, not Edge.Cuts. Neither changes the board shape; the strip would otherwise be routed as a second contour.
8. **Pour settings.** Outlines and connectivity agree. KiCad's thermal gap/spoke (0.177 mm mainboard, 0.1135 mm I/O) and minimum width come from the importer; Eagle 4.13 recomputes its fill at CAM time from isolate, width and the design rules, so the fill edges themselves were not regenerated for comparison.

Text glyphs differ by font (KiCad stroke font vs Eagle vector font) and were compared as strings and anchors, not as strokes.

## The three recorded connection gaps

All three are the only airwires (layer 19, "Unrouted") stored in the original boards. Eagle's ratsnest included the pours: track-only analysis gives 50 mainboard and 8 I/O GND islands, yet one GND airwire per board remained. KiCad reproduces them exactly.

- **Mainboard S22 pad 1 [+5V].** In the Eagle copper, +5V is two islands. The supply entry from the I/O board (J3.3, J3.4) feeds the ATmega162 side. All five 74HC595 LED drivers' VCC pins sit on the other island. Only S19 and S22 have pad 1 on one island and pad 2 on the other. The original switch symbol draws pins 1–2 and 3–4 as joined strips; on the B3F-40XX these pads are 12.5 mm apart on one strip. The switches therefore carry +5V to the LED drivers, which the shipped units could not have worked without. Fix in revision 25: KiCad jumper pad groups ("1" "2") ("3" "4") on all 23 B3F-40XX placements and the library footprint, with no copper change. DRC now finds +5V connected.
- **Mainboard IC9 pad 8 [GND] vs the B.Cu GND track.** The mainboard ground is two pours separated by a 1.14 mm drawn moat (y 107.95–109.09 at IC9). The analog pour (prio 5, 253 items, IC9.8, J4–J7 pin 2) is on one side, the digital pour (prio 6, 504 items, ATmega162, shift registers, J3.7/J3.8) on the other. Eagle's airwire is just the nearest point between the two.
- **I/O MIXOUT sleeve [GND] (F.Cu arc) vs the B.Cu GND track.** A separate top pour joins the MIXOUT/MIXIN sleeves, MIXIN's normalling contact and J7 pin 2, separated from the main pour by a moat. The bottom track has an overlapping 4.47 mm stub ending under the sleeve pad at (99.54, 1.143), where a link was removed. The production photo shows the same separate jack pour.

The original jumper table (J3 12-wire, J4–J7 3-wire, pin for pin; GND on J3.7/8 and pin 2 of J4–J7) joins these four ground islands into one tree: digital ↔ I/O main via J3, analog ↔ I/O main via J4–J6, jack island ↔ analog via J7. That is one connected ground with no loop between islands (`connection-gap-review.json`). Routing either GND airwire would add a loop through the wiring. Neither needs a fix, and none was made.

## Verdict

Drills, all copper tracks and arcs, all vias and every other pad, the pour outlines, paste and all non-text silkscreen reproduce the original Eagle board. Electrical connectivity, including the original ground split, is the same. Nothing in the comparison blocks ordering. Differences that would bring the KiCad output closer to the original Eagle CAM output, all awaiting the owner's decision: the 27 SIP9 pad lengths (copper), the 445 name-label positions and 11 renamed labels (silkscreen), and the via tenting and NPTH mask frame (fabrication notes).
