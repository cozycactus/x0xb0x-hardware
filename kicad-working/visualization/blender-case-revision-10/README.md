# x0xb0x assembly — Blender revision 10 / KiCad revision 11

Open `x0xb0x-populated-with-case.blend`. All 491 fitted components are embedded: 409 mainboard and 82 I/O. No external board exports are required to view the assembly. Revision 9 remains unchanged alongside this version for comparison.

## Audio mounting-nut refinement

Only the three exterior black PA6 mounting nuts for HEADPHONE, MIX OUT and MIX IN have new mesh geometry. They now have six SW15 wrench flats, a circular 17.5 mm rear flange, 1.5 mm flange thickness and 5 mm total depth, following the recovered manufacturer drawings. Their front corners have a smooth rounded transition to a circular front face, reflecting the visible manufacturer drawing and photograph. The 15 mm front-face diameter, 0.55 mm transition depth and sampled quarter-ellipse curve are explicit visual approximations; their exact radii and molding profile are not dimensioned.

The new flange, wrench body and rounded front are coaxial with the retained plain 9.6 mm bore. This shifts only the mesh exterior center approximately 0.082 mm to the native connector axis; each original object origin, stored matrix, material and source collection remains unchanged. Rear and front seating planes remain unchanged. The three 11.3 mm-bore washers are unchanged. Undimensioned rear radial features are omitted so no rib height or mounting-seat claim is invented.

The installed native NYS216 connector follows the recovered 2007 revision-C drawing with a 3/8-32 UNEF (9.525 mm major diameter) nose. The retained exterior hardware dimensions come from the 2015 drawing, which specifies M11. The 9.6 mm plain nut bore remains an illustrative clearance for the installed older nose. Thread geometry, historical nut identity, interchangeability and physical fit remain unqualified. Sources and exact parameter classifications are recorded in `../../validation/nys216-hardware-quality/`.

## Preserved assembly and views

All native connector bodies, bores, contacts and PCB geometry are unchanged. The five obsolete rear closing disks removed in revision 9 remain absent, and all eleven rear openings retain their intended cavities or contacts. All remaining scene geometry, shaders, component positions, labels, wiring, cameras and view animation are preserved. All 40 complete PCB-mounted LEDs and 23 PCB-attached button caps remain.

- Frame 1: assembled enclosure.
- Frame 80: exploded enclosure and boards; LEDs and caps follow the PCB.
- Frame 120: control-side inspection with panel and caps hidden.
- Frame 160: wiring study; physical routing and wire length remain qualified.

The rear camera is also available. All five standard views are refreshed, together with `rear-openings-closeup.png` and a mounting-nut detail. The additional diagnostic cameras exist only during rendering and are not saved into the scene.

## Verification and limits

`revision-10-change-record.json` records the three refined mesh signatures, source hashes, exact center shifts and preserved baseline. Independent saved-scene, geometry, rear-opening and portable-file checks are under `verification/`. The original panel drawings and design license remain at `../blender-case-revision-7/source/`.

KiCad remains revision 11. Its existing three connection gaps and board/parity warnings remain. Exact fitted parts, molding tolerances, spacer outlines, cap sockets/travel, installed lead forming and physical assembly remain unqualified. No connector-fit, routing or fabrication certification follows from this visual refinement.
