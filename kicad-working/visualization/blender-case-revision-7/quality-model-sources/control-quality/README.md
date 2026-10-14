# TL1100 publisher CAD alignment and validity repair

The default candidate uses the detailed TL1100Fxxxx STEP supplied by E-Switch through its public product asset host. The original file is preserved byte-for-byte with SHA256 `c8d75086238d6ab7716c6dc38c2d587c8d39ba9cc365655c49a244b4ca88d430`. The source is family CAD; its actuator geometry matches the exact TL1100F160Q published 7.30 mm height. Force, plating options and exact historical mold revision are not established by this geometric comparison.

`control-quality-manifest.json` contains one default assignment for all 23 S5–S27 references, using the full nominal/free-state model. A body-above-seat alternate is included outside `assignments[]`. Both variants include complete STEP, STL and separate face-role surface STL files for visual inspection. Face-role STLs are open surface subsets; their union reproduces the complete model, and they are not standalone closed solids.

## Canonical origin and external dimensions

The publisher CAD's body seating datum is Z=−3.8825 mm and actuator tip is Z=+3.4175 mm. A rigid +3.8825 mm Z translation places the seat at canonical Z=0, the actuator tip at +7.3 mm and terminal tips at −3.5 mm. X/Y remain centered on the original four-pad pattern. The full exact CAD bounds are X ±7.05 mm, Y ±6 mm, Z −3.5…+7.3 mm. The native assignment uses zero offset/rotation and unity scale. No board placement, side flip or case transform is baked into the candidate.

The source CAD had one invalid, zero-area cylindrical face at a hidden internal interface. Its two circular boundaries, 0.015 mm apart, had collapsed to a shared mid-height vertex. Generic repair did not resolve it. A local cylinder union of radius 1.5001 mm and height 0.035 mm repairs that interface. It adds **0.035683988 mm³**, or **0.007451%** of the original 478.905465 mm³ volume, while preserving exact external bounds. Both shapes outside a 3.2 ×3.2 ×0.1 mm internal region are valid and have zero symmetric-difference volume. The complete repaired shape is one valid solid. This localized repair is documented rather than represented as unchanged publisher topology.

The body-above-seat alternate retains only geometry at canonical Z≥0. It omits the below-seat terminal shapes while retaining above-seat terminal shoulders and manufacturer body detail; consequently its width is 12.8 mm. It is a source subset and is not a resized housing replacement.

## Electrical terminal axes and free-state retention bends

The nominal manufacturer terminal axes are X ±6.25 mm, Y ±2.50 mm. Actual imported B3F-40XX pad centers are X ±6.2484 mm, Y ±2.4892 mm, giving **0.010918 mm** axis residual. The actual drill is **1.1938 mm**; the manufacturer's drawing recommends **1.30 mm**. No drill or footprint was changed.

Cross-sections were sampled through the conservative 1.6 mm lamination interval at 0.025 mm steps, with 0.0005 mm curve discretization deflection. The nominal straight 0.30 ×1.00 mm terminal shoulder fits the actual circular drill with approximately **0.0641 mm radial margin**; the narrower 0.30 ×0.22 mm solder tip has approximately **0.4031 mm radial margin**. These geometric cross-section results do not qualify an installed elastic part.

The outward kink is the publisher's **uncompressed free-state retention geometry**. Its worst sampled radius from the actual drill axis is **0.928124 mm**, exceeding the actual drill radius by **0.331224 mm**. The rigid render therefore intersects the drilled volume until that retention bend compresses during insertion. The model does not simulate elastic deformation, stress, insertion force or tolerance. The actual drill is also smaller than the published recommendation. This is a detailed manufacturer nominal/free-state model, not a fully fitted or physically qualified terminal model. The pin-section report preserves every sampled section and the exact pad axes.

## Appearance and verification

The publisher file has one grey appearance. The candidate assigns explicit AP214 face styles for black housing/actuator and metal cover/terminals; these roles are inferred presentation choices. Adding styles preserves exact re-imported BRep geometry. STL tessellation may produce tiny chord differences in reported bounds (approximately 0.000052 mm at curved terminal extrema), while exact re-imported CAD bounds remain authoritative.

The source manufacturer STEP, actual PCB and imported footprint remained unchanged during generation. The full model contains 35,250 triangles; the body-above-seat alternate contains 33,938 triangles. Isolated native KiCad export probes and a standalone preview verify the readable geometry and palette without editing the actual project. No scene is saved or changed by these checks.

Manufacturer CAD/drawing rights remain with the publisher. The alignment, bounded repair and review scripts are original CC0-1.0 work. Physical cap fit, full switch travel, production tolerances and installed terminal fit remain unqualified.

## Final native export review

The final review passed isolated native KiCad export, raw GLB buffer inspection and a visually inspected GLB render. The full exact STEP bounds remain X ±7.05 mm, Y ±6 mm, Z −3.5…+7.3 mm. The maximum native GLB bound difference is 0.000247 mm from curve tessellation; its actuator tip differs from 7.3 mm by 0.000000172 mm. All primitives retain assigned materials and four palette colors. Both frozen STEP hashes remain unchanged. Reports are in `native-probes/native-canonical-bounds-audit.json`, `native-probes/native-color-export-audit.json` and `tl1100-final-review.json`.

The earlier incomplete review image was caused by the camera near clipping plane cutting through these small models. The corrected native preview `tl1100-native-cad-review.png` shows both variants completely. The correction changed only the standalone preview camera; the model assets were not changed. Native geometric completeness and accurate bounds do not qualify the free-state retention bends as installed terminal geometry.
