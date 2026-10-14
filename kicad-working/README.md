# x0xb0x KiCad working revision 11

This revision improves 26 fitted model references: the 24 historical 2SC536F transistors and the 6/16 MHz ceramic resonators. Both editable projects retain all 491 fitted visual models. Electrical connectivity, copper routing, footprint placement, drills, symbol libraries and project rules are unchanged.

- Mainboard: `mainboard/mainboard.kicad_pro`
- I/O: `ioboard/ioboard.kicad_pro`
- Current complete assembly: `visualization/blender-case-revision-12/x0xb0x-populated-with-case.blend`
- Current model plan: `validation/models-review-11/combined-model-plan.json`
- Source and model review: `validation/models-review-11/`
- Current validation: `validation/working-validation-summary.json`

## Historical transistor illustrations

The recovered Sanyo No.333H drawing in the 1985 semiconductor handbook distinguishes NP2003A (TO-92) from the smaller SP2000B. The BOM's TO-92 description and original near-square part photograph support a qualified NP family illustration; they do not establish every fitted vendor or mould revision. The F suffix is a gain rank, not a package identifier.

The models retain the drawing's typical 5 x 4 x 5 mm body and full 0.45 x 0.44 mm typical lead stock. Factory 1.3 mm exits are formed to the original PCB axes: 21 normal and three asymmetric positions. Original body seating, tail heights and all model transforms remain unchanged. Lead bends, unsized mould profiles and materials are illustrative. Typical dimensions are not maximum toleranced envelopes.

## Resonator illustrations

XTL1 and XTL2 retain their existing published maximum envelopes and complete leads. Taper and coated shoulders follow the Abracon outline's appearance; exact profile coordinates and radii remain undimensioned illustration choices. The original 2.54 mm pitch, 0.6 x 0.35 mm lead sections, seating, tail heights and XTL1's 180-degree mapping are preserved.

## Assembly and limits

The corrected 40 PCB-mounted LEDs and 23 PCB-attached button caps are preserved. Revision 8 retains the revision-7 case, panel, controls, editable labels, wiring curves, camera views and all other component geometry. Its source geometry is a documented composite of the preserved revision-7 assembly and the selected revision-11 native KiCad component meshes. Blender revision 9 removes five obsolete rear socket disks and opens six audio nut/washer meshes while preserving all native component geometry. Blender revision 10 refines only the three audio nut profiles using the manufacturer drawings and photograph; all rear opening corrections remain. Blender revision 11 places eleven rear legends on the plate while preserving the complete component and enclosure geometry. Its seating review records remaining nominal audio-housing and power/USB lower-edge intersections, with historical registration and physical fit unqualified. Blender revision 12 corrects the three MIDI legends from the original schematic and current PCB net topology: DIN1 OUT, DIN2 THRU, DIN3 IN. All four DIN connector models and poses remain unchanged. Source and CAD availability evidence is in `validation/din-midi-review/`. Earlier scenes remain available as baselines. These Blender-only changes are documented under `validation/rear-openings-review/`, `validation/nys216-hardware-quality/` and `validation/rear-seating-review/`; the KiCad projects remain revision 11.

The existing three PCB connection gaps and board/parity warnings remain documented. Models do not certify physical assembly, enclosure tolerances, cap travel, vendor identity or fabrication readiness. Earlier working notes are retained at `validation/README-revision-10.md`; original Eagle sources remain unchanged.
