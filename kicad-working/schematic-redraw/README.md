# Redrawn schematics (KiCad working revision 28)

The original Eagle schematics were one large sheet per board: the mainboard's is 570 x 728 mm, with the digital part spread out and the analog part packed tight. The KiCad import added 236 service references such as `#GND42` to them, and one `N$` label on nearly every net. This revision redraws both as sets of A3 sheets, one per block. The circuit, the board copper and every net name stay as they were.

| Board | Sheets |
|---|---|
| Mainboard | [CPU](../mainboard/p02_cpu.kicad_sch), [rotary encoders](../mainboard/p03_encoders.kicad_sch), [tact switches](../mainboard/p04_switches.kicad_sch), [LEDs](../mainboard/p05_leds.kicad_sch), [CV and VCO](../mainboard/p06_cv_vco.kicad_sch), [VCF](../mainboard/p07_vcf.kicad_sch), [VCA](../mainboard/p08_vca.kicad_sch), [envelope](../mainboard/p09_env.kicad_sch), [mixer and headphone](../mainboard/p10_mixer.kicad_sch) |
| I/O board | [power](../ioboard/p02_power.kicad_sch), [USB](../ioboard/p03_usb.kicad_sch), [MIDI, DIN sync and jacks](../ioboard/p04_midi_jacks.kicad_sch) |

The PDFs are [mainboard-schematic.pdf](mainboard-schematic.pdf) and [ioboard-schematic.pdf](ioboard-schematic.pdf). Nothing has been built or measured from these sheets.

## How the sheets were made

- **By hand, from the original layout.** Each block keeps the original's parts, order and signal flow, in its own frame. Every wire is typed in `mainboard_sheets.py` and `ioboard_sheets.py`; nothing is auto-routed. `x0x_draw.py` holds the drawing tools and symbols.
- **Symbols.** Transistors, dual transistors, pots, resistors, capacitors and diodes use new symbols in the style of the original sheet. Chips, connectors, switches and jacks keep their original symbol graphics, with line and text sizes matched. Everything is in each project's `x0x.kicad_sym`.
- **Net names are kept.** The board, the fabrication packages and the simulation use the Eagle names, such as `N$124`. A net that stays on one sheet carries its name on one pin, as a global label at 0.05 mm, because KiCad ignores "hide" on labels and a local label would add the sheet's path to the name. Each net has one such label, so a label can't join anything by itself. A net that crosses sheets has a visible label on each sheet, with its name typed by hand.
- **Values and pin names are kept** from the single-sheet schematic in `data/<board>_parts.json`, so the BOM and the simulation read the same data. Device names with nothing to say on a sheet, such as `LED5MM` or `MA03-''`, stay as the part's value but are hidden.
- **The board files changed only in their links.** KiCad finds a footprint's symbol by its path, and the path changes when a symbol moves onto a sub-sheet. `relink_board.py` rewrites those `path` lines, 410 on the mainboard and 82 on the I/O board, which is what KiCad's "Re-link footprints" does, and adds one to each of the mainboard's seven mounting holes. Copper, nets, placement and text are untouched; `pcb-relink-record.json` holds the hashes.

## Results

From the last run of `verify_redraw.py --mutation`, recorded in [docs/schematic-redraw.json](../../docs/schematic-redraw.json):

| Check | Mainboard | I/O board |
|---|---|---|
| Pins compared with the board copper | 1160 on 324 nets: none differs in group or name | 222 on 59 nets: none differs in group or name |
| Pins compared with the original Eagle schematic | 1160 on 324 nets: none differs | 222 on 59 nets: none differs |
| Pads open on the board | All open on the sheet too | All open on the sheet too |
| ERC under the project rules | 0 violations | 0 violations |
| DRC with parity | 335 violations, 1 unconnected, 127 parity. As at revision 27, except that the holes' 7 "extra footprint" warnings became 14 mismatches, on value and BOM flag | 254, 1, 45: the same as revision 27 |
| Board file against revision 27 | 410 `path` lines differ and 7 are added, nothing else | Only 82 `path` lines differ |
| Each footprint's symbol and link | 417, each with a symbol and linked to its own | 82, each with a symbol and linked to its own |
| File format and sheet instances | As KiCad 10.0.7 writes them, with pages in sheet order | The same |
| One wire left out of each sheet in turn | The comparison failed on all 9 sheets | The comparison failed on all 3 sheets |

Opened by hand in the KiCad 10.0.7 editor, once, on the installed files:

