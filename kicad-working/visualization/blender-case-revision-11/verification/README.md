# Independent saved Blender revision 11 verification

Final scene SHA256: `fc02d403f1bcac0aa98937fd29e5f8d77e01f69400104278ea512d36eea01ff9` (42,928,643 bytes). Preserved revision 10 SHA256: `9c75786aa2ea7a551ef68ed0715c6ac8ef12455213dd24192e5a07f4d00f1d07`.

- **14,820 fresh saved-file preservation checks pass.** Exactly eleven rear legend object poses change, solely by translations along the shared rear-panel normal. No stored geometry, FONT data, material, shader, curve, camera, animation or other object pose changes. All 491 native components, 40 complete LEDs, 23 PCB-attached caps, case/panels and six audio hardware meshes remain unchanged.
- **185 actual glyph-plane checks pass** across 44 evaluated glyph poses in frames 1, 80, 120 and 160. The rear legend instancer and actual panel have identical evaluated poses. The backs of the unchanged glyphs lie at **0.010008..0.010040 mm** outside the saved panel surface, matching the nominal 0.01 mm target within float-transform precision. Maximum in-plane difference is 0.00000191 mm; the original 0.012 mm full glyph extrusion is retained.
- The unchanged reusable rear-opening verifier passes **44 checks / 974 raycasts** for all eleven ports. Intentional power pin, USB tongue and DIN inserts/contact bores remain present.

`audit_saved_scene.py` independently reopens both saved scenes and writes compact snapshots before comparing all stored objects and evaluated matrices in all four inspection frames. It permits only the eleven named normal translations, explicit revision metadata and one new guide. `audit_legend_planes.py` uses actual evaluated FONT vertices and actual saved panel vertices, rather than the nominal font location or source collection coordinates. FONT/MESH conversion representations are not counted as separate labels. Both inspections preserve the saved files.

The full rear seating audit is retained in `kicad-working/validation/rear-seating-review/scene-audit/README.md`. Its three 0.508 mm audio housing overlaps and POWER/USB 0.081 mm lower-slot clips remain **unchanged nominal illustration conflicts**. The label-only correction does not demonstrate a physical board misfit or resolve historical part identity/body-seat uncertainties. Physical fit remains unqualified.

Machine-readable evidence: `final-saved-scene-audit.json`, `rear-legend-plane-audit.json`, `rear-openings-audit.json` and `independent-validation-summary.json`. Rendering is verified separately and does not alter the saved scene.
