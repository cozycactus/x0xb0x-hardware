# PacTec PT-10 visualization reconstruction

The case geometry is reconstructed from PacTec drawing **82232, revision C**,
mirrored by [Farnell/Newark](https://www.farnell.com/datasheets/1483254.pdf).
The local original PDF and its SHA-256 provenance are in `../source/`.

This is an editable visualization model, not the original manufacturer's CAD.
No PT-10 STEP or Pro/ENGINEER source was recovered. Exact molded draft angles,
fillet radii, internal ribs, retaining clips, screws, and rubber feet are omitted.
The STL shells are separate valid solids, supplied in millimeters; importing at
0.001 scale gives Blender meters. The FCStd and STEP contain the same two bodies.

## Coordinate frame and panel datums

X is across the case, centered on zero; Y runs from the front toward the rear;
Z=0 is the outer floor of the bottom cover, excluding feet.
`pt10-datums.json` gives the panel bases and all reconstruction assumptions.
`case-parts.json` identifies the meshes and checks their validity and extents.

Printed case dimensions are 11.000 x 7.998 x 3.033 inches
(279.4 x 203.1492 x 77.0382 mm) with a 15-degree main panel slope.
These override the rounded 11 x 7.9 x 3-inch catalogue description.
The main plate is 9.150 x 6.428 x .062 inches, and the rear plate is
8.580 x 2.070 x .062 inches. The original x0xb0x panel files supply its cutouts.

Two necessary placements are traced from the dimensionally calibrated C-C
vector view, and should be treated as approximately +/-0.5 mm:

- Main panel front setback: 22.6929 mm to its underside front edge.
- Rear panel outer-face depth: Y=198.4947 mm.

The main panel underside front Z=31.9532 mm uses the .100-inch floor and
1.158-inch front height in section C-C. The latter is interpreted as a datum to
the panel underside; the separate .062-inch metal plate is extruded outward
along its normal.

The rear panel lower Z=6.2992 mm uses the explicit detail-D stack:
2.54-mm inner floor + .250-inch bottom-board boss - .102-inch groove offset.
The undimensioned rear-view silhouette appears to place the opening about
10 mm higher than the C-C/detail-D stack. This model uses detail D. This drawing
interpretation must be checked against a physical PT-10 before mechanical use.

## Generalized molded geometry

The front outer curve is traced from C-C; rear curves and 7-mm XY corner radii
are generalized. Side walls use the .100-inch (2.54-mm) nominal section.
The rear seam is at the printed 1.535-inch height; its front height is an
approximation. A 0.18-mm seam gap makes the two covers legible in Blender.

The four bottom bosses use the printed PCB hole grid and .250-inch height;
their outer diameter, bore diameter, and board centering are approximations.
The original molded tabs and panel screw clips are not modeled. The narrow
main-panel ledge and rear groove surround are visual approximations.

## Rebuild and validation

`build_pt10_case.py` rebuilds FCStd, STEP, STL, the mesh manifest, and source hash.
It uses the already installed FreeCAD Python runtime with no added dependency.
Both shells pass OpenCascade `isValid()`, and each exports as one solid.
The combined outer envelope matches the printed width, depth, and height.
Those checks establish valid reconstruction geometry, not factory fit,
collision-free assembly, fabrication accuracy, or component correctness.
