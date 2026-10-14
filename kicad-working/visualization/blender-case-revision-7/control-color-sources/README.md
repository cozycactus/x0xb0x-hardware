# Control STEP appearance correction

Six color-corrected STEP copies cover the same 34 control references as the preserved models-review-6 body illustrations. `control-color-manifest.json` supplies the parent integrator's `assignments[]` contract and `parts[]` records. No actual KiCad project, footprint library, delivered scene or original model is edited by this work.

The original control STEP files were exported by FreeCAD in headless mode without ViewObject appearance data. They contained no `COLOUR_RGB` or `STYLED_ITEM` entities. Native KiCad consequently exported their glTF primitives without material assignments, producing the default pale appearance. The other body families already contained working AP214 appearance data.

The corrected files append standard AP214 surface styles to the existing solid faces, using the source control manifest's material-role palette. Every original STEP entity remains verbatim unchanged. Geometry is not reexported or reconstructed. There is one corrected combined STEP per family, at the original scale, orientation and origin.

| Family | Instances | Palette roles in native KiCad GLB |
|---|---:|---|
| E-Switch TL1100F160Q | 23 | Dark housing/actuator; gray metal cover |
| Panasonic EVUF2LFL3 | 5 | Dark housing, sleeve and shaft |
| Alpha RV112BCF-40 | 2 | Dark housing, sleeve and shaft |
| CTS 290VAA5F201B2 | 1 | Gray case; lighter bushing/shaft |
| NKK B12AB | 1 | Gray bracketed housing envelope; dark bushing; lighter lever |
| Grayhill 25LB22-H | 2 | Dark housing, bushing, shaft and anti-turn tab |

The palette describes these original illustrations. Exact historical material finish is not established, and the existing NKK mixed-material housing remains one unsplit envelope. STEP diffuse color does not encode the separate Blender metallic/roughness suggestions.

`control-color-geometry-audit.json` proves all six files reload as valid geometry, retain the same exact BRep serialization, topology, volume and canonical bounds, and preserve every original STEP entity. The source files and input projects stayed unchanged during generation and validation.

`native-control-color-audit.json` records twelve native KiCad probes: original and corrected STEP on the same isolated one-reference PCB for each family. The probes preserve the selected actual footprint's side, position, angle and model pose; all six selected controls are B.Cu placements. The original and corrected exports have **byte-identical GLB binary geometry**, identical accessor/bufferView geometry data, identical primitive geometry metadata and identical component nodes/transforms. All corrected faces have explicit materials; all original faces lack materials.

Every native face palette and role's native mesh bounds passes. STEP palette values are sRGB; glTF base-color factors use linear RGB. The largest channel comparison error is approximately 1.05e-8. Geometry integrity is exact; the separate 0.02 mm mesh-bounds tolerance only accommodates circular tessellation chord extrema while checking material-role association.

`native-probes/` preserves the isolated PCB fixtures, exported GLBs and native export logs. Each export uses a separate output directory to avoid KiCad's shared temporary-name collisions. Original models and actual projects remain outside the writable probe set.

All source dimensions, original-F.Cu canonical coordinates, zero offsets/rotations, body-only classification, historical identity qualifications and seating limitations carry forward unchanged. This is an appearance correction and provides no additional terminal, seating, enclosure or fabrication qualification.

Project hashes are generation-time evidence, not a requirement that the active project remain at its preintegration revision. The parent integrator may subsequently install these validated appearance copies. That authorized model-path update does not change the preserved original/colored native probes or their geometry/color proof. Revalidation of these source assets uses the immutable probe files and STEP hashes; a subsequent populated board/scene audit establishes integration evidence separately.
