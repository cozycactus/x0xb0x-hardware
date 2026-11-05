# x0xb0x KiCad working revision 30

Revision30 puts two SC-59 chips on the mainboard, Q128 and Q139, next to the rare JFETs Q28 and Q39, which are now marked do-not-place. The holes stay. Every original pad, track, via and drill still matches the Eagle board. Nothing has been built or measured. Blender revision 28 doesn't have these two chips yet. See `smd-sites/README.md`.

Revision29 puts four SOT-363 chips on the mainboard, Q112, Q121, Q122 and Q126, next to the rare SIP pairs Q12, Q21, Q22 and Q26, which are now marked do-not-place. The holes stay. Every original pad, track, via and drill still matches the Eagle board. Nothing has been built or measured. Blender revision 28 has the chips and leaves those pairs out. See `smd-sites/README.md`.

Revision28 redraws both schematics by hand as sets of A3 sheets, one per block: nine for the mainboard and three for the I/O board. Every pin is on the same net as on the board copper and in the original Eagle schematic, with the same names. The board files change only in the `path` lines that link footprints to symbols; copper, nets, placement, models and Gerbers are unchanged. See `schematic-redraw/README.md`.

Revision27 refills the two mainboard F.Cu ground pours, whose saved fill still cleared the SIP9 pads as they were before revision 26 lengthened them and touched 23 of them, and moves the four I/O rear-plate datum lines from Edge.Cuts, where they formed a second board outline, to Dwgs.User. Only the pours' filled polygons and the four lines' layer change; DRC now checks the copper as saved. Order packages for both boards are in `fabrication/revision-27/`. See `validation/models-review-27/`.

Revision26 gives the 27 SIP9 pads of IC14, IC15A and IC15B Eagle's restrung and elongated 1.408x2.816mm size, and places the reference labels of the 461 parts with an Eagle smashed name record at that record's position, rotation, size and layer. The 11 references KiCad ends with 0 keep their reference, hidden, and print the Eagle name through a footprint text. Drills, tracks, vias, nets, zones, placement, models and schematics are unchanged. See `validation/models-review-26/`.

Revision25 compares both boards' Gerbers and drills with the original Eagle 4.13 boards and declares the internal 1-2/3-4 strips of the 23 B3F-40XX switches as KiCad jumper pad groups. Through S19 and S22 those strips close the recorded S22 +5V gap; the two remaining GND gaps are the original's drawn ground splits, joined through the J3-J7 wiring. Copper, pads, drills, nets, zones, placement, models and the I/O project are unchanged. See `validation/models-review-25/`.

Revision24 prints the part markings of the17 ICs, transcribed from the kit photographs, on the unchanged chip models. Revision23 seats IC3 and IC2 in their original-BOM TE DIP sockets (manufacturer models) with the KiCad chips resting on top. Revision22 gives all212 fixed resistors the original kit's colour bands from the parts page (tan5%, light-blue1%) on the unchanged KiCad DIN0207 bodies; footprint caches and PCB values are unchanged. Revision21 gives all39 radial electrolytics Xicon XRL bodies from the XRL datasheet and the original kit photographs (5x11, 6.3x11 and10x12.5mm cans) with leads on the original2.54/5.08mm holes; C17 and C3/C5 are recoloured only. Revision20 corrects both PTCs from the recovered Micro-Ohm LPTC12 family page to3.7x1.9mm bodies and0.45mm leads. Original PCB spacing and model transforms remain. Revision19 adds40 VCC STD240B black spacers beneath the unchanged LED bodies and leads, from the detailed manufacturer drawing. The6.096mm seat and all existing LED transforms remain unchanged. Revision18 corrects USB0 to the recovered original-BOM Kobiconn154-2442-E drawing: body0.38mm above PCB, signal projection2.91mm, board-lock projection3.72mm, insulated signal exits and illustrative gold mating strips. Revision17's TL1100F metal leg colours are preserved. Revision 16 rebuilt the Grayhill 25L rotary switches (S3, S4) from their drawing and a product photograph. Revision 15 gave 24 terminals of six models formed legs, so every drawing-derived terminal joins its body (15 references). Revision 14 corrected four terminal models against their drawings (12 references). Revision 13 added terminals to the 12 component models that had none: 25 placed references across both boards. Revision 12's corrected SDS-50J contact pattern and revision 11's historical transistor and resonator illustrations are preserved. Both editable projects retain all 491 fitted visual models. Electrical connectivity, copper routing, footprint placement, drills, model transforms, symbol libraries and project rules are unchanged.

