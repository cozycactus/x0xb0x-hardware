# SMD sites for the rare transistors

KiCad working revision 29 puts four SOT-363 chips on the mainboard, next to the holes of the rare SIP pairs they replace. Revision 30 does the same for the two 2SK30A JFETs, with SC-59 chips. The holes stay, so an original part or, for a pair, an [adapter](../adapters/ssip5-dual/README.md) can still go in if a chip doesn't work out.

**Status: routed and checked in KiCad. Nothing has been ordered, built or measured.**

| Chip | Replaces | Part | Why this part |
|---|---|---|---|
| Q112 | Q12, 2SC1583 | BCM847BS | Vbe matching is what counts here; the datasheet promises 2 mV at 2 mA |
| Q121 | Q21, 2SC1583 | BC847CDW1T1G | The one position where gain matters; this part has the higher gain |
| Q122 | Q22, 2SC2291 | BCM847BS | The model shows no effect from this pair |
| Q126 | Q26, 2SC1583 | BCM847BS | As Q12; a Vbe offset is trimmed out with TM4 |
| Q128 | Q28, 2SK30A-O | 2SK208-O | The same JFET on paper, in the same Idss grade |
| Q139 | Q39, 2SK30A-Y | 2SK208-Y | The same JFET on paper, in the same Idss grade |

The reasons and the simulated figures are in the [adapter README](../adapters/ssip5-dual/README.md), which uses the same chips. Those figures are model values.

**Fit each chip or the part it replaces, never both.** The sheets and the BOM mark Q12, Q21, Q22, Q26, Q28 and Q39 do-not-place, and those symbols are crossed out. Fit one instead of its chip only if you take the chip off.

## Building it

- **Solder the chips first,** before any neighbour. Pin 1 is at the silkscreen dot, and the pitch is 0.65 mm: use flux and check for bridges under magnification. The land pads are lengthened outward for an iron. Q128 and Q139 are easier, with a 1.9 mm pitch.
- **Tight places, in the nominal sizes of the illustrative models.** `fit-check.json` has all six sites.
  - **Q126 is tightest against thermistor R100A0's model.** The model's side reaches 0.09 mm over the chip's outline, just above the chip's 1.1 mm height. `fit_check.py` lists this as touching because it measures to the box around the chip, leads included. The [Blender revision 28 screen](../visualization/blender-case-revision-28/verification/chip-neighbour-audit.json), mesh to mesh, finds no overlap and a smallest gap of 0.07 mm at the chip's top edge. Real parts vary by more than that. Fit R100A0 after the chip and keep it from pressing on it. The chip stays here on purpose (see below).
  - **Lands:** Q121's pin 4 land ends 0.07 mm from standing resistor R110, and Q126's lands 0.07 mm from R100A0.
  - **Q128 stands between R105 and C33.** Its body ends 0.26 mm from the model of standing resistor R105, and its gate land 0.08 mm from it, so keep R105 upright. C33's model reaches 0.11 mm over the chip's edge, 0.32 mm above the chip. The WIMA MKS02 in the parts list is narrower than that model, 2.5 mm against 3.2 mm, and stands 0.39 mm clear of the chip.
  - **Overhangs:** C18's model reaches 0.31 mm over Q112's edge, 0.41 mm above the chip. Q23's reaches 0.5 mm over Q122's edge, 2.09 mm above it. Neither touches.
- **Measure the pair before relying on it.** BCM847's matching is stated only at 2 mA, and the ladder runs at 3 to 27 µA. BC847C has no matching figure at all. The adapter README lists what to measure at each site; on the board that means testing a chip off the board first, or at the holes of its site once it's fitted.

## What changed on the board

Routed by hand in the KiCad PCB editor: 81 track segments of 0.25 mm and 7 vias of 0.8 / 0.39 mm. The zones were refilled in the editor, and `finish_board.py` marked the SIP pairs do-not-place. One original B.Cu track, on N$148, is split where a new track joins it; its geometry is unchanged.

Q112 and Q126 were routed twice. The first routing, from `place_chips.py`'s positions, passed the rules but gave Q112 base tracks of 8.7 and 4.43 mm, with extra bends and a wide pocket in the F.Cu ground pour. `rework_sites.py` cleared those two chips' tracks, moved them, and shortened the lands of all four chips from 1.4 to 1.1 mm.

