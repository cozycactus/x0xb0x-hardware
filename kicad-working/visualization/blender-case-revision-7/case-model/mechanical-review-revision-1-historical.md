# Assembly visualization review

The PacTec printed case/panel dimensions match the original x0xb0x panel outer
profiles. The 15-degree top slope and nominal case envelope are sourced from
manufacturer drawing 82232 revision C. Unsized molded detail and panel setbacks
remain reconstruction assumptions, documented in `pt10-datums.json`.

The initial shell cavity incorrectly extended the central sloped roof through
the curved front and rear shoulders. This created long artificial open slits.
The generator now follows the full shoulder profile at nominal wall thickness.
The corrected assembled preview visibly closes the front shoulder; the upper
cover remains one valid solid. Native board geometry and panel datums were not
changed by this correction.

A bounded read-only probe sampled **69,827 actual native board-model vertices**
in assembled frame 1 against the corrected case STL solids. Candidate points
were checked with two exit-normal rays and then confirmed by OpenCascade
`isInside()` against the reconstructed CAD solids. The report is
`case-clearance-review.json`, which records the Blender snapshot and STL hashes.

No sampled mainboard or component vertices were inside the case. There were
**14 confirmed sampled hits**, all on three I/O PCB rear-edge meshes, against
the approximated bottom rear groove support. The affected samples are near
X=+110.744 mm, Y=197.428 to 199.079 mm, Z=10.923 to 12.533 mm. The I/O PCB rear
outline currently reaches 0.584 mm beyond the chosen rear-panel outer face.
This reflects the chosen I/O depth and generalized groove surround; it does
not establish an error in the PCB source. The real connector-to-panel setback
and groove shape must be resolved for mechanical-fit use. Moving the visual
I/O board roughly 2.3 mm forward would avoid this assumed groove, but should
only be chosen as an explicit visualization placement assumption.

The rear panel cutouts themselves clear the modeled lower opening lip: the
lowest DXF cutout edge is 6.35 mm above the panel bottom, while the lower groove
overlap is 2.5908 mm. Mainboard PCB placement and its XY control/cutout
registration are reviewed separately in `../panels/`.

This is a sampled visualization check. It does not check every mesh triangle,
prove positive physical clearance, certify manufactured component models, or
resolve the original rear mounting-hole discrepancy of approximately 0.2455 mm.
