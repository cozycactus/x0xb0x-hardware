# Blender revision23 — corrected Micro-Ohm PTC dimensions

Open `x0xb0x-populated-with-case.blend` with Blender5.2.2LTS. R100A0/R100B0 have the recovered Micro-Ohm LPTC12 body3.7x1.9mm and0.45mm leads. Fourteen existing part meshes change. All1721 objects,491 native references,40 LEDs,40 black spacers,23 caps, existing materials, case geometry, camera poses and animation are preserved. No scene objects or shaders are added.

The original10.16mm PCB lead spacing and component transforms remain. Body standoff, formed bends, cut tails and coating details remain documented illustrations. See `../../../docs/ptc-primary-dimension-correction.json` and the KiCad20 review for source and limits.

All491 models match fresh native KiCad exports. The saved scene passes10 preservation checks,106 portability checks,44 rear-opening checks/974 rays, and the existing25-reference/133-piece terminal-join check. All489 models with drilled holes pass declared fit allowances. The revised PTCs introduce no new external triangle contacts in121 nearby-mesh tests. Eleven known nominal fit findings and three electrical connection gaps remain unchanged.

Frames1 assembled,80 exploded,120 control-side,160 wiring study. `ptc-before.png` and `ptc-after.png` use the same camera and scale to show the correction; `ptc-installed.png` is a read-only diagnostic view with temporary inspection lighting. These checks do not qualify physical fit, tolerances, thermal contact or circuit operation.