- Schematic PDFs: `schematic-redraw/mainboard-schematic.pdf`, `schematic-redraw/ioboard-schematic.pdf`
- Mainboard: `mainboard/mainboard.kicad_pro`
- I/O: `ioboard/ioboard.kicad_pro`
- Current complete assembly: `visualization/blender-case-revision-28/x0xb0x-populated-with-case.blend`
- Current model plan: `validation/models-review-24/combined-model-plan.json`
- SIP9 pads and name labels: `validation/models-review-26/`
- Fabrication packages (order-ready): `fabrication/revision-30/`
- Adapters for the rare dual transistors at Q12, Q21, Q22 and Q26: `adapters/ssip5-dual/` (not yet built)
- Pour refill and I/O outline: `validation/models-review-27/`
- Fabrication comparison and connection gaps: `validation/models-review-25/`
- Source and model review: `validation/models-review-24/` (IC markings), `validation/models-review-23/` (IC sockets), `validation/models-review-22/` (resistor bands), `validation/models-review-21/` (XRL electrolytics), `validation/models-review-20/` (PTC dimensions), `validation/models-review-18/` (USB drawing correction), `validation/models-review-17/` (TL1100F colours), `validation/models-review-16/` (Grayhill rebuild), `validation/models-review-15/` (formed legs), `validation/models-review-14/` (corrections) and `validation/models-review-13/` (terminals)
- Current validation: `validation/working-validation-summary.json`

## USB BOM drawing correction

The user recovered Mouser KC-301021 (2006-07-19) for the original BOM connector. The previous illustration mixed Kobiconn body dimensions with FCI terminal lengths. The new model retains its printed outer dimensions and original XY axes while correcting the vertical dimensions. Four signal-pin solids previously intersected the metal shell floor; clearances and insulating exits now separate them. Their stock, exit skirts, mounting-fork shape and gold mating-strip dimensions remain illustrative. Original PCB pads, drills, copper, placement and model transforms are unchanged; only the USB0 model and its cache path change. See `validation/models-review-18/`.

## TL1100F leg colours

The publisher's TL1100F CAD is one grey solid. Revision 8 coloured its faces by position and left the leg faces that rise above the board, outside the 12 × 12 mm housing, black. Those 24 faces per switch now use the terminal colour; the B-rep is byte-identical, and KiCad's own export confirms the colours on all 23 switches. Only 23 PCB model paths and one footprint-cache path change.

## Grayhill 25L rebuild

A photograph of the 25L hex-output part showed a round drum top over the square base, two lock lugs, a white `8 4 2 1 C` label band, and a green output board with soldered pins. The drawing's front view puts the non-turn tab on the centre line opposite the pins. The body is rebuilt with those features, keeping every printed dimension and the pins. The four MT holes stay empty: they serve the optional 25J5155 bracket, and the BOM part 25LB22-H has no `-Z` bracket suffix. Only two PCB model paths and one footprint-cache path change. Fresh ERC is clean, and both DRC reports equal revision 15.

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

