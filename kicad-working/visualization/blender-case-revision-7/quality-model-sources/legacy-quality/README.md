# Mitsubishi 2SC2291 detailed Q22 candidate

The recovered four-page scan is a primary Mitsubishi Semiconductor datasheet. Its header reads 三菱半導体〈トランジスタ〉 and explicitly identifies 2SC2291. The original PDF is preserved as `2SC2291-downloaded.pdf`, SHA256 `94490817af4574353e2d13ef7720efb3d358c5aa748e3b2b4b7d8fc0cb94f935`. It was recovered from the public diyaudio attachment through the existing logged-in browser. The 2021 PDF metadata dates the scan, not the original manufacturer publication.

This candidate replaces the guessed Q22 body with a drawing-derived maximum package and five nominal full-diameter leads. It is original parametric CAD, not downloaded manufacturer 3D CAD. No identity or package dimensions are borrowed from 2SC1583 merely because the source devices share SSIP5.

## Manufacturer dimensions and pinout

The page 1 drawing gives **8.1 mm maximum width, 3.6 mm maximum depth and 5.6 mm maximum height**, with a **2 ×2 mm top bevel in the YZ side profile**. The lead row is **1.4 mm from the flat side**, opposite that bevel. Nominal row pitch is **1.25 mm**, nominal round lead diameter **0.45 mm**, and factory uncut lead length **10.5 mm minimum**. The note identifies untoleranced dimensions as representative values.

Canonical flat face is negative Y and opposite bevel positive Y, with the lead row at Y0. Body bounds therefore use Y −1.4…+2.2 mm. Pin 1 is negative X before the actual native footprint rotation. Source pin functions left to right are **1 E1, 2 C1, 3 common B, 4 C2, 5 E2**. Face naming is a frame convention; no unverified manufacturer lettering is embossed on the model.

## Explicit installed illustration

The original Q22 SSIP5 footprint has **2.286 mm** pitch and **1.0 mm** drills. Nominal straight manufacturer leads at 1.25 mm pitch would not match those pads. The full 8.1 mm body is preserved, and the full 0.45 mm wires spread above the board from package roots X −2.5, −1.25, 0, 1.25, 2.5 mm to original board axes X −4.572, −2.286, 0, 2.286, 4.572 mm.

Body bottom **Z3.0 mm**, top Z8.6 mm, tangent circular **R0.65 mm** bends, 0.12 mm internal lead embedding and tails ending at Z−2.5 mm are explicitly chosen installation illustrations. They are not manufacturer stand-off, forming, bend-stress or trim specifications. Straight lower tails begin at Z0.4 mm and continue through the full nominal 1.6 mm board thickness.

The illustrated formed lead length from the body is 5.5 mm for the centre pin, 5.7480 mm for the inner pair and 6.4234 mm for the outer pair. These lengths depict trimmed leads, with at least 5.0000, 4.7520 and 4.0766 mm respectively cut from the published minimum 10.5 mm factory length. Exact installed stand-off, cut length, alloy/temper, stress, springback and actual part tolerances remain unknown.

No source PCB pad, body dimension or native assignment was moved or scaled to make the illustration fit. The Q22-specific model node stays zero offset, zero rotation and unity scale; the existing F.Cu footprint angle 180° remains the native placement. The heterogeneous SSIP5 cache remains unassigned. This model must not be propagated to other SSIP5 devices.

## Validity and native export

The colored STEP contains six valid solids: maximum molded body and five formed leads. Their united external geometry is one valid connected solid; the combined STL is closed with **51,208 facets**. Black epoxy and silver metal are presentation choices. Adding AP214 styles preserves reimported BRep serialization.

Exact trimmed BRep bounds use FreeCAD `optimalBoundingBox()`: **X ±4.797 mm, Y −1.4…+2.2 mm, Z −2.5…8.6 mm**. Ordinary `BoundBox` conservatively includes unused toroidal-trim regions at X ±4.869093 mm; that value is recorded separately and does not indicate an enlarged physical lead. The exact body remains **X ±4.05 mm, Y −1.4…+2.2 mm, Z3…8.6 mm**.

The isolated installed KiCad exporter combines the six source solids into one mesh with two materials. Read-only native topology grouping recovers all six connected features. Each feature agrees with the exact STEP bounds to within **0.000000382 mm**. Both colors survive export, and F.Cu angle 180° and XY placement pass. The minimal probe uses default layer stack geometry; its measured model plane is recorded and does not establish the actual board's installed height.

The independent source/section audit checks the exact body, YZ bevel, five source roots and seven planes across nominal 1.6 mm lamination against the actual Q22 pads/drills. Its nominal radial lead-to-drill margin is **0.275 mm**. This verifies the drawn full-diameter straight tails against the source holes; it does not qualify plating, tolerances, physical lead forming or complete assembly clearance.

`2sc2291-native-package-review.png` is visually inspected and shows both the flat-face and opposite-bevel views. No delivered Blender scene was opened or saved. No actual project or shared footprint cache was edited.

## Files

`legacy-quality-manifest.json` supplies one Q22-specific assignment, source provenance, all canonical dimensions, lead forming choices and original file hashes. `build_2sc2291_candidate.py` regenerates the candidate, with the CC0 STEP color helper in this directory. Complete STEP/STL and separate body/lead STLs are retained for inspection. Native and independent audits are `native-probes/native-export-audit.json` and `independent-2sc2291-audit.json`; final asset hashes and STL closure are recorded separately. The original generator/reconstruction is CC0-1.0; the manufacturer scan retains publisher rights.
