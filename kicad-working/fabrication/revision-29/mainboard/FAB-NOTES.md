# x0xb0x mainboard — fabrication notes (KiCad working revision 29)

**Status: ready to order**, once you have made the choices below. Upload `x0xb0x-mainboard-rev29-fabrication.zip` (or the files in `gerbers/`). Revision 27 refilled the F.Cu ground pours, so that they clear the SIP9 pads that revision 26 lengthened. As revision 26 saved them, the pours touched 23 of those pads. The copper as plotted now passes KiCad's DRC without a refill.

## Board

| Item | Value | Source |
|---|---|---|
| Size | 237.49 × 180.34 mm rectangle (job file: 237.744 × 180.594 mm, including the 0.127 mm outline stroke) | Edge.Cuts, one closed contour |
| Layers | 2 copper (F.Cu, B.Cu) | board file, job file |
| Thickness | 1.6 mm, FR-4 assumed | board file `(general (thickness 1.6))`, job file. The board has no stack-up section and the decoded Eagle 4.13 rules hold no layer setup, so material and copper weight are not recorded |
| Copper | F.Cu: tracks and two GND pours (analog and digital, split by the original 1.14 mm moat); B.Cu: tracks only | |
| Plated holes | 1216 (1203 pads + 13 vias), 11 sizes 0.390–2.800 mm, no slots | `mainboard-PTH.drl`, drill report |
| Non-plated holes | 7 × 3.302 mm mounting holes | `mainboard-NPTH.drl` |
| Smallest track | 0.25 mm (81 segments at the four SOT-363 chips); otherwise 0.4064 mm (3 tracks), and most are 0.508 and 1.016 mm | PCB |
| Smallest clearance | 0.254 mm (R77 pad 2 to a B.Cu track; Eagle's 10 mil rule) | KiCad DRC, rules raised step by step |
| Smallest drill | 0.390 mm (7 new vias), 0.600 mm (6 original vias); smallest pad drill 0.8128 mm; largest 3.302 mm | PCB |
| Smallest annular ring | pads 0.254 mm (SIP9 short side, 1.408 mm pad on 0.9 mm drill); vias 0.203 mm (1.006 mm on 0.6 mm) | PCB |
| Hole to copper / hole to hole / copper to edge | 0.458 / 0.881 / 0.500 mm. The hole-to-hole figure is a new via beside Q12's pad 3; it was 0.984 mm without the chips | KiCad DRC |
| Solder mask | 1234 openings on top (1203 pads + 7 NPTH + 24 SMD pads) and 1210 on the bottom; vias tented. The SMD pads leave 0.26 mm of mask between them | mask Gerbers |
| Paste | 24 openings on top, for the four SOT-363 chips; bottom empty. Not needed if the chips are soldered by hand | paste Gerber |
| Silkscreen | Both sides. Top 16668 strokes, bottom 5064. Most strokes are 0.127 mm; 981 are 0.1016 mm and 184 bottom strokes are 0.0508 mm | silk Gerbers |
| Parts | 421 footprints: 347 top, 74 bottom (LEDs, switches and other panel-side parts), 7 of them mounting holes, 4 of them SOT-363 chips | PCB |

## Package (`gerbers/`, zipped as `x0xb0x-mainboard-rev29-fabrication.zip`)

The package uses Gerber X2 with net attributes, in mm, 4.6 format:
- **Gerbers (`.gbr`):** `F_Cu`, `B_Cu`, `F_Mask`, `B_Mask`, `F_Paste`, `B_Paste`, `F_Silkscreen`, `B_Silkscreen`, `Edge_Cuts`.
- **Job file:** `mainboard-job.gbrjob`.
- **Drills:** Excellon `mainboard-PTH.drl` and `mainboard-NPTH.drl` (metric, decimal).
- **Drill documentation:** drill maps `*-drl_map.pdf` and `mainboard-drill-report.txt`.

Previews: `mainboard-preview-top.png` and `-bottom.png`, rendered with gerbv; the bottom view is mirrored, as seen from below.

Not included: an IPC-D-356 netlist. GND is two copper islands joined through the J3–J7 wiring, and +5V reaches the LED drivers through the internal strips of S19/S22. A fab that compared the copper against the KiCad netlist would report opens on both. Let the fab test against the netlist it extracts from the Gerbers.

## Differences from the original Eagle CAM output (revisions 25–27)

- **NPTH mask:** the 7 mounting holes open exactly 3.302 mm; Eagle added its 0.1016 mm stop frame (3.505 mm). This is harmless on mounting holes: the drill clears any mask that registers onto the rim.
- **Vias:** the 6 original vias are tented here. Eagle 4.13 probably exposed them (its via stop limit was not decoded).
- **Outline:** Eagle's 0.23 mm stubs at (0, 0) are not in KiCad's closed rectangle.

Every original pad, via, drill and pour outline, and all original silkscreen geometry and labels, match the original (revision-29 comparison). So does every original track, but one that is split where a new track joins it. The chips, their tracks and vias, and the pockets they cut in the pour, are additions. Eagle 4.13 computed its pour fill at CAM time; the fill itself was not regenerated for comparison.

## Choices for the owner

1. **Thickness 1.6 mm.** *Recommended*: the board and job files state it, and it is the standard thickness.
2. **Copper 1 oz (35 µm) outer layers.** *Recommended*: the weight is not recorded anywhere and 1 oz is standard. The board has no high-current path; its 0.4–1 mm tracks carry signals and small supply currents.
3. **Surface finish.** Options:
   - lead-free HASL (*recommended*: cheapest; the original's tinned pads look the same; every part is through-hole but the four chips, and their 0.65 mm pitch can be hand-soldered on HASL);
   - leaded HASL, if you solder with leaded solder (same result);
   - ENIG (flat gold, longer shelf life, costs more; its only use here is flatter pads for the four chips).

   Use the same finish on both boards.
4. **Mask and silkscreen colours.** Green mask, white silkscreen on both sides (*recommended*: matches the production I/O board photograph; no mainboard photograph is in the repository).
5. **Via tenting.** Order as exported, tented (*recommended*: needs no board change; 6 vias of 0.6 mm and 7 of 0.39 mm, none used as test points). Some fabs cannot guarantee full tenting at 0.6 mm and may leave the via rim partly open, which is harmless. Exposing them like Eagle would need a board-setting change in a new revision.
6. **Thin silkscreen.** Accept the fab's DFM warning for the 0.127 mm and thinner strokes (*recommended*: same geometry as the original; fabs typically print or widen them). Let the fab clip silkscreen from exposed pads, which is the usual default.
7. **Electrical test.** Ask for the fab's standard flying-probe test against its Gerber-extracted netlist. Do not send a KiCad netlist (see above).
8. **Panelisation.** Not needed: order the board as its own design, at the fab's minimum quantity. If the fab offers to remove or place its order number, put it on the bottom side or omit it.
9. **Assembly files.** For your own kit assembly. Four SOT-363 chips are the only SMD parts, soldered by hand, so no stencil or assembly order is needed. Fit them before their neighbours (see `kicad-working/smd-sites/README.md`). Q12, Q21, Q22 and Q26 are marked do-not-place: fit each SIP part only instead of its chip, never both:
   - `assembly/mainboard-bom.csv`: one row per reference. The silkscreen prints IC15A, IC15B, R100A and R100B for KiCad's IC15A0, IC15B0, R100A0 and R100B0; U$2–U$29 are the mounting holes.
   - `assembly/mainboard-positions.csv`: mm, Gerber orientation.