The corrected 40 PCB-mounted LEDs and 23 PCB-attached button caps are preserved. Revision 8 retains the revision-7 case, panel, controls, editable labels, wiring curves, camera views and all other component geometry. Its source geometry is a documented composite of the preserved revision-7 assembly and the selected revision-11 native KiCad component meshes. Blender revision 9 removes five obsolete rear socket disks and opens six audio nut/washer meshes while preserving all native component geometry. Blender revision 10 refines only the three audio nut profiles using the manufacturer drawings and photograph; all rear opening corrections remain. Blender revision 11 places eleven rear legends on the plate while preserving the complete component and enclosure geometry. Its seating review records remaining nominal audio-housing and power/USB lower-edge intersections, with historical registration and physical fit unqualified. Blender revision 12 corrects the three MIDI legends from the original schematic and current PCB net topology: DIN1 OUT, DIN2 THRU, DIN3 IN. That revision preserved all four DIN connector models and poses. Source and CAD availability evidence is in `validation/din-midi-review/`. Earlier scenes remain available as baselines. These Blender-only changes are documented under `validation/rear-openings-review/`, `validation/nys216-hardware-quality/` and `validation/rear-seating-review/`; they preserved the KiCad revision-11 projects. Blender revision 13 applies the four native KiCad12 DIN mesh corrections while retaining every other object and all four inspection poses. Blender revision 14 seats the rear plate on the original Eagle I/O Dimension-strip datum, 0.508 mm behind the PCB edge at the three REAN footprint origins, by moving only the I/O board placement; the audio shoulders now seat on the plate and the KiCad projects are unchanged. Its evidence is under `visualization/blender-case-revision-14/verification/`. Blender revision 15 raises the same placement 0.081 mm onto the original rear-DXF height datum, 0.250 in above the plate's lower edge, with the three audio nuts following the jack axes; the POWER/USB bodies now rest on their cutout edges. Its evidence is under `visualization/blender-case-revision-15/verification/`. Blender revision 16 applies the KiCad13 terminal-completed meshes at the 25 references, adding 14 terminal part objects and one tin material while preserving every other object, pose and view. Its evidence is under `visualization/blender-case-revision-16/verification/`. Blender revision 17 applies the four KiCad14 terminal corrections by replacing 12 mesh datablocks; no object or material is added. Its evidence is under `visualization/blender-case-revision-17/verification/`. Blender revision 18 applies the KiCad15 formed terminal legs by replacing 15 mesh datablocks; no object or material is added. Its evidence is under `visualization/blender-case-revision-18/verification/`. Blender revision 19 applies the KiCad16 Grayhill rebuild at S3 and S4. Its evidence is under `visualization/blender-case-revision-19/verification/`. Blender revision 20 applies the KiCad17 TL1100F leg colours to 23 meshes. Its evidence is under `visualization/blender-case-revision-20/verification/`.

Blender revision21 applies the corrected USB native geometry to the one preserved USB mesh object. A gold shader is the only added material; all other objects, poses, materials and geometry are preserved.

The board/parity warnings remain documented; revision25 settles the three PCB connection gaps. Models do not certify physical assembly, enclosure tolerances, cap travel, vendor identity or fabrication readiness. Earlier working notes are retained at `validation/README-revision-10.md`; original Eagle sources remain unchanged.

Blender revision22 adds only40 spacer meshes and one black thermoplastic shader. All1681 previous objects, optical materials, poses and animation are preserved; evidence is in `visualization/blender-case-revision-22/verification/`.

Blender revision23 replaces only14 PTC part meshes. Source dimensions and assumptions are in `validation/models-review-20/`; saved-scene preservation is in `visualization/blender-case-revision-23/verification/`.

Blender revision24 replaces only the39 electrolytic part meshes and adds four XRL materials. Sources, sizes and assumptions are in `validation/models-review-21/`; saved-scene preservation and the recorded C8/TM6 contact are in `visualization/blender-case-revision-24/verification/`.

Blender revision25 replaces only the212 resistor part meshes (outlines unchanged) and adds twelve body and band materials. Band sources and checks are in `validation/models-review-22/`; saved-scene preservation is in `visualization/blender-case-revision-25/verification/`.

Blender revision26 replaces only the IC3 and IC2 part meshes and adds two socket materials. Socket sources and checks are in `validation/models-review-23/`; saved-scene preservation and the neighbour screen are in `visualization/blender-case-revision-26/verification/`.

Blender revision27 replaces only the17 IC part meshes and adds one ink material. Marking sources and checks are in `validation/models-review-24/`; saved-scene preservation is in `visualization/blender-case-revision-27/verification/`.

Blender revision28 adds the four KiCad29 chips, removes the do-not-place SIP pairs Q12, Q21, Q22 and Q26, replaces the eight mainboard layer meshes with a fresh export, and adds three chip materials. All other objects, the I/O board layers and every pose are preserved. Saved-scene preservation, the layer audit and the neighbour screen are in `visualization/blender-case-revision-28/verification/`.