| Chip | Position | Base tracks | F.Cu pour lost, first routing → now |
|---|---|---|---|
| Q112 | Centred under its row of holes | 4.50 and 4.51 mm | 19.57 → 9.96 mm² |
| Q121 | Not moved | 6.00 and 5.99 mm | 16.86 → 17.08 mm² |
| Q122 | Not moved | Both bases are on N$115 | 14.19 → 14.65 mm² |
| Q126 | Beside the thermistor | 3.68 and 5.26 mm | 9.99 → 8.50 mm² |

Q126's base tracks can't be made equal. The chip stays between R100A0 and its row, so that it stays near the thermistor's temperature. That is my reading of why the thermistor sits there; no design note states it. The original N$98 arc on B.Cu also limits where a via can go. A difference of 1.6 mm in a base track at these currents has no modelled effect, because the analog model has no copper in it.

The pour loss is within 8 mm of each chip, from `compare_gerbers.py`. Outside those pockets the pour is unchanged but for specks.

Compared with revision 28, from `compare_board.py` and `compare_gerbers.py`:

| Check | Result |
|---|---|
| Original tracks, arcs and vias | All still there; new ones lie within 14 mm of a chip |
| Existing footprints | Differ only in their links to symbols, the do-not-place mark on the four SIP pairs, and KiCad's trimming of unused layers from the hole keepouts |
| B.Cu, F.Mask, F.Paste, F.Silkscreen Gerbers | Differ only within 14 mm of a chip |
| F.Cu Gerber | 51.1 mm² differs near the chips. Another 0.081 mm² differs elsewhere, in specks of at most 3 pixels at 25 µm, which is the refilled pour's arithmetic |
| B.Mask, B.Paste, B.Silkscreen, Edge.Cuts Gerbers | Identical |
| Original Eagle boards ([comparison](../validation/models-review-29/README.md)) | All 1209 original pads and 1209 plated holes still match. The new items are reported as extra, and one track segment as split |
| DRC of the copper as saved | No copper violation. 6 more silkscreen warnings than revision 28 |
| Update PCB from Schematic, read in the editor, not applied | Nothing removed. The chips get only the sheet name, sheet file and unit lines that all 421 footprints get |

## Revision 30: the 2SK208 sites

The 2SK30A was the last rare transistor with no answer on this board. Its replacement comes only in SC-59, this project has no adapter for that package, and Mouser lists none in stock. So the mainboard now has two more sites, placed by `place_jfets.py` and finished by `finish_jfets.py`.

**The part.** Toshiba's 2SK208 sheet and the 2SK30A sheet give the same figures: -50 V gate to drain, 10 mA gate current, 100 mW, the grades R, O, Y and GR with the same Idss limits, Vgs(off) -0.4 to -5 V, |Yfs| at least 1.2 mS, Ciss 8.2 pF, Crss 2.6 pF and a noise figure of 0.5 dB. The 2SK30A figures come from Tiger Electronic's copy of Toshiba's sheet. Neither part was measured. Pins are 1 source, 2 drain, 3 gate; the footprint's pad numbers follow Toshiba's S-Mini drawing, and its pad layout agrees with KiCad's own SC-59.

**The footprint.** `x0x-smd:SC-59_Hand` has lands 1.2 x 0.7 mm, running from 0.75 to 1.95 mm off centre. Q128's body fits the 3.17 mm between the silkscreen of R105 and C33, so its silkscreen is only short marks, and the courtyard narrows around the gate land to leave R105's hole outside it.

**The tracks were not drawn with the mouse, unlike revision 29's.** The screen was locked when they were routed. Each path was drawn by hand on a map of the copper, checked for clearance and written by `finish_jfets.py`. KiCad's DRC then checked them like any other track.

