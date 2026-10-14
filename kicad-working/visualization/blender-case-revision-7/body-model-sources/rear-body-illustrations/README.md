# Rear connector body illustrations

Five combined STEP models and eight separate STL segments cover all eleven rear connector references. These fill the visible assembly using nominal published body dimensions. They are body-only visual illustrations; terminals and locators are omitted, and physical fit is not qualified. PCB files and the delivered Blender scene are not edited by this package.

| References | Original footprint | Model basis | Nominal body dimensions (mm) |
|---|---|---|---|
| DIN1–DIN4 | CP-2350 | SDS-50J manufacturer family drawing | 20 × 15.8 × 21.1 |
| CV0, GATE0 | MJ-3536N | Current Same Sky MJ-3536N drawing | 10 × 15.8 × 10, plus 3 mm bushing projection |
| POWER0 | PJ-202AH | Current Same Sky PJ-202AH drawing | 9 × 14.4 × 11 |
| HEADPHONE0, MIXIN0, MIXOUT0 | REAN_1_4STERO | REAN NYS216 drawing | 20 × 33 overall depth × 16.5 maximum height |
| USB0 | PN61729 | Original BOM Kobiconn 154-2442-E, drawing KC-301021 | 12.04 × 16 × 10.62 |

The USB body is explicitly a generic Type B illustration based on the original BOM part. It is not represented as exact PN61729 CAD. Current MJ-3536N/PJ-202AH drawings provide nominal bodies but do not establish historical lead or locator positions. SDS-50J socket details, bushing threads, small housing features and USB shell gauge/aperture chamfers are simplified. The NYS216 model retains the conservative 16.5 mm maximum front height shown in the source; its other view also calls out a 15.5 mm side height. No body was reduced to hide a fit conflict. NYS216 exterior nut/washer are omitted because the scene already includes separately sourced exterior hardware.

## Coordinates and assignment

Every asset is in millimetres in the original F.Cu footprint frame: X is footprint X, Y is negative footprint Y, and Z is outward from the PCB mounting surface. No board placement, case placement, side flip, or board thickness is baked into these files. The native KiCad model assignment uses offset [0, 0, 0], rotation [0, 0, 0], and scale [1, 1, 1]. KiCad then applies the actual footprint pose. POWER0's actual 180 degree footprint rotation is essential: its canonical housing extends toward negative Y, matching the original footprint construction.

`rear-body-illustrations-manifest.json` contains `parts[]` for independent STL inspection and `assignments[]` for one combined STEP model per footprint. Each assignment includes source hash, classification, source URLs and limitations. Each STEP combines housing and mating face/bushing segments; it includes AP214 style entities for suggested colors. FreeCAD successfully re-imported every combined STEP, and all resulting solids were valid. Color appearance can vary by importing application.

The standalone `rear-body-review.png` shows five representative bodies at the same scale, using their source dimensions. It does not show terminal fit, panel fastening, or complete assembly clearance. `rear-body-illustrations.FCStd` retains editable solids. `source/` includes copied primary drawings and the extracted original USB drawing text with its source URL. The original PCB footprint poses and source hashes are recorded in the manifest.

## Validation boundary

All eight STL exports were generated from valid CAD solids. The package contains 7,960 triangles and eleven assigned reference instances. Combined STEP files were re-imported and checked for valid solids. Geometry provides full nominal body envelopes; no check establishes electrical pin compatibility, drill registration, insertion force, manufacturing tolerances, exact historic part revision, or physical enclosure fit. Earlier project geometry and existing model assignments are outside this package's mutation scope.
