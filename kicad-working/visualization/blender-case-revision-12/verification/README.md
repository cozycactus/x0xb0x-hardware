# Revision 12 independent saved-scene verification

The frozen revision 12 scene is `../x0xb0x-populated-with-case.blend`,
SHA256 `517da1343de66a3e3b5c4848c182bcd263cccca419d3601e5805e0d3402228e1`
(42,930,111 bytes). Its preserved revision 11 baseline has SHA256
`fc02d403f1bcac0aa98937fd29e5f8d77e01f69400104278ea512d36eea01ff9`.
Both saved files were freshly reopened in native Blender 5.0.0 and remain
byte-for-byte unchanged by this inspection.

The correction changes three editable FONT body strings. The independent
electrical classifier derives their functions from actual IO-board pad nets;
it reads neither generator mappings nor old panel labels.

| Connector | Revision 11 text | Revision 12 text | Electrical evidence |
| --- | --- | --- | --- |
| DIN1 | MIDI IN | MIDI OUT | Pin 5 through R13 to MIDI_OUT/J3.6; pin 4 through R14 to +5V |
| DIN2 | MIDI OUT | THRU | Pin 5 through R15 to the buffered MIDI_IN receiver node/Q50.2/J3.5; pin 4 through R18 to +5V |
| DIN3 | THRU | MIDI IN | Pin 4 through R19 to IC24.1; pin 5 to IC24.2, the 4N37 optocoupler input |
| DIN4 | SYNC | SYNC | Four signal pins through R21–R24 to DINSYNC1–DINSYNC4 |

`THRU` abbreviates MIDI THRU and `SYNC` abbreviates DIN SYNC. Actual evaluated
text origins align horizontally with the corresponding native DIN axes, and
each generated glyph is nearest its named port. The original binary Eagle
schematic was also freshly decoded: all 62 selected connected pad memberships
match the KiCad PCB. The evidence extract records the decoder/spec hashes,
source hash, original record indices and 24-byte record contents. Its portable
replay checks those bytes and memberships against the preserved binary and
current PCB. The broader original schematic/board source review is under
`../../../validation/din-midi-review/`.

The focused results are:

- **Saved-file preservation: PASS, 41 aggregate checks.** Complete compressed
  before/after snapshots cover all 1,661 stored objects and actual displayed
  instances in frames 1, 80, 120 and 160. Only the three named FONT bodies and
  their generated glyph meshes change. Every object pose, collection link,
  hierarchy, other geometry, material/shader, font resource, animation curve,
  camera, render setting and historical embedded guide is retained. Exactly
  the declared revision metadata and one new guide are added/updated.
- **Electrical legend regression: revision 11 fails exactly three labels;
  revision 12 passes all four.** `baseline-midi-legends-audit.json` is the
  intentionally failing baseline evidence. `midi-legends-audit.json` is the
  current passing result.
- **Actual glyph/panel geometry: PASS, 13 aggregate checks across 44 glyph
  poses.** All eleven glyph backs remain nominally 0.01 mm outside the panel;
  measured values are 0.01000813–0.01003984 mm with a 0.0001 mm numerical
  tolerance. Full extrusion remains 0.012 mm. The eight unchanged labels retain
  their actual in-plane bounds; the corrected strings retain their exact
  object/instance poses while their generated widths change.
- **Rear apertures: PASS, 44 checks and 974 rays across all eleven ports.**
  The unchanged repository checker includes native openings, audio hardware
  bores, DIN contacts, power annulus and USB passages; intended recessed backs,
  contact inserts and the USB tongue remain present.
- **Portability: PASS, 106 checks.** All 491 native reference assemblies
  (409 mainboard/82 IO), 40 native LEDs and 23 board-parented caps remain
  embedded, with zero unpacked external dependencies.
- **Delegated visual review: PASS, seven images.** The renderer reviewed five
  standard views and two focused rear diagnostics, and separately confirmed
  that rendering changed neither saved scene. The renderer owns
  `final-render-review.json` and `render-readonly-verification.json`.

With `use_auto_texspace` still enabled, Blender automatically recomputes each
changed FONT's texture-space XY location/size from its generated glyph bounds.
Those derived caches change with the body strings and are explicitly checked
against the actual local glyph vertices. Their normal components stay exact;
every editable font/style/material/textbox setting remains unchanged. This
accounts for the automatic data changes rather than treating cached bounds as
an unauthorized style edit. Character formatting remains uniform and exact
for the new text lengths. Every FONT datablock identity, user count and local
ownership is preserved; each corrected label has one data user.

These checks qualify the saved illustration, its connectivity-derived legend
meaning and sampled visual apertures. They do not certify physical assembly,
thread compatibility, plug insertion, soldering or fabrication. The previous
seating review remains unchanged: three audio bodies intersect the nominal
panel by 0.508 mm, and the nominal power/USB lower body envelopes clip their
cutouts by about 0.081 mm. Those are documented model/datum conflicts with
unqualified historical seating; this text correction makes no fit claim. The
editable typography is a presentation reconstruction, and the 0.01 mm display
gap is a rendering choice rather than physical ink thickness.

## Reproduce

Run from the repository root, replacing `blender` with the installed Blender
executable if needed. All commands inspect source/core files without writing
them. Audit scripts write only their verification evidence and never save a
scene. The `--python-exit-code 1` option makes failed Python assertions fail the
process.

```sh
blender --background --python-exit-code 1 --python kicad-working/visualization/blender-case-revision-12/verification/audit_saved_scene.py
blender --background --python-exit-code 1 --python kicad-working/visualization/blender-case-revision-12/verification/audit_legend_planes.py
blender --background kicad-working/visualization/blender-case-revision-12/x0xb0x-populated-with-case.blend --python-exit-code 1 --python kicad-working/visualization/blender-case-revision-12/verification/verify_midi_legends.py
blender --background kicad-working/visualization/blender-case-revision-12/x0xb0x-populated-with-case.blend --python-exit-code 1 --python scripts/verify_rear_openings.py
blender --background kicad-working/visualization/blender-case-revision-12/x0xb0x-populated-with-case.blend --python-exit-code 1 --python scripts/verify_blender_scene.py
```

Running `verify_midi_legends.py` with the preserved revision 11 scene must exit
nonzero and identify DIN1, DIN2 and DIN3. The default saved-file audit captures
fresh complete snapshots. Its optional `-- --reuse-snapshots` mode replays the
full equality comparison against those captured snapshots, freshly checks the
saved scene hashes and FONT ownership/functions, and preserves the snapshot
hashes in the result.

`derive_midi_functions.py` can replay the checked-in binary-record evidence
with standard Python. A complete fresh semantic decode additionally accepts
`--legacy-decoder <inspect_eagle_source.py>` and
`--parser-spec <eagle_bin_parser.cpp>` from the original import toolchain; those
external tools are optional and are not required by the portable replay. The
broader source review provides a separate portable binary verification.