| Track | Layer, width | Length | Note |
|---|---|---|---|
| Q128 gate to C33, N$113 | F.Cu, 0.25 mm | 4.71 mm | The VCO's timing node. A straight 45 degree line, which passes under the chip's corner, in the pour |
| Q128 source to R105, N$108 | F.Cu, 0.25 mm | 1.73 mm | |
| Q128 drain to Q28's drain hole, +12V | F.Cu, 0.25 mm | 5.96 mm | About 2 mA, so about 12 mV lost |
| Q139 drain to Q39's drain hole, N$53 | F.Cu, 0.25 mm | 1.82 mm | Gate and source join the ground pour, as Q39's do |

That is 9 track segments and no vias. Within 8 mm of the chips the F.Cu pour loses 6.20 mm² at Q128 and 2.17 mm² at Q139, far less than at the SOT-363 sites.

Compared with revision 29, from `compare_board.py` and `compare_gerbers.py`:

| Check | Result |
|---|---|
| Original tracks, arcs and vias | All still there, none split; the 9 new segments lie within 14 mm of a chip |
| Existing footprints | Differ only in their links to symbols and the do-not-place mark on Q28 and Q39 |
| F.Cu Gerber | 8.72 mm² differs near the chips. Another 0.023 mm² differs elsewhere, in specks of at most 7 pixels at 25 µm, from the refilled pour |
| F.Mask, F.Paste, F.Silkscreen Gerbers | Differ only within 14 mm of a chip |
| B.Cu, B.Mask, B.Paste, B.Silkscreen, Edge.Cuts Gerbers | The same when drawn. B.Cu's file lists its objects in another order |
| Drill files | The same but for their dates |
| Original Eagle boards ([comparison](../validation/models-review-30/README.md)) | All 1209 original pads and 1209 plated holes still match, as at revision 29 |
| DRC of the copper as saved | No copper violation. Counts as at revision 29: 341, 1 and 127. KiCad lists at most 199 `silk_over_copper` items, and that type is already full, so a new one can't show in the count |
| Update PCB from Schematic, read in the editor, not applied | Nothing removed. The chips get only the sheet name, sheet file and unit lines that all 423 footprints get |

## Limits

- **Silkscreen:** R111's and Q21's printed text and outlines run under Q121's pads, and Q22's under Q122's. The fab clips silkscreen at pads, so some of that text will be cut. Q112's own label crosses Q15's outline. Revision 29 doesn't move the original text.
- **Silkscreen at Q128:** Q28's printed label runs under Q128's body and across its drain land, so the fab will clip it there. Revision 30 doesn't move the original text.
- **The pour:** the ground pour has a pocket at each site, sized in the table above. KiCad finds all the same connections as before, and one known gap remains, as at revision 27. The effect on the filter's noise or hum hasn't been simulated, and the analog model has no copper in it.
- **Blender:** [revision 28](../visualization/blender-case-revision-28/README.md) has the four SOT-363 chips and revision 29's copper changes, and leaves the do-not-place SIP pairs out. Revision 27 still shows the pairs. Neither has Q128 or Q139: both still show Q28 and Q39.
- **Availability:** checked on 2026-11-04. Mouser: BC847CDW1T1G 14,336; BCM847BS from Diotec 7,100, Nexperia 1,508 + 2,018, Diodes 238. Digi-Key: BC847CDW1T1G 48,000; BCM847BS from Diotec 12,587, Nexperia and Diodes none. On 2026-11-05 Mouser had 2SK208-O 9,313 and 2SK208-Y 9,454 at $0.66. Check on the day.

## Rerun

```sh
git show 8d172d1:kicad-working/mainboard/mainboard.kicad_pcb > /tmp/rev28.kicad_pcb
python3 -I kicad-working/smd-sites/compare_board.py /tmp/rev28.kicad_pcb kicad-working/mainboard/mainboard.kicad_pcb
python3 kicad-working/smd-sites/compare_gerbers.py /tmp/rev28.kicad_pcb kicad-working/mainboard/mainboard.kicad_pcb
python3 kicad-working/smd-sites/fit_check.py
```

For revision 30, compare with `1ba31be`'s board instead of `8d172d1`'s.

The last two need numpy; `compare_gerbers.py` also needs scipy, Pillow and gerbv. `place_chips.py`, `finish_board.py`, `rework_sites.py`, `place_jfets.py` and `finish_jfets.py` are the record of what was done to the board. Don't run them again.
