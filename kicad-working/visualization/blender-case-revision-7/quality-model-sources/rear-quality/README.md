# Detailed rear connector candidates

Two drawing-derived candidates cover the four SDS-50J DIN connectors and three NYS216 audio jacks. They are intended to replace earlier coarse body illustrations after review. Both complete STEP files include AP214 face colors, combined STL files and separate material/feature STLs. Editable FreeCAD documents are included. The actual PCB projects, existing assigned source models and delivered Blender scenes are untouched.

No authentic downloadable manufacturer STEP was recovered for these exact parts. Same Sky's MJ-3536N/PJ-202AH pages report their requested 3D model unavailable, the SDS-50J 3D page returns an error, and the visible SnapMagic download requires registration. REAN's exact NYS216 page publishes a detailed DXF and PDF but no STEP; STEP files for other NYS variants were not substituted. The source availability record includes the URLs and outcomes.

## SDS-50J / CP-2350

The candidate retains the full 20 × 15.8 × 21.1 mm envelope and 1.8 mm flange from the current manufacturer's SDS-J drawing, page 3. It adds a keyed mating cavity, elongated socket recesses, separate visible mating contact sleeves, rear cover steps and the lower relief. The contact centers follow the printed 7 mm PCD with 25°/45° orientations; the mounting holes retain the printed 19 mm circle and 1.6 mm hole diameter with the two lower holes 25° below horizontal.

The outer dimensions and printed patterns are authoritative nominal source dimensions. Cavity diameter, socket slot dimensions, small reliefs, rear-cover profile and contact axial depths are unsized reconstructions from the views. The current SDS-J drawing differs from the indexed historical 2005 CUI drawing in flange details; exact historical mold equivalence is unproven. Solder terminals and locators are omitted.

## NYS216

The primary manufacturer DXF identifies NYS216, drawing 3102 ST 22 01, with a 2004 original date and 2007 revision C. It shows a ribbed housing with three open contact windows and visible contact strips. The candidate uses those window/rib stations, a separate rear projection, mating bore and nominal 3/8-32 UNEF nose. Three visible leaf-contact strips illustrate the open housing; they do not reproduce every switched contact or the electrical terminal geometry. Nut and washer remain separate existing presentation hardware.

Printed nominal dimensions govern: 20 mm width, 33 ±0.5 mm overall axial length, 15.5 mm body height, 8.5 mm nose projection and 8 mm socket axis above the illustrated body datum. The drawing's 2:1 model-space geometry is normalized by 0.5 to physical millimetres; this is drawing calibration, not enclosure-fit scaling. Unsized raw geometry conflicts with some printed dimensions: its overall outline measures 33.75 mm, rib height 15.3 mm and drawn nose circle 10.5 mm, while the printed thread designation gives a 9.525 mm nominal major diameter. These conflicts are preserved in `source/nys216-feature-evidence.json`; the published dimensions govern the candidate.

The earlier 16.5 mm solid-box height and 11 mm nose were conservative or approximate envelopes. This improvement follows the actual body-height and thread callouts, and was not reduced to conceal a scene intersection. The official current product page gives 8.2 mm distance to PCB while the drawing axis is 8 mm; actual seating feet/gap remain unmeasured. Circular grooves illustrate the 32 TPI pitch, with no true helical thread or tolerance claim. Window depth, sheet stock and contact curvature are unsized reconstructions.

## Coordinates, validation and integration

Every candidate uses the original F.Cu footprint frame: X is footprint X, Y is negative footprint Y, Z is outward from the component side, and dimensions are millimetres. The connector front shoulder/flange is Y=0 and the body extends into +Y. No board placement, case transform, side flip or installed seat is baked in. Planned native assignment offset/rotation are zero and scale is unity.

`rear-quality-manifest.json` provides two complete STEP assignments in the same integration contract as previous reviews, per-segment STL data, source hashes, printed dimensions, improvements and limitations. All source and exported solids are valid. AP214 face coloring is checked by re-import: the exact uncolored and colored BRep serializations are equal. The two combined meshes contain 175,970 triangles in total, preserving the higher-detail openings and nose grooves. The candidate review render is a standalone artifact; it does not establish terminal, panel, harness or enclosure fit.

Generated reconstruction geometry is CC0-1.0. Manufacturer source documents retain their own rights. These candidates are detailed sourced illustrations, not recovered manufacturer CAD or physically qualified replacements.

Standalone front/rear contact-sheet review passed. Isolated native KiCad probes loaded both complete STEP files and exported all component primitives with their assigned face colors: three SDS50J palette colors and two NYS216 palette colors. These checks confirm readable geometry/material payloads, not assembly fit.
