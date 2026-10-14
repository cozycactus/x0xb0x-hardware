# x0xb0x assembly — Blender revision 7 / KiCad revision 10

Open `x0xb0x-populated-with-case.blend`. All 491 fitted native references are embedded (409 mainboard / 82 I/O). A separate inspection copy is used for the live GUI and excluded from delivery. Previous saved versions remain unchanged.

## This revision

LED1–LED40 are represented by one complete PCB-mounted assembly each. The nominal 5 mm head is raised from its stock 3 mm body datum to the original BOM STD240B 0.24 inch (6.096 mm) mounting length; full-width leads continue to the PCB/cut tails. The older sequencer 0.22 inch entry is recorded as a conflicting alternative. The official source CAD head has a 4.9 mm lens body and 5.8 mm lower flange, both preserved exactly. Each lens projects approximately 1.3 mm above the modeled panel. Supplied LED vendor, optical material and physical tolerances remain qualified. Forty disconnected red lens display pieces are removed. The 23 switch caps keep their assembled geometry and now follow their PCB switches when the board is exploded, while remaining hidden in frames 120 and 160 for inspection. The unlit clear-lens shader is illustrative; no electrical LED states or light output are simulated.

IC20 and KK1 now follow the original author's bent-back assembly instruction and original photographs. The complete prior regulator body/tab and full-size folded heatsink are rigidly reoriented; no body is shrunk or trimmed. The exact 90 degree bend and 2 mm vertical datum are installation illustration choices, not measured source dimensions. Native footprint and model transforms are unchanged. IC20 terminals remain omitted. The reconstructed free-state spring fingers retain a documented nominal regulator overlap, so physical spring clamping, thermal performance and tolerances remain unqualified.

CV0, GATE0 and POWER0 now have independent drawing-derived detailed molded housings, open cavities, bushings and visible contact illustrations. Published exterior envelopes remain full size. Undimensioned interior details remain explicitly approximate. Below-seat terminals are omitted: full nominal fit to the imported round drills is unqualified. No proprietary manufacturer CAD file is redistributed.

The source-family manifests, generators, drawings and audits are under `quality-model-sources`. The current 491-reference assignment plan is `board-meshes/source-model-plan.json`. Earlier source directories and reports remain historical evidence for previous geometries; use the current plan and revision-10 manifests to identify active assets. Some remaining rare parts still use qualified illustrations.

## Views

- Frame 1: assembled case.
- Frame 80: exploded boards and enclosure.
- Frame 120: control side with top plate and caps hidden.
- Frame 160: wiring routing study; length and physical fit remain unverified.

Case, panels, knobs, cap geometry/assembled positions, editable labels, board poses and all24study curves retain their previous geometry. The exploded cap attachment and removed lens doubles are the explicit front-control presentation changes. The obstacle screen is refreshed against current native models. J3 still exceeds the documented stock wire length. The detached historical I/O Dimension construction contour remains preserved and hidden.

## Verification and limitations

`verification` records save/reopen population, canonical source dimensions, unchanged component/PCB/case geometry, presentation poses, label and curve preservation, desktop inspection status and rendered views. The saved scene passes 1,856 checks; the independent front assembly audit passes 694 checks. Final live desktop inspection was unavailable because the Mac was locked. All five saved-scene rendered views were visually reviewed. Fresh KiCad ERC/DRC findings belong to working revision 10. Existing three connection gaps and board/parity warnings remain unchanged; no electrical design or rules were changed.

The original author photos correct the orientation assumption, but do not measure installed bend height, lead form or historical supplied vendor. Nominal source-body and case screens do not establish actual fitted tolerances. Enclosure dimensions and board seats remain reconstructed/qualified, not fabrication certification.
