# x0xb0x assembly — Blender revision 8 / KiCad revision 11

Open `x0xb0x-populated-with-case.blend`. All 491 fitted components are embedded: 409 mainboard and 82 I/O. No external board exports are required to view the assembly. The original revision-7 scene is retained alongside this version for comparison.

## Updated models

Twenty-four 2SC536F transistor positions now use qualified historical Sanyo NP2003A family illustrations. The recovered No.333H drawing gives a typical 5 x 4 x 5 mm body and 0.45 x 0.44 mm lead stock; these are typical dimensions, not maximum toleranced envelopes. The original BOM's TO-92 description and near-square photograph support the package choice, without proving the exact fitted vendor or mould. Twenty-one normal and three asymmetric lead forms retain their PCB axes, model transforms, body seating and tails. Installed bends and unsized cosmetic details remain illustrative.

The 6 MHz and 16 MHz resonators have refined taper and coated lead shoulders. Their existing published maximum body envelopes, complete leads, mounting datum, 2.54 mm pitch and pin order are unchanged. Exact shoulder profiles, radii and colors remain undimensioned illustrations.

The new plastic/epoxy bodies are nonmetallic and their leads metallic. Roughness and optical appearance are presentation choices. Source drawings, generators, licenses and geometry reviews are under `../../validation/models-review-11/`. Current native assignment provenance is `board-meshes/source-model-plan.json`.

## Preserved assembly

Only the selected 26 component mesh subtrees were replaced from fresh native KiCad exports. All 491 original component roots and their transforms remain. The other component geometry, enclosure, panels, knobs, 23 button caps, editable labels, wires, cameras and view animation are preserved. All 40 complete PCB-mounted LED assemblies and their clear unlit shaders remain unchanged; duplicate panel lenses are not reintroduced.

The native source collections retain historical names and identities. Their current geometry is explicitly recorded as a composite of the preserved revision-7 assembly and the selected revision-11 native component meshes, rather than a byte-identical import of a new whole-board GLB.

## Views

- Frame 1: assembled enclosure.
- Frame 80: exploded enclosure and boards; LEDs and caps follow the PCB.
- Frame 120: control-side inspection with the panel and caps hidden.
- Frame 160: wiring study with caps hidden; physical routing and wire length remain qualified.

The rear camera is also available. The saved five views are `assembled.png`, `rear.png`, `exploded.png`, `control-side.png` and `wiring-study.png`.

## Verification and limits

`verification/final-saved-scene-audit.json` compares both saved scenes, including unchanged object geometry, shaders, curves, source roots, animation and actual displayed poses. `revision-8-change-record.json` records every native replacement and source hash. The original front and rear panel drawings and design license remain at `../blender-case-revision-7/source/`.

Fresh KiCad revision-11 ERC/DRC findings are recorded separately. Electrical geometry and rules are unchanged; the existing three connection gaps and board/parity warnings remain. Exact spacer molding, cap sockets/travel, historical fitted parts, installed lead forming, enclosure tolerances and physical assembly remain unqualified. No wire-routing or fabrication certification follows from this visual update.
