# x0xb0x assembly — Blender revision 11 / KiCad revision 11

Open `x0xb0x-populated-with-case.blend`. All 491 fitted components are embedded: 409 mainboard and 82 I/O. No external board exports are required. Revision 10 remains unchanged alongside this version.

## Rear legends seated on the panel

Only the eleven original rear legend objects move. They previously floated over 1.24 mm above the panel and cast visible detached shadows under the lettering. Each actual rear-most glyph surface now sits 0.01 mm outside the existing panel exterior, measured from evaluated glyph vertices against the actual panel normal. Their original FONT geometry, wording, font, size, extrusion, material, in-plane positions, rotations and scales are preserved. The 0.01 mm separation is a display choice to avoid coincident surfaces; it is not a claim about physical ink thickness.

The rear legend instancer already follows the original panel in all four views. Its ownership and animation remain unchanged. No duplicated text object was removed: the paired evaluated FONT and MESH records are representations of each one original editable FONT object.

## Preserved assembly and views

Every component, PCB, connector body/contact/bore, nut, washer, case, panel cutout, wire, label shape, camera and existing animation remains unchanged. All 40 complete PCB-mounted LEDs and 23 PCB-attached button caps remain. The rounded audio mounting nuts from revision 10 retain their documented dimensions and illustrative front profile. All eleven rear openings retain their native cavities or contacts; the five obsolete closing disks removed in revision 9 remain absent.

- Frame 1: assembled enclosure.
- Frame 80: exploded enclosure and boards; LEDs and caps follow the PCB.
- Frame 120: control-side inspection with panel and caps hidden.
- Frame 160: wiring study; physical routing and wire length remain qualified.

The rear camera is also available. The five standard views and `rear-openings-closeup.png` are refreshed from this saved scene. Diagnostic cameras exist only during rendering.

## Verification and limits

`revision-11-change-record.json` records every original and resulting legend surface gap, matrix, unchanged FONT signature and four-view panel ownership check. Independent saved-scene, rear-opening and portable-file checks are under `verification/`. The baseline investigation is `../../validation/rear-seating-review/presentation-audit/`.

KiCad remains revision 11. Circuit geometry, placement, routing and existing validation findings are unchanged, including three recorded connection gaps. Inferred case/panel datums and historical native connector seating remain qualified separately; this presentation correction does not force uncertain connector shoulders onto one plane. Historical thread compatibility, fitted parts, molding tolerances, spacers, cap travel and physical assembly remain unqualified.
