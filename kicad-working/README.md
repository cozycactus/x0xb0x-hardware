# x0xb0x KiCad working revision 15

This revision gives 24 terminals of six models formed legs, so every drawing-derived terminal joins its body (15 references). Revision 14 corrected four terminal models against their drawings (12 references). Revision 13 added terminals to the 12 component models that had none: 25 placed references across both boards. Revision 12's corrected SDS-50J contact pattern and revision 11's historical transistor and resonator illustrations are preserved. Both editable projects retain all 491 fitted visual models. Electrical connectivity, copper routing, footprint placement, drills, model transforms, symbol libraries and project rules are unchanged.

- Mainboard: `mainboard/mainboard.kicad_pro`
- I/O: `ioboard/ioboard.kicad_pro`
- Current complete assembly: `visualization/blender-case-revision-18/x0xb0x-populated-with-case.blend`
- Current model plan: `validation/models-review-15/combined-model-plan.json`
- Source and model review: `validation/models-review-15/` (formed legs), `validation/models-review-14/` (corrections) and `validation/models-review-13/` (terminals)
- Current validation: `validation/working-validation-summary.json`

## Terminals joined to their bodies

In six models, 24 terminals stopped just above the seat, 0.03–2.4 mm beside the body: the Alpha and Panasonic pot pins, the CTS encoder terminals, the NKK bracket legs, SDS-50J pins 4–5 and the MJ-3536N tip and shunt. The drawings show these terminals leaving the base edge and turning down. Each now has a formed leg with its own section, running into the nearest body edge; leg height and bend are assumptions. All 62 terminals of the 12 models join their bodies, and `scripts/verify_terminal_joins.py` checks this on the native export. Only 15 PCB model paths and six footprint-cache paths change. Fresh ERC is clean, and both DRC reports equal revision 14.

## Terminal corrections

An independent source review of revision 13's 19 nominal hole conflicts found four models that did not follow their drawings. The Alpha and Panasonic overall tab dimensions run across the outer slot edges, so the tabs now sit at ±5.5 and ±4.50 mm, matching Eagle. PJ-202AH terminal 2 is 2.50 mm wide, and the SDS-50J pin sections follow the period CUI drawing (rev D, 2006), retained in `validation/models-review-14/terminal-quality/sources/`. The conflicts fall to 11: the NYS216 rows (unresolved, 0.35 mm), the USB board-lock press fit, PJ-202AH terminal 3 and SDS-50J pins 1 and 2 at Eagle's grid positions. Only 12 PCB model paths and four footprint-cache paths change. Fresh ERC is clean and both DRC reports equal revision 13.

## Drawing-derived terminals

Every fitted model now has a lead in every drilled hole, except the four Grayhill bracket holes, whose legs the drawing does not define. Terminal positions come from the NYS216, SDS-50J, MJ-3536N, PJ-202AH, USB-B, TO-220, CTS 290, Alpha, Panasonic, NKK and Grayhill drawings in each model frame and were not moved to the pads. Previous body solids are retained exactly, and the assembly models keep their named parts. Thicknesses, bends and some widths are labelled assumptions; the LPTC thermistor leads have no manufacturer data.

A native audit cuts every terminal at both board faces against the real drills and records 19 nominal interferences where a drawing and the footprint disagree, in the NYS216, SDS-50J, USB, PJ-202AH, Alpha and Panasonic models. Neither source was altered to fit. Only 25 PCB model paths and the 12 matching footprint-cache model paths change. Fresh ERC on both boards has zero errors and warnings, and both DRC reports equal the previous fresh reports. The evidence is in `validation/models-review-13/`.

## Corrected DIN contacts

The SDS-50J front drawing places the two outer contact centers on the horizontal diameter. Its 25-degree leaders describe the elongated slot tilts; the previous model mistakenly used those angles for their center positions. The corrected model preserves the housing, rear cover, three lower contacts, nominal envelope and all footprint transforms. Only the four PCB model paths and the matching footprint cache model path change. Source, solid and native export evidence is recorded in `validation/models-review-12/`.

The downloaded Warehouse CAD is retained in separate local case comparison scenes. Its flange dimensions and body-to-pin registration differ from the current drawing and PCB. A rigid nominal pin-fitting shift causes a 0.12 mm flange overlap with the existing panel. That geometry has not replaced the active drawing-derived STEP model.