- **Loading:** both projects open with no error message and no format warning, and stay unmodified. Every sheet shows real symbols, and pages run 2 to 10 and 2 to 4.
- **ERC in the editor:** 0 violations on both, with the same four ignored tests as revision 27.
- **Net-name labels:** on the I/O board's MIDI sheet, a click on the spot of the 0.05 mm label `N$22` selects the pin under it, with no extra menu, and a click on the wire shows `N$22` as its connection name. Other labels weren't tried.
- **Update PCB from Schematic, dialog read and closed, nothing applied:** it removes nothing, and it changes no pad's net except for moving open pads to `unconnected-` nets. New since revision 27: the new sheet names, and for each mounting hole a value of `~`, a BOM flag and its sheet name. `IC1` moves to another of its own units, because KiCad's choice of unit depends on the order of items on the sheet. The rest was already there at revision 27: on the mainboard, 70 value changes, 43 pads on `unconnected-` nets and 23 jumper pad groups; on the I/O board, 7 value changes, 38 pads on `unconnected-` nets and a warning about `IC24` pad 3.

An earlier state of this revision, commit `ad65ff0`, opened with an error message. Its sheet instances named a top-level sheet other than the project's, its format numbers were older than KiCad writes, and `relink_board.py` gave every footprint on a sheet the same path. Only the editor showed these. `kicad-cli` netlists, ERC and DRC passed, and parity matches by reference. `verify_redraw.py` now checks all three.

Also checked, once, on the installed files:

- **Copper:** track segments and vias are identical: 2649 and 6 on the mainboard, 418 and 2 on the I/O board. All 9 Gerbers of each board re-export identically apart from their creation dates, so the revision-27 fabrication packages still apply.
- **BOM:** `kicad-cli sch export bom` gives the same value and DNP for every part as the revision-27 BOM files.
- **Simulation:** `extract_vcf.py --check` still matches, and `verify_report.py` still passes 45 of 45.
- **Overlaps:** the Amber `lint_sch.py` tool, run with the 0.05 mm labels left out, reports text inside a symbol's own outline (for example, the part name inside a dual transistor's capsule) and wires inside an imported symbol's outline (IC15's link between pins 6 and 7, S1's and S2's mounting pins). I looked at those on the renders and none touches anything. It is not a zero-finding result.
- **Rendering:** every sheet was rendered and looked at, with zoomed crops of the switch and LED sheets.

The net comparison caught real mistakes while drawing: swapped pads on R83, R84, R88, R89, C103, R131 and R138, and a wire that stopped one column short at Q31. So it can fail, and did.

## Where the sheets differ from the original

No net differs. These are differences of presentation:

| Sheet | Original | Here |
|---|---|---|
| CPU | XTL1 drawn as a transistor, using its `2SC2021R` device | Drawn as a three-pin resonator, with the value kept and a note on the sheet |
| VCF | R124, R125 and R126 are in the expanded BOM's VCF section | On the VCA sheet, where they sit on the original and connect |
| CV and VCO | R100A0 and R100B0 each print `THERMISTOR-7,5` | The value is hidden, and one note names both |
| Envelope | VR6's section A drawn with the other pots | Marked as unused, with all its pins on ground as on the board |
| All | Pots at the edge of the sheet | Beside the circuit they control, with their panel names kept |
| All | No PWR_FLAG | Flags where a rail arrives through a connector, a diode or a resistor, for ERC |
| CPU | Mounting holes `U$2`, `U$23`, `U$24`, `U$25`, `U$27`, `U$28` and `U$29` aren't on the sheet; they are only on the board | A frame with a pin-less symbol for each, out of the BOM, so that Update PCB doesn't delete them |

## Limits

- **"Update PCB from Schematic" has been read but never applied.** At revision 27, with no symbols for them, it would have deleted the seven mounting holes.
- **Parts on the same two nets look identical to the net checks.** R74 and R75, for example, could trade places unnoticed. Their names rest on the original sheet.
- A net with one pin on the sheets can't show a wrong group, only a wrong name.
- The Eagle nets in `data/<board>_eagle_nets.json` were read from `original-eagle/` by the parser used for the first import, not transcribed by a person.

## Rerun

Close the projects in KiCad first: `install.py` overwrites the sheets.

```sh
cd kicad-working/schematic-redraw
python3 install.py mainboard
python3 install.py ioboard
python3 verify_redraw.py --mutation
```

`run_board.sh <board> <folder>` builds into a scratch folder instead, renders a PDF and compares the nets. `extract_parts.py` regenerates `data/<board>_parts.json` from a board and a netlist of a schematic with the same values and pin names.
