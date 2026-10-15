# Blender revision 25 — original-kit resistor colour bands

Open `x0xb0x-populated-with-case.blend` with Blender 5.2.2 LTS. All 212 fixed resistors show the native KiCad 22 banded models: tan 5% bodies with four bands and light-blue 1% bodies (R4, R5, R106, R74-R90) with five, read from the original parts page. Body and lead geometry are unchanged; only the 212 existing part meshes change (outlines equal within 1 micrometre), twelve body and band materials are added, and two materials left unused by the old beige bodies drop out. All 1721 objects, 491 native references, the Xicon XRL electrolytics, 40 LEDs and spacers, 23 caps, case geometry, camera poses and animation are preserved.

Upright parts read from the top, lying parts from the pad-1 end. Band positions, widths and colour values are illustrations; the 1% body colour is sampled from uncalibrated photographs and the 5% tan from the page's band graphic. See `../../../docs/resistor-colour-bands.json` and the KiCad 22 review for sources and limits.

All 491 models match fresh native KiCad exports. The saved scene passes 13 preservation checks, 106 portability checks, 44 rear-opening checks/974 rays, the 25-reference/133-piece terminal-join check and the drill-fit check on all 489 drilled models. Because the outlines are unchanged, no clearance or contact changes.

Frames 1 assembled, 80 exploded, 120 control-side, 160 wiring study. `resistors-*-before.png` and `-after.png` use identical cameras over the 1% 200K row and a 5% cluster; their lighting is temporary. These checks do not qualify physical fit, tolerances or circuit operation.
