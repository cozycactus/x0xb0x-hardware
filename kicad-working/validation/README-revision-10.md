# x0xb0x KiCad working revision 10

This revision improves the 3D geometry for 45 fitted references: forty PCB-mounted LED assemblies, the photo-qualified bent-back IC20/KK1 pair, two MJ-3536N audio jacks and the PJ-202AH power jack. All 491 fitted references retain their visual models. Previous source assets, stable scenes and archives are preserved.

- Mainboard: `mainboard/mainboard.kicad_pro`
- I/O: `ioboard/ioboard.kicad_pro`
- Blender with case: `visualization/blender-case-revision-7/x0xb0x-populated-with-case.blend`
- Current model plan: `validation/models-review-10/combined-model-plan.json`
- Fresh checks: `validation/working-validation-summary.json`

The original author instructs bending IC20 back before fitting the heatsink. Original placement/soldering photos show its body extending approximately parallel to the PCB beyond the edge. The new rigid pair preserves the previous nominal full-size body and folded heatsink geometry; the exact 90 degree bend and 2 mm datum are explicit illustration assumptions. Capacitor-body interference from the previous upright alignment is removed in the modeled pair. Remaining free-state spring overlap is documented, not elastic-fit certification.

LED1–LED40 now have one complete PCB-mounted model each, with original generic head geometry, full-width extended leads and the BOM mounting length. The lenses pass through the panel holes and project approximately 1.3 mm above the modeled panel. The older sequencer 0.22 inch versus named STD240B 0.24 inch conflict remains qualified. Blender removes forty disconnected lens display pieces and attaches the 23 button caps to their PCB switches in the exploded view. The unlit clear lenses represent the red-emitting LEDs shown in the original assembly photographs; optical appearance is illustrative.

Rear jacks have detailed housings, cavities, bushings and visible contact illustrations from manufacturer drawings. Below-seat terminals remain omitted; original round drills differ from the published slot requirements and no terminal is thinned to conceal that limitation. The downloaded proprietary CAD research ZIP is excluded from portable delivery; delivered replacements are independent parametric reconstructions.

Every non-model PCB/library node, schematic, project setting, electrical pad/net/copper/routing, outline and footprint placement is unchanged. All model offsets, rotations and scales are unchanged. Existing PCB connection gaps, warnings and parity findings remain recorded. Nominal drawings and photographs do not establish actual fitted vendor, tolerances, lead forming or enclosure fabrication readiness.

Portable model assets use project-relative paths. Earlier documentation is retained in `validation/README-revision-9.md`. Original Eagle sources and the preservation import remain unchanged.

The saved Blender revision 7 passes 1,856 scene checks and 694 independent front-control checks. All 40 LED axes align with the original panel holes in the model, and all 23 caps retain their assembled geometry and positions. Actual spacer molding, cap retention and switch travel remain unmodeled. Use frame 1 for the assembled case and frame 80 for the exploded assembly; frames 120 and 160 intentionally hide the caps. The five rendered views were visually reviewed. Final live desktop inspection was unavailable because the Mac was locked; this limitation is recorded separately from the saved-file checks.
