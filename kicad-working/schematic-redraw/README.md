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
- **The board files changed only in their links.** KiCad finds a footprint's symbol by its path, and the path changes when a symbol moves onto a sub-sheet. `relink_board.py` rewrites those `path` lines, 410 on the mainboard and 82 on the I/O board, which is what KiCad's "Re-link footprints" does. Copper, nets, placement and text are untouched; `pcb-relink-record.json` holds the hashes.

## Results

From the last run of `verify_redraw.py --mutation`, recorded in [docs/schematic-redraw.json](../../docs/schematic-redraw.json):

| Check | Mainboard | I/O board |
|---|---|---|
| Pins compared with the board copper | 1160 on 324 nets: none differs in group or name | 222 on 59 nets: none differs in group or name |
| Pins compared with the original Eagle schematic | 1160 on 324 nets: none differs | 222 on 59 nets: none differs |
| Pads open on the board | All open on the sheet too | All open on the sheet too |
| ERC under the project rules | 0 violations | 0 violations |
| DRC with parity | 335 violations, 1 unconnected, 120 parity: the same as revision 27 | 254, 1, 45: the same as revision 27 |
| Board file against revision 27 | Only 410 `path` lines differ | Only 82 `path` lines differ |
| One wire left out of each sheet in turn | The comparison failed on all 9 sheets | The comparison failed on all 3 sheets |

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

## Limits

- The sheets were generated and checked with `kicad-cli` 10.0.7. They have not been opened in the KiCad schematic editor, so how the editor shows or handles the 0.05 mm labels is not checked.
- **Parts on the same two nets look identical to the net checks.** R74 and R75, for example, could trade places unnoticed. Their names rest on the original sheet.
- A net with one pin on the sheets can't show a wrong group, only a wrong name.
- The Eagle nets in `data/<board>_eagle_nets.json` were read from `original-eagle/` by the parser used for the first import, not transcribed by a person.
- A later "Update PCB from Schematic" must keep the board's nets: the schematic names match them, but this revision hasn't run that command.

## Rerun

Close the projects in KiCad first: `install.py` overwrites the sheets.

```sh
cd kicad-working/schematic-redraw
python3 install.py mainboard
python3 install.py ioboard
python3 verify_redraw.py --mutation
```

`run_board.sh <board> <folder>` builds into a scratch folder instead, renders a PDF and compares the nets. `extract_parts.py` regenerates `data/<board>_parts.json` from a board and a netlist of a schematic with the same values and pin names.
