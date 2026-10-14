# Actual rear seating audit — preserved Blender revision 10

The rear panel is 1.5748 mm thick, with its **exterior at local normal Z = 0** and its interior at Z = -1.5748 mm. This is measured from the actual saved panel mesh. Its fitted circular/rectangular hole boundaries reproduce the retained original DXF dimensions. All eleven native connector axes were measured through actual evaluated collection instances, rather than source-collection coordinates.

The audit finds three separate kinds of nominal illustration conflict:

- The three audio jack housing shoulders project approximately **0.508 mm into solid panel material**. Exact-solver intersections of the saved triangle meshes measure about **101.9 mm³ per housing**. Their threaded nose, washer and nut remain open and the exterior stack is in contact. The .508 mm conflict comes from the current native model datum combined with the original footprint front offset; it does not establish that the historical physical PCB or supplied connector was wrong.
- The POWER and USB illustrated bodies extend **0.081 mm below their rectangular cutouts**, producing approximately **1.1480 mm³** and **1.5358 mm³** of nominal panel-material intersection. Their mating apertures remain clear. The generic USB center and both body seating datums are not qualified historical mechanical datums, so this does not justify changing the whole PCB height.
- All eleven rear legends sit **1.2440–1.2560 mm above the panel exterior**, explaining their visible floating shadows. This is a presentation placement defect independent of the connector seating uncertainties.

The three audio washer exteriors remain centered about **0.082 mm above their native bore axes**; their holes follow the native axes and the newer nut exteriors are coaxial. This small eccentricity is part of the retained illustrative washer geometry. No washer changes are made by this review.

| Port | Vertical axis minus cutout center (mm) | Native mating face outside panel (mm) | Shoulder beyond inner plane (mm) | Saved-mesh panel overlap (mm³) |
| --- | ---: | ---: | ---: | ---: |
| POWER0 | +0.5770 | +1.2192 | — | 1.1480 |
| HEADPHONE0 | -0.0820 | +7.4332 | +0.5080 | 101.9151 |
| MIXIN0 | -0.0820 | +7.4332 | +0.5080 | 101.9121 |
| MIXOUT0 | -0.0820 | +7.4332 | +0.5080 | 101.9121 |
| CV0 | +0.0850 | +1.4252 | +0.0000 | 0.0000 |
| GATE0 | +0.0850 | +1.4252 | +0.0000 | 0.0000 |
| USB0 | -0.6130 | +1.2192 | — | 1.5358 |
| DIN1 | -0.0632 | -1.5748 | +0.0000 | 0.0000 |
| DIN2 | -0.0632 | -1.5748 | +0.0000 | 0.0000 |
| DIN3 | -0.0632 | -1.5748 | +0.0000 | 0.0000 |
| DIN4 | -0.0632 | -1.5748 | +0.0000 | 0.0000 |

Positive mating-face values are outward projection; negative values are recess. For DIN, the flange front touches the panel interior while the opening is recessed by the panel thickness. For MJ/CV/GATE, the body shoulder touches the interior and the 3 mm bushing projects 1.4252 mm beyond the exterior. For POWER/USB, no unsupported seating shoulder is inferred from the rectangular front face. The USB "axis" is the existing generic envelope center, not a printed PCB-to-port datum.

The smallest clearance between the saved faceted panel hole and the MJ bushing envelope is approximately **0.0863 mm**; it is about **1.0540 mm** around each audio nose. DIN mating cavities have about **1.3991 mm** of margin to the saved polygonal plate openings. These are saved-mesh measurements; source DXF circles are smooth and actual manufacturing tolerances are unqualified. Horizontal axis errors are below 0.00002 mm numerical precision; the tabulated vertical offsets are deliberate/current illustrative registration differences.

The audio washers span Z = 0..1.2 mm and the nuts Z = 1.2..6.2 mm. Actual contact gaps are within roughly 0.00001 mm numerical precision. Each native nose ends at Z = 7.4332 mm, leaving about **1.2332 mm** beyond the nut front. If the same 8.5 mm nose shoulder were seated at the plate interior, the conditional stack 8.5 - 1.5748 - 1.2 - 5 would leave **0.7252 mm**. That arithmetic combines older nose and newer hardware illustrations; it is not a claim of thread interchangeability or an instruction to move the board.

All eleven native connector meshes were also screened against both saved enclosure meshes: **no material intersections were detected**. This concerns these eleven connector illustrations, not a complete physical-fit certification of the project.

Geometry measurements and Boolean evidence are in `rear-seating-audit.json`. Exact-solver Boolean results concern the stored triangle meshes, with a 0.01 mm³ threshold distinguishing substantial nominal intersections from coplanar float noise; they are not exact manufacturer BRep or toleranced physical measurements. The rear-opening verifier separately establishes the mating passages and should not be interpreted as proving housing seating.

Confidence is high for the positions, intersections, printed-panel thickness and visible legend offset of this saved scene. Confidence in an absolute physical correction remains limited by historical connector identity, omitted terminals/locators, body-seat details and the assumed enclosure/PCB assembly datums. The source review is in `../source-audit/README.md`.

No source scene, PCB, native model, component pose, enclosure, hardware or wiring was changed. Saved scene SHA256: `9c75786aa2ea7a551ef68ed0715c6ac8ef12455213dd24192e5a07f4d00f1d07`. The source bytes remain unchanged after inspection.
## Revision 11 follow-up

Blender revision 11 corrects only the eleven rear legend object translations. Their unchanged editable glyph geometry now starts approximately **0.01 mm outside the panel**, with actual geometry checked in all four inspection frames. The independent saved-file comparison confirms that every native connector, PCB, enclosure, hardware mesh and their poses remain unchanged. Therefore the native housing/panel intersection findings above also apply to revision 11 and remain explicitly qualified nominal illustration conflicts.

The correction does not move the I/O board, force a generic USB datum onto the historical board, alter the source panel holes or claim that the original physical assembly misfits. Independent revision 11 verification is in `kicad-working/visualization/blender-case-revision-11/verification/README.md` from the repository root.
