# Bent-back regulator and full-size heatsink installation illustration

The original x0xb0x power-supply assembly instruction explicitly tells the builder to bend **IC20 back before attaching the heatsink**. The original `7805place`, `7805soldered` and `7805measure` photographs show the regulator body and tab approximately parallel to the PCB, extending out beyond the board edge. The previous upright body model did not represent that assembly instruction.

This isolated candidate retains the complete revision 9 heatsink and the existing nominal MC78M05 TO220 plastic body/tab. Both are rigidly rotated into a photo-qualified bent-back illustration. The source-qualified width, depth, thickness, hole and all folds remain intact. The current project boards, older source models, case, footprints, copper and saved Blender scenes are unchanged by these scripts.

The two assignment entries in `bent-pair-manifest.json` are independently project-compatible: **IC20 / 78XXS** and **KK1 / D03S**. Offsets and rotations remain zero; scales remain unity. The illustration pose is contained in each complete colored STEP file.

| Model | Retained source geometry | Canonical bounds in its own source footprint frame, mm |
|---|---|---|
| IC20 | 10.0 mm body width, 4.455 mm plastic depth, 15.5 mm body/tab length, 1.27 mm tab thickness and 3.66 mm hole; two colored source solids | X −5..5, Y 3..18.5, Z 1.38..5.835 |
| KK1 | Revision 9 full folded 574502B00000G, 21.84 × 10.03 × 19.05 mm before rotation; one solid, 86 faces, 0.63 mm sheet, 3.81 mm hole | X −10.92..10.92, Y 2.63..21.68, Z 0.75..10.78 |

The exact **−90° angle and 2.0 mm installation-height datum are illustration assumptions**. The source photos were visually inspected, but were not used as calibrated metrology. No factory formed-lead drawing or installed bend-radius dimension was found. **All IC20 leads remain omitted**: the previous nominal lead-width/hole-fit concern is retained openly, and no terminals are thinned, displaced or invented.

The canonical mappings are explicit: the old IC20 body maps `(x,y,z)` to `(x,z,2−y)`; the old KK1 maps to `(x,z+2.63,9.51−y)`. The native IC20 footprint is **1.27 mm toward the PCB interior from KK1**. That relative translation is applied by KiCad, not duplicated into the regulator model. After the original native placement, both mounting-hole axes are coaxial at Y14.44 mm in the KK1 frame. The nominal back-contact plane is Z1.38 mm; the regulator tab spans Z1.38..2.65 mm and the rear heatsink sheet Z0.75..1.38 mm.

The prior source-aligned **1.729422 mm³** regulator overlap remains entirely within the reconstructed free-state spring-finger regions, with **zero overlap outside those regions**. No spring is deformed or removed. This documents nominal geometry and does not simulate or certify elastic clamping, contact force, alloy condition, thermal behavior or tolerance fit.

## Validation

- `bent-pair-geometry-audit.json`: **33 checks passed** after fresh STEP reload. Source face/solid counts, volumes and inverse-rigid-transform geometry were preserved; all full and segmented STL meshes are closed.
- Exact C3/C4/C5 source BReps no longer intersect either illustrated part. Heatsink source-model distances are **C3 9.084 mm, C4 4.535 mm, C5 6.163 mm**. The wider exact-neighbor check is restricted to zero/unity F.Cu model assignments; existing library-pose exceptions and B.Cu placement are covered by the separate native screen.
- `native-probes/native-export-audit.json`: actual KiCad GLB export retains zero/unity assignments, both IC20 material roles, the heatsink material and the actual −1.27 mm relative native origin. Maximum canonical bounds error is **0.000001603 mm**.
- `bent-pair-native-scene-screen.json`: stable Blender revision 6 was read without saving. **609 original mesh instances** were scanned, with **16 candidate/obstacle pairs** refined against the current native boards, components, panels, spacers and case. No new triangle-surface intersections were found; saved scene SHA is unchanged.
- `bent-pair-native-review.png` displays native KiCad model meshes with a small illustrative source-board-edge patch. The left study includes the complete heatsink; the right removes the heatsink to expose the same bent body/tab. Those side-by-side arrangement translations are preview presentation only.

A clear mesh-surface screen does not certify complete containment, lead fit, original case seating or physical assembly. Original regulator vendor/suffix, exact bend geometry, mounted height and spring behavior still require physical confirmation. This candidate corrects the clearly documented direction of installation while preserving those limits.

## Sources

The original author page is [x0xb0x power-supply assembly](https://www.ladyada.net/make/x0xb0x/fab/powersupply.html). Direct original retrieval returned HTTP403; the HTML and original images were recovered from the project mirror at pinned commit `1910f746d2d8758f2651596b00c08f76c847c926`. `sources/retrieved-source-manifest.json` records exact URLs, byte sizes and SHA256 hashes. The retained original photos were visually inspected before modeling.

The original [parts page](https://ladyada.net/make/x0xb0x/fab/parts.html) identifies MC78M05/7805 and Aavid574502B00000G. Existing nominal regulator dimensions are sourced within the [onsemi MC78M00 case221AB drawing](https://www.onsemi.com/download/data-sheet/pdf/mc78m00-d.pdf), retained here as `sources/onsemi-mc78m00.pdf`; this does not authenticate the exact original supplied vendor. Full heat geometry comes from revision 9's reconstruction of the [Boyd specific drawing](https://info.boydcorp.com/hubfs/Thermal/Air-Cooling/Boyd-Board-Level-Cooling-Slide-On-5744.pdf), retained here with its prior source-interpretation limitations.

Original reconstruction and installation illustration are CC0-1.0. Original-author photos and manufacturer drawings retain their publishers' copyrights. No manufacturer-authored CAD or measured installed fit is claimed.
