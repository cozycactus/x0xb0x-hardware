# x0xb0x I/O board — fabrication notes (KiCad working revision 30)

**Status: ready to order**, once you have made the choices below. Upload `x0xb0x-ioboard-rev30-fabrication.zip` (or the files in `gerbers/`). Revision 27 moved the rear-plate datum off Edge.Cuts. That datum is four lines on the original Eagle Dimension layer, a 222.25 × 1.651 mm rectangle 0.508 mm behind the rear edge. On Edge.Cuts it formed a second closed board outline. It now sits on Dwgs.User beside the detached datum line, and the Blender rear-plate seating still reads it there. `ioboard-Edge_Cuts.gbr` holds the single 213.36 × 44.45 mm outline.

## Board

| Item | Value | Source |
|---|---|---|
| Size | 213.36 × 44.45 mm rectangle (job file: 213.41 × 44.50 mm, including the 0.05 mm outline stroke) | Edge.Cuts, one closed contour |
| Layers | 2 copper (F.Cu, B.Cu) | board file, job file |
| Thickness | 1.6 mm, FR-4 assumed | board file `(general (thickness 1.6))`, job file. There is no stack-up section, so material and copper weight are not recorded |
| Copper | F.Cu: tracks and three GND pours as in the original, one of them the separate MIXOUT/MIXIN jack island; B.Cu: tracks only | |
| Plated holes | 231 (229 pads + 2 vias), 12 sizes 0.600–3.200 mm, no slots | `ioboard-PTH.drl` |
| Non-plated holes | none (`ioboard-NPTH.drl` is empty) | |
| Smallest track | 0.381 mm (75 tracks) | PCB |
| Smallest clearance | 0.2037 mm (N$17 track to the GND pour; Eagle's 8 mil rule) | KiCad DRC, rules raised step by step |
| Smallest drill | 0.600 mm (vias); smallest pad drill 0.8128 mm; largest 3.200 mm | PCB |
| Smallest annular ring | pads 0.254 mm (USB0 pin 1: 1.458 mm pad on 0.95 mm drill); vias 0.203 mm | PCB |
| Hole to copper / hole to hole / copper to edge | 0.407 / 1.050 / 0.500 mm | KiCad DRC |
| SMD | IC25 FT232BM, LQFP-32, 0.8 mm pitch, bottom side: 32 pads | PCB |
| Solder mask | top 229 openings, bottom 261 (229 + 32 SMD); vias tented | mask Gerbers |
| Paste | bottom only, 32 apertures for IC25; `ioboard-F_Paste.gbr` is empty | paste Gerbers |
| Silkscreen | Top 3519 strokes (white on green: production photograph `validation/models-review-10/heatsink-fit-research/sources/ioboard_done.jpg`), bottom 47. Most strokes are 0.127 mm, 281 are 0.1016 mm. 80 top strokes, the KK1 heatsink outline, extend past the board's top edge and will be clipped | silk Gerbers |
| Parts | 82 footprints: 81 top, 1 bottom (IC25); KK1 (heatsink) has no pads | PCB |

## Package (`gerbers/`, zipped as `x0xb0x-ioboard-rev30-fabrication.zip`)

The set matches the mainboard's:
- **Gerbers:** nine Gerber X2 layers (`.gbr`).
- **Job file:** `ioboard-job.gbrjob`.
- **Drills:** `ioboard-PTH.drl` and `ioboard-NPTH.drl`.
- **Drill documentation:** drill maps and the drill report.

Previews: `ioboard-preview-top.png` and `-bottom.png` (mirrored).

Not included: an IPC-D-356 netlist. The MIXOUT/MIXIN jack ground is a separate copper island joined through J7 and the analog mainboard ground, so a KiCad-netlist comparison would report an open on GND.

## Differences from the original Eagle CAM output (revisions 25–27)

- **IC25 mask:** the 32 SMD openings have the same 0.603 × 1.803 mm size but 0.1016 mm corner radii; Eagle's were square. No effect on soldering.
- **Vias:** the 2 vias are tented here; Eagle 4.13 probably exposed them.
- **Outline:** three board-edge lines had zero width in Eagle (0.05 mm in KiCad). The rear-plate datum (the four lines above, plus the line at y −2.921) is on Dwgs.User, so it is not plotted.

The saved pour fill differs from a fresh KiCad refill by about 1.9 mm² in two places. It passes DRC as saved and was left unchanged.

## Choices for the owner

1. **Thickness 1.6 mm.** *Recommended*: the board and job files state it, and it is the standard thickness.
2. **Copper 1 oz (35 µm).** *Recommended*: the weight is not recorded and 1 oz is standard; the 2.032 mm supply tracks need nothing heavier.
3. **Surface finish.** Options:
   - lead-free HASL (*recommended*: matches the photographed original; the 0.8 mm-pitch FT232BM hand-solders well on HASL);
   - ENIG (flatter pads for IC25, costs more).

   Use the same finish on both boards.
4. **Mask and silkscreen colours.** Green and white (*recommended*, as in the production photograph).
5. **Via tenting.** Order as exported, tented (*recommended*; 2 vias of 0.6 mm).
6. **Thin and off-board silkscreen.** Accept the DFM warnings for the 0.127 mm strokes and the KK1 outline clipped at the board edge (*recommended*).
7. **Electrical test.** Ask for the fab's flying-probe test against its own Gerber-extracted netlist; don't send a KiCad netlist.
8. **IC25 FT232BM assembly.** Options:
   - hand-solder it as the kit builder (*recommended*: it is a single 0.8 mm-pitch part; paste and position files are included if you choose otherwise);
   - have the fab place only IC25. That needs `ioboard-B_Paste.gbr` for a stencil, the BOM and position files, and a second, assembly order.
9. **Panelisation.** Not needed: order the board as its own design, separately from the mainboard.

Assembly files:
- `assembly/ioboard-bom.csv`: one row per reference. The silkscreen prints CV, GATE, POWER, USB, MIXOUT, MIXIN and HEADPHONE for the KiCad references ending in 0.
- `assembly/ioboard-positions.csv`: mm, Gerber orientation.
