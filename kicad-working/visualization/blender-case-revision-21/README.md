# Blender revision21 — corrected Kobiconn USB

Open `x0xb0x-populated-with-case.blend` with Blender5.2.2LTS. This scene contains the complete case,491 native component references,40 LEDs and23 button caps. It retains all1681 objects and all existing placement, animation, cameras, case geometry and shaders from immutable revision20.

Only USB0's mesh is replaced with the four-part native KiCad revision18 export; one illustrative gold contact shader is added. The connector body has the drawing's0.38mm PCB standoff,2.91mm signal projections and3.72mm mounting-tab projections. The signal exits are insulated and clear the metal shell. See `../../../docs/usb-kobiconn-correction.json` for dimensions, source and assumptions.

Saved-scene preservation passes10 checks. All491 models match fresh native KiCad exports, portable-scene checks pass106 checks, rear-opening checks pass44 checks/974 rays, all489 models with drilled holes pass the declared drill-fit allowances, and the terminal join check retains25 references/133 pieces. A nearby-mesh comparison introduces no new contact objects. Nine rendered views were visually reviewed, including `usb-in-case.png` and `usb-underside.png`; rendering left the saved scene unchanged. Reports and replay scripts are in `verification/`.

This remains a nominal visualization. Eleven documented nominal terminal/drill fit findings and the pre-existing electrical gaps remain unresolved; no fabrication or physical assembly qualification is implied.
