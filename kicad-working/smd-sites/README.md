# SMD sites for the rare dual transistors

KiCad working revision 29 puts four SOT-363 chips on the mainboard, next to the holes of the rare SIP pairs they replace. The holes stay, so an original pair or an [adapter](../adapters/ssip5-dual/README.md) can still go in if a chip doesn't work out.

**Status: routed and checked in KiCad. Nothing has been ordered, built or measured.**

| Chip | Replaces | Part | Why this part |
|---|---|---|---|
| Q112 | Q12, 2SC1583 | BCM847BS | Vbe matching is what counts here; the datasheet promises 2 mV at 2 mA |
| Q121 | Q21, 2SC1583 | BC847CDW1T1G | The one position where gain matters; this part has the higher gain |
| Q122 | Q22, 2SC2291 | BCM847BS | The model shows no effect from this pair |
| Q126 | Q26, 2SC1583 | BCM847BS | As Q12; a Vbe offset is trimmed out with TM4 |

The reasons and the simulated figures are in the [adapter README](../adapters/ssip5-dual/README.md), which uses the same chips. Those figures are model values.

**Fit each chip or the SIP part it replaces, never both.** The sheets and the BOM mark Q12, Q21, Q22 and Q26 do-not-place, and those SIP symbols are crossed out. Fit one instead of its chip only if you take the chip off.

## Building it

- **Solder the chips first,** before any neighbour. Pin 1 is at the silkscreen dot, and the pitch is 0.65 mm: use flux and check for bridges under magnification. The land pads are lengthened outward for an iron.
- **Tight places, in the nominal sizes of the illustrative models.** `fit-check.json` has all four sites.
  - **Q126 is tightest against thermistor R100A0's model.** The model's side reaches 0.09 mm over the chip's outline, just above the chip's 1.1 mm height. `fit_check.py` lists this as touching because it measures to the box around the chip, leads included. The [Blender revision 28 screen](../visualization/blender-case-revision-28/verification/chip-neighbour-audit.json), mesh to mesh, finds no overlap and a smallest gap of 0.07 mm at the chip's top edge. Real parts vary by more than that. Fit R100A0 after the chip and keep it from pressing on it. The chip stays here on purpose (see below).
  - **Lands:** Q121's pin 4 land ends 0.07 mm from standing resistor R110, and Q126's lands 0.07 mm from R100A0.
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

## Limits

- **Silkscreen:** R111's and Q21's printed text and outlines run under Q121's pads, and Q22's under Q122's. The fab clips silkscreen at pads, so some of that text will be cut. Q112's own label crosses Q15's outline. Revision 29 doesn't move the original text.
- **The pour:** the ground pour has a pocket at each site, sized in the table above. KiCad finds all the same connections as before, and one known gap remains, as at revision 27. The effect on the filter's noise or hum hasn't been simulated, and the analog model has no copper in it.
- **Blender:** [revision 28](../visualization/blender-case-revision-28/README.md) has the four chips and these copper changes, and leaves the do-not-place SIP pairs out. Revision 27 still shows the pairs.
- **Availability:** checked on 2026-11-04. Mouser: BC847CDW1T1G 14,336; BCM847BS from Diotec 7,100, Nexperia 1,508 + 2,018, Diodes 238. Digi-Key: BC847CDW1T1G 48,000; BCM847BS from Diotec 12,587, Nexperia and Diodes none. Check on the day.

## Rerun

```sh
git show 8d172d1:kicad-working/mainboard/mainboard.kicad_pcb > /tmp/rev28.kicad_pcb
python3 -I kicad-working/smd-sites/compare_board.py /tmp/rev28.kicad_pcb kicad-working/mainboard/mainboard.kicad_pcb
python3 kicad-working/smd-sites/compare_gerbers.py /tmp/rev28.kicad_pcb kicad-working/mainboard/mainboard.kicad_pcb
python3 kicad-working/smd-sites/fit_check.py
```

The last two need numpy; `compare_gerbers.py` also needs scipy, Pillow and gerbv. `place_chips.py`, `finish_board.py` and `rework_sites.py` are the record of what was done around the hand routing. Don't run them again.
