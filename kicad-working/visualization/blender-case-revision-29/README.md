# Blender revision 29 — JFET sites on the mainboard

Open `x0xb0x-populated-with-case.blend` with Blender 5.2.2 LTS. This revision brings the scene level with KiCad working revision 30 on the mainboard. The KiCad board isn't changed, and no model, pad or pose is scaled, reshaped or moved.

- **Added:** the two SC-59 chips Q128 (2SK208-O) and Q139 (2SK208-Y), at their footprints. Each is KiCad's stock `SC-59` model, with three new materials in KiCad's colours.
- **Removed:** the TO-92 JFETs Q28 and Q39. KiCad marks them do-not-place, and a chip or its JFET goes on the board, never both. Their holes and pads stay and stand empty. Revision 28 still shows them.
- **Replaced:** the eight mainboard layer meshes (copper, pads, vias, both silkscreens, both masks, board body), from a fresh KiCad 30 export, in the scene's own materials. They now show the chips' lands and the 9 new track segments. There are no new vias.
- **Preserved:** the other 489 model references, the I/O board layers, the case, panels, LEDs, spacers, caps, wiring study, previous materials, cameras and animation. The scene still stores 1721 objects and 491 fitted references, 409 + 82. No material is retired: Q28 and Q39 shared theirs with other parts.

## Contacts

Measured at frame 1, in nominal model sizes. Gaps are mesh to mesh, in 3D. Land gaps are in plan, from the land to the neighbour's surface up to 0.3 mm above the chip's height, as `fit_check.py` measures them.

| Chip | Closest neighbour | Smallest gap | Closest land | Free height above the chip |
|---|---|---|---|---|
| Q128 | C33 | 0.35 mm | Gate land to R105, 0.08 mm | 7.71 mm, under R105 |
| Q139 | IC12 | 1.53 mm | Pin 3 land to IC12, 0.95 mm | 35.97 mm, under the I/O board's R22 |

No chip model overlaps anything, and the removed JFETs touched nothing either. Q128's other close neighbours are R105, 0.42 mm from the chip, R118, 1.31 mm, and C33, 0.28 mm from the drain land.

The land gaps agree with `../../smd-sites/fit-check.json` to 0.01 mm. Its body gaps read tighter, 0.26 mm rather than 0.42 mm to R105, because `fit_check.py` uses the largest sizes in Toshiba's S-Mini drawing, 3.1 x 1.75 mm plastic, and KiCad's model has 3.0 x 1.6 mm. Real parts vary by more than the 0.08 mm at the gate land, so the build note stands: keep R105 upright.

## Checks

All 491 models match fresh native KiCad exports. The saved scene passes 16 preservation checks against revision 28, 106 portability checks, 44 rear-opening checks with 974 rays, the 25-reference, 133-piece terminal-join check and the drill-fit check on 489 drilled models. All 8 layer meshes match a fresh export. The two chips stand within 0.001 mm of their KiCad positions and follow the mainboard in the three frames that show it; frame 160 hides the board, as it did before.

Frames 1 assembled, 80 exploded, 120 control-side, 160 wiring study. `jfet-*-before.png` and `-after.png` use identical cameras over each site, framed between the chip and the holes. A resistor lead crosses in front of Q128's pin-1 end in its view, so its mark doesn't show; Q139's does. Each site has its own lamp energy, the same before and after.

At a 2% tolerance, `assembled.png` has no pixel changed from revision 28. `control-side.png` has 245, at the holes of Q28 and Q39, and `exploded.png` has 1339, mostly where the JFETs are gone.

## Limits

- The chip model has nominal sizes, no part marking and no solder. It isn't CAD of the 2SK208 to be bought.
- Pads keep the scene's grey material, although the export colours them gold.
- The I/O board layers weren't refreshed. A fresh export has the same copper, pads, vias and main board body, but differs in both silkscreens and both masks and no longer has the detached datum strip.
- Nothing has been built or measured. These checks don't qualify physical fit or circuit operation.

See `../../../docs/blender-jfet-sites.json` and `../../smd-sites/README.md`.
