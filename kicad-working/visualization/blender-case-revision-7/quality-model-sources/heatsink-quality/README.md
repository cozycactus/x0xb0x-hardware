# KK1 detailed 574502B00000G drawing-derived candidate

This isolated review replaces the coarse three-solid envelope with one continuous folded aluminium sheet, including rounded returns, lanced spring fingers, an internal channel, the published through hole and a holding catch. No public exact manufacturer STEP was recovered in the bounded search. This is an original parametric reconstruction from the exact 574502B00000G drawing, not manufacturer CAD. The 03200/03300/03700 solder-tab variants were not substituted.

The colored STEP and STL are `Aavid_574502B00000G_DrawingDerived_FoldedSpring.step` and `.stl`. `heatsink-quality-manifest.json` contains one compatible assignment for ioboard KK1, footprint D03S, with zero offset/rotation and unity scale. The generator is `build_heatsink_candidate.py`. Source PCB, footprint, previous model and nominal regulator hashes are retained; none were edited. The generator/review work is CC0-1.0; manufacturer source drawings retain publisher rights.

## Published dimensions and reconstruction limits

The primary 2017 Boyd/Aavid PDF is preserved with SHA256 `dd353265a5a8fdb57d77b1abe8a6c40b036684f2c6df460ee070fad60bae2f5f`. Its page 2 lower drawing explicitly identifies **574502B00000G**. Width 21.84 mm, depth 10.03 mm and height 19.05 mm govern the full candidate. Exact canonical bounds are X ±10.92 mm, Y −1.27…8.76 mm and Z 0…19.05 mm. The prior illustration datum is retained; no installed fitting shift is baked into the model.

The same drawing supplies a 4.19 ±0.13 mm checking-gauge gap, Ø3.81 mm through hole, metric hole-axis height 11.81 mm, and upper-lance datum 14.99 mm. Its parenthetical 11.81 (.485) callout conflicts internally; the manufacturer catalogue printed page 45 corroborates 11.81 (.465), so metric 11.81 is retained. The family table's 9.02 mm depth conflicts with the specific drawing's 10.03 mm; the specific drawing governs. The manufacturer catalogue also identifies 0.63 mm aluminium, black anodize and the exact no-solder-tab FigureB variant. Its full mirrored PDF could not be archived because the distributor server failed/timed out; the accessed source URL and observed evidence are recorded in `sources/drawing-feature-evidence.json`.

Inner channel width, bend radii, lances, contact-finger loft and small holding catch are traced/assumed because the drawing does not dimension their tooling geometry. They are explicitly parameterized rather than presented as exact production CAD. Spring alloy/temper, spring force, deformation, stamping tolerances, surface finish thickness and actual installed slide position remain unqualified. The original 13.716 mm D03S footprint artwork conflicts with the 21.84 mm BOM body; the original artwork is unchanged.

## Mechanical result at the unchanged native placement

The original KK1 and IC20 source origins differ by native Y −1.27 mm, with both F.Cu and angle 0. The isolated native probe preserves that relationship. It uses the unchanged review 8 nominal body-only IC20 illustration, not an authenticated installed regulator assembly.

The coarse three-solid heatsink intersects nominal IC20 by **40.92mm³**. The detailed continuous candidate intersects it by **48.642693mm³**, in the two front cooling returns at KK1-frame bounds X ±5 mm, Y −1.27…−0.65 mm and Z 3…18.5 mm. No regulator body or heatsink was trimmed, scaled or moved to suppress this result.

The interference is not restricted to the slender reconstructed spring fingers. The checking channel is at Y 3.94…8.13 mm, while nominal IC20 occupies Y −5.105…−0.65 mm. The retained illustration seat/body mapping is therefore incompatible with that channel. This is an unresolved source/seat limitation, not qualified elastic compression or clamping contact. A physically fitted assembly would need actual part/installed seating evidence. Thermal contact or performance is not certified by this visual candidate.

`heatsink-native-contact-review.png` is visually inspected: left shows complete native candidate, centre the retained nominal IC20 pose, and right an exact BRep intersection witness in red through transparent presentation copies. The delivered scene was not opened or saved.

## Validation

Fresh exact STEP import: **one valid solid, 86 faces, 797.077409635 mm³**. Round-trip volume is preserved and adding 86 AP214 face styles preserves exact imported BRep serialization. The independent 12-check audit verifies continuity, published bounds, 0.63 mm sheet, hole radius/axis, 4.19 mm checking gap, explicit mm units, zero assignment and unchanged source hashes. It passes.

The isolated installed KiCad exporter creates one complete KK1 native mesh with black material. Fresh Blender native import agrees with exact STEP bounds to **0.000001144 mm**, retains source relative IC20 translation to within 0.000000139 mm, and passes the native audit. These are source-qualified geometric/export checks, not installed fit qualification.

Reports: `independent-heatsink-audit.json`, `native-probes/native-export-audit.json`, `nominal-regulator-contact-audit.json`, `sources/drawing-feature-evidence.json`, and `sources/cad-availability.json`. Frozen candidate hashes are in `frozen-candidate-hashes.json`.
