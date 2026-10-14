# Project-local component models

These files support this project's 3D view. Paths use `${KIPRJMOD}` and do not
require the original installed model library. Keep the complete project folder.

`KiCad/` contains unmodified official KiCad package models. The accompanying
license retains the KiCad library exception; original STEP headers and model
hashes preserve author/provenance information.

Most models are generic package illustrations rather than exact fitted parts.
They do not establish manufacturer series, body height, resistor color codes,
LED color, sockets, component standoffs, enclosure clearance or actual assembly.
See MODEL-PROVENANCE.json and the detailed project review for selections/limits.

`Project/` contains original CC0-1.0 parametric diode illustrations. Their body
and lead maxima use the linked primary Vishay package drawings; formed lead
spacing matches these boards exactly. Standoff, bends, cut tails and colors are
explicit illustration choices, not measurements of fitted parts. The generator
and dimensional record are included for reproducibility.

Revision5 adds qualified package illustrations supported by original BOM identities
and primary-authored package drawings. Nominal bodies, lead forming, standoffs,
colors and cut tails are explicitly documented in REVISION-5-SOURCES.json and
the review manifests. Some shared footprint libraries intentionally have no
model: their placed instances need different part-specific bodies, or include
an unresolved population alternative. Preserve these per-instance overrides
when updating footprints from libraries. No physical assembly fit is certified.

Known nominal model intersections in revision5: C25/C26, C26/C27, C41/R130. These concern
illustrated body/rim envelopes and mounting choices, not confirmed physical
faults. Exact parts, tolerances and fitted poses require review. Documented
dimensions and board placement are retained. See REVISION-5-INTERSECTIONS.json.

Revision6 populates fitted visual bodies using original BOM identities, published
nominal dimensions, and explicitly identified source-outline approximations.
Uncertain terminals and locators are omitted. Geometry, sources, assumed heights
and seating limitations are recorded in REVISION-6-SOURCES.json and manifests. Some shared footprint libraries intentionally have no
model: their placed instances need different part-specific bodies, or include
an unresolved population alternative. Preserve these per-instance overrides
when updating footprints from libraries. No physical assembly fit is certified.

Revision7 corrects control model surface colors without changing model geometry, nominal dimensions or any physical PCB design node. Historical body/terminal/seating limitations remain. Previous model assets are retained.

Revision8 replaces selected coarse models with detailed manufacturer CAD or drawing-derived reconstructions. Published dimensions and source limitations are recorded per model; PCB geometry and native assignment transforms are unchanged. Previous model assets are retained.

Revision9 replaces selected coarse models with detailed manufacturer CAD or drawing-derived reconstructions. Published dimensions and source limitations are recorded per model; PCB geometry is unchanged. The documented KK1 model-only seating exception, if present, changes only its 3Doffset; all other native assignment transforms are unchanged. Previous model assets are retained.

Revision10 replaces selected coarse models with detailed manufacturer CAD or drawing-derived reconstructions. Published dimensions and source limitations are recorded per model; PCB geometry is unchanged. All native assignment offsets, rotations and scales are unchanged. Previous model assets are retained.

Revision11 replaces selected coarse models with independent drawing-derived illustrations. Published dimensions, package-selection inferences and undimensioned details are recorded per model; PCB geometry is unchanged. All native assignment offsets, rotations and scales are unchanged. Previous model assets are retained.
