# x0xb0x assembly — Blender revision 12 / KiCad revision 11

Open `x0xb0x-populated-with-case.blend`. All 491 fitted components are embedded: 409 mainboard and 82 I/O. No external board exports are required. Revision 11 remains unchanged alongside this version.

## MIDI legends matched to the circuit

Only three editable rear legend strings change. The electrical topology identifies DIN1 as MIDI OUT, DIN2 as MIDI THRU and DIN3 as MIDI IN. Their display text is now `MIDI OUT`, `THRU` and `MIDI IN`, respectively. DIN4 retains `SYNC` for DIN SYNC. The previous presentation had cycled the three MIDI labels onto the wrong sockets; the component positions and circuit itself were already unchanged.

Every font, size, extrusion, ink material, alignment, object position, rotation, scale, source collection and view animation is preserved. The actual glyph rear surfaces retain the nominal 0.01 mm display separation established in revision 11. This offset prevents coincident surfaces and is not a physical ink-thickness claim. The editable typography remains a presentation reconstruction, not recovered original panel silkscreen artwork.

## Preserved assembly and views

All native PCB and component geometry, connector bodies/contacts/bores, nuts, washers, enclosure, panel cutouts and wires are unchanged. All forty complete PCB-mounted LEDs and twenty-three PCB-attached button caps remain. All eleven rear openings retain their native cavities or contacts, and the rounded audio mounting nuts from revision 10 remain unchanged. No unretrieved internet DIN model has been imported.

- Frame 1: assembled enclosure.
- Frame 80: exploded enclosure and boards; LEDs and caps follow the PCB.
- Frame 120: control-side inspection with panel and caps hidden.
- Frame 160: wiring study; physical routing and wire length remain qualified.

The rear camera is also available. The five standard views, `rear-openings-closeup.png` and `rear-midi-detail.png` are freshly rendered from this saved scene. The additional diagnostic cameras exist only while rendering and are not saved in the scene.

## Verification and limits

`revision-12-change-record.json` records the exact before/after strings, unchanged style signatures and matrices, source hash and glyph separation checks. Independent electrical mapping, saved-scene, glyph-plane, rear-opening and portable-file checks are under `verification/`. The source investigation is under `../../validation/din-midi-review/`.

KiCad remains revision 11. Circuit geometry, placement, routing and existing validation findings are unchanged, including three recorded connection gaps. Inferred case/panel datums, historical connector seating, thread compatibility, fitted parts, molding tolerances, spacers, cap travel and physical assembly remain qualified separately. This label correction provides no physical-fit or fabrication certification.
