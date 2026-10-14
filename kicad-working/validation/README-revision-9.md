# x0xb0x KiCad working revision 9

This revision improves the 3D model geometry for nine fitted references: seven potentiometers, one full-size folded heatsink and the original Mitsubishi 2SC2291 package. All 491 fitted references remain modeled. Previous assets and deliverables are preserved.

- Mainboard: `mainboard/mainboard.kicad_pro`
- I/O: `ioboard/ioboard.kicad_pro`
- Blender with case (separate Blender delivery): `visualization/blender-case-revision-6/x0xb0x-populated-with-case.blend`
- Current model plan: `validation/models-review-9/combined-model-plan.json`
- Fresh checks: `validation/working-validation-summary.json`

Every non-model PCB/library node, schematic, project setting, electrical pad/net/copper/routing, outline and footprint placement is unchanged. All model offsets, rotations and scales remain unchanged. The proposed KK1 seating adjustment was rejected because it intersects the unchanged nearby capacitor models; installed heatsink seating remains unresolved. Actual mechanical fit, historical variants, pot terminals and Q22 formed/trimmed leads remain qualified per source record. No source body is reduced to clear the enclosure.

Portable assets use project-relative paths. Earlier documentation is retained in `validation/README-revision-8.md`. Original Eagle sources and preservation import remain unchanged.