In revision 12, fresh I/O ERC had zero errors and warnings under the retained rules, and all I/O DRC finding lists exactly equalled revision 11.

## Historical transistor illustrations

The recovered Sanyo No.333H drawing in the 1985 semiconductor handbook distinguishes NP2003A (TO-92) from the smaller SP2000B. The BOM's TO-92 description and original near-square part photograph support a qualified NP family illustration; they do not establish every fitted vendor or mould revision. The F suffix is a gain rank, not a package identifier.

The models retain the drawing's typical 5 x 4 x 5 mm body and full 0.45 x 0.44 mm typical lead stock. Factory 1.3 mm exits are formed to the original PCB axes: 21 normal and three asymmetric positions. Original body seating, tail heights and all model transforms remain unchanged. Lead bends, unsized mould profiles and materials are illustrative. Typical dimensions are not maximum toleranced envelopes.

## Resonator illustrations

XTL1 and XTL2 retain their existing published maximum envelopes and complete leads. Taper and coated shoulders follow the Abracon outline's appearance; exact profile coordinates and radii remain undimensioned illustration choices. The original 2.54 mm pitch, 0.6 x 0.35 mm lead sections, seating, tail heights and XTL1's 180-degree mapping are preserved.

## Assembly and limits

The corrected 40 PCB-mounted LEDs and 23 PCB-attached button caps are preserved. Revision 8 retains the revision-7 case, panel, controls, editable labels, wiring curves, camera views and all other component geometry. Its source geometry is a documented composite of the preserved revision-7 assembly and the selected revision-11 native KiCad component meshes. Blender revision 9 removes five obsolete rear socket disks and opens six audio nut/washer meshes while preserving all native component geometry. Blender revision 10 refines only the three audio nut profiles using the manufacturer drawings and photograph; all rear opening corrections remain. Blender revision 11 places eleven rear legends on the plate while preserving the complete component and enclosure geometry. Its seating review records remaining nominal audio-housing and power/USB lower-edge intersections, with historical registration and physical fit unqualified. Blender revision 12 corrects the three MIDI legends from the original schematic and current PCB net topology: DIN1 OUT, DIN2 THRU, DIN3 IN. That revision preserved all four DIN connector models and poses. Source and CAD availability evidence is in `validation/din-midi-review/`. Earlier scenes remain available as baselines. These Blender-only changes are documented under `validation/rear-openings-review/`, `validation/nys216-hardware-quality/` and `validation/rear-seating-review/`; they preserved the KiCad revision-11 projects. Blender revision 13 applies the four native KiCad12 DIN mesh corrections while retaining every other object and all four inspection poses. Blender revision 14 seats the rear plate on the original Eagle I/O Dimension-strip datum, 0.508 mm behind the PCB edge at the three REAN footprint origins, by moving only the I/O board placement; the audio shoulders now seat on the plate and the KiCad projects are unchanged. Its evidence is under `visualization/blender-case-revision-14/verification/`. Blender revision 15 raises the same placement 0.081 mm onto the original rear-DXF height datum, 0.250 in above the plate's lower edge, with the three audio nuts following the jack axes; the POWER/USB bodies now rest on their cutout edges. Its evidence is under `visualization/blender-case-revision-15/verification/`. Blender revision 16 applies the KiCad13 terminal-completed meshes at the 25 references, adding 14 terminal part objects and one tin material while preserving every other object, pose and view. Its evidence is under `visualization/blender-case-revision-16/verification/`. Blender revision 17 applies the four KiCad14 terminal corrections by replacing 12 mesh datablocks; no object or material is added. Its evidence is under `visualization/blender-case-revision-17/verification/`. Blender revision 18 applies the KiCad15 formed terminal legs by replacing 15 mesh datablocks; no object or material is added. Its evidence is under `visualization/blender-case-revision-18/verification/`.

The existing three PCB connection gaps and board/parity warnings remain documented. Models do not certify physical assembly, enclosure tolerances, cap travel, vendor identity or fabrication readiness. Earlier working notes are retained at `validation/README-revision-10.md`; original Eagle sources remain unchanged.
