# x0xb0x hardware: KiCad and Blender

Private working repository for the x0xb0x Eagle-to-KiCad conversion and reconstructed enclosure assembly. Original design: **Copyright (c) Limor Fried & Adafruit Industries**. x0xb0x is an Adafruit trademark.

## Open the current projects

- [Mainboard — KiCad working revision 10](kicad-working/mainboard/mainboard.kicad_pro)
- [I/O board — KiCad working revision 10](kicad-working/ioboard/ioboard.kicad_pro)
- [Complete assembly — Blender revision 7](kicad-working/visualization/blender-case-revision-7/x0xb0x-populated-with-case.blend)
- [KiCad notes](kicad-working/README.md) and [Blender views and limitations](kicad-working/visualization/blender-case-revision-7/README.md)

Keep each complete project folder together: symbols, footprints and STEP models use project-relative paths. The Blender file embeds the populated boards and can be opened without the original workspace or external board exports. It was saved with Blender 5.0.0. The current KiCad projects were checked using KiCad 10.0.7.

![Assembled x0xb0x](kicad-working/visualization/blender-case-revision-7/assembled.png)

## What is included

- Both editable KiCad schematics and routed PCBs, project-local libraries and all 491 fitted component models.
- The original four Eagle files, byte-for-byte preserved under [original-eagle](original-eagle/).
- The corrected Blender enclosure, original panel DXFs, model generators, reference sources, attribution and verification reports.
- Complete PCB-mounted LED models at all 40 positions. Their lenses pass through the front panel; the earlier duplicate lens objects were removed.
- All 23 button caps attached to their PCB switches in the exploded view, with their assembled positions retained.
- The detailed rear jacks and photo-qualified bent-back regulator/heatsink arrangement.

Blender views: **frame 1** assembled, **frame 80** exploded, **frame 120** control-side inspection, **frame 160** wiring study. The caps are intentionally hidden in the two inspection views.

## Validation and known limits

The current saved scene passed 1,856 scene checks and 694 independent front-control checks. All five rendered views were visually reviewed. Both schematics passed ERC with zero errors and warnings under the recorded project rules. Existing PCB connection gaps remain at mainboard IC9.8/GND, mainboard S22.1/+5V and I/O MIXOUT0/GND; recorded DRC and schematic-parity warnings also remain. The 3D update did not alter the circuit, copper routing or footprint placement.

The LED height uses the BOM's named STD240B 0.24-inch spacer. An older assembly table says 0.22 inch; the discrepancy is documented. Exact spacer molding, button retention/travel, historical vendor variations, omitted terminals, reconstructed enclosure tolerances and the wiring study remain qualified. These files do not establish fabrication or physical assembly readiness.

Run `python3 scripts/verify_project.py` to verify the checked-in file hashes, 250 current KiCad project files, original Eagle sources and saved Blender scene. This is an integrity check; it does not rerun electrical or physical validation. The native audit/model-generation scripts retain historical source paths and may require macOS applications, source baselines or other tools; their recorded results are preserved as evidence.

Key reports: [working validation](kicad-working/validation/working-validation-summary-revision-10.json), [front controls](kicad-working/validation/models-review-10/front-controls-review/final-front-control-assembly-review.md), [saved-scene verification](kicad-working/visualization/blender-case-revision-7/verification/final-saved-scene-audit.json).

Delivery ZIPs, old Blender scenes, temporary native probes, local application state and redundant board GLB exports are excluded. The native GLB exports can be regenerated from the KiCad projects with `kicad-working/validation/models-review-10/export_quality_boards.py`; they are already embedded in the saved Blender scene.

## Sources and licensing

See [LICENSE.md](LICENSE.md) for asset-level attribution. Original documentation: [downloads](https://www.ladyada.net/make/x0xb0x/download.html), [parts list](https://www.ladyada.net/make/x0xb0x/fab/parts.html), [sequencer assembly](https://www.ladyada.net/wiki/x0x/sequencerfabrication). The original Eagle conversion used the existing cozycactus KiCad fork at commit `ac8691a64afa0a78d04f0073e82896bcdec82657`; no KiCad source change was required.

This repository starts with a snapshot of the current validated working files. Earlier local work is represented by the included provenance and reports, rather than an invented Git history.
