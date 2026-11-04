# Blender revision 28 — SMD sites on the mainboard

Open `x0xb0x-populated-with-case.blend` with Blender 5.2.2 LTS. This revision brings the scene level with KiCad working revision 29 on the mainboard. The KiCad board isn't changed, and no model, pad or pose is scaled, reshaped or moved.

- **Added:** the four SOT-363 chips Q112, Q121, Q122 and Q126, at their footprints. Each is KiCad's stock `SOT-363_SC-70-6` model, with three new materials in KiCad's colours.
- **Removed:** the SIP pairs Q12, Q21, Q22 and Q26. KiCad marks them do-not-place, and a chip or its pair goes on the board, never both. Their holes and pads stay and stand empty. Revision 27 still shows the pairs.
- **Replaced:** the eight mainboard layer meshes (copper, pads, vias, both silkscreens, both masks, board body), from a fresh KiCad 29 export, in the scene's own materials. They now show the chips' lands, tracks and 7 vias, and the other board changes since these meshes were last exported, such as KiCad 26's name labels.
- **Preserved:** the other 487 model references, the I/O board layers, the case, panels, LEDs, spacers, caps, wiring study, previous materials, cameras and animation. The scene still stores 1721 objects and 491 fitted references, 409 + 82.

## Do-not-place parts

The scene holds fitted references, as `scripts/verify_blender_scene.py` and `PROJECT.json` count them. An unfitted alternate has no place in it, as with IC15A0, which is mutually exclusive with IC15B0. `kicad-cli` exports do-not-place footprints by default, so `scripts/verify_kicad_blender_models.py` now passes `--no-dnp`. The drill-fit and terminal-join checks read KiCad rather than the scene, so they still export the pairs, and the pairs' leads stay checked against their holes.

## Contacts

Measured mesh to mesh at frame 1, in nominal model sizes:

| Chip | Closest neighbour | Smallest gap | Free height above the chip |
|---|---|---|---|
| Q112 | C18, overhanging | 0.43 mm | 0.46 mm |
| Q121 | R110 | 0.72 mm | 44.82 mm |
| Q122 | Q23, overhanging | 0.78 mm | 2.10 mm |
| Q126 | R100A0 | 0.07 mm | 51.14 mm |

No chip model overlaps anything. `../../smd-sites/fit-check.json` lists Q126 and R100A0 as touching because `fit_check.py` measures to the box around the chip, leads included. R100A0 enters that box by 0.09 mm just above the chip's top, where the chip body has no material. Real parts vary by more than 0.07 mm, so the build note stands: fit R100A0 after the chip and keep it from pressing on it.

The removed pairs touched nothing either.

## Checks

All 491 models match fresh native KiCad exports. The saved scene passes 16 preservation checks against revision 27, 106 portability checks, 44 rear-opening checks with 974 rays, the 25-reference, 133-piece terminal-join check and the drill-fit check on 489 drilled models. All 8 layer meshes match a fresh export. The four chips stand within 0.001 mm of their KiCad positions and follow the mainboard in the three frames that show it; frame 160 hides the board, as it did before.

Frames 1 assembled, 80 exploded, 120 control-side, 160 wiring study. `smd-*-before.png` and `-after.png` use identical cameras over each site. Tall neighbours hide Q112, Q121 and Q122 from any slant, so those three look straight down and clip everything more than 1.35 mm above the board; parts cut this way show open, and they still cast shadows.

## Limits

- The chip model has nominal sizes, no part marking and no solder. It isn't CAD of the parts to be bought.
- Pads keep the scene's grey material, although the export colours them gold.
- The I/O board layers weren't refreshed. A fresh export has the same copper, pads, vias and main board body, but differs in both silkscreens and both masks and no longer has the detached datum strip.
- Nothing has been built or measured. These checks don't qualify physical fit or circuit operation.

See `../../../docs/blender-smd-sites.json` and `../../smd-sites/README.md`.
