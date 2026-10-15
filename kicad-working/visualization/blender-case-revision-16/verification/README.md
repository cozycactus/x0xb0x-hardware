# Saved revision-16 checks

`run_verification.sh` regenerates every report, the terminal sheet and the renders from the frozen saved scenes; it never saves a scene.

`../update_terminals.py` produced the scene from revision 15 and the native KiCad revision-13 GLB exports recorded in `kicad-working/validation/models-review-13/native-export-record.json`. Before saving, it asserts:

- each reference's placement frame and every part's local transform equal the native export;
- every previous object and material is retained;
- exactly 14 terminal objects are added.

`audit_saved_scene.py` freshly opens both frozen scenes. It compares all object identities, stored data and properties, shaders, packed fonts, collections, animation, editable glyphs, texts and actual displayed instance matrices at frames 1, 80, 120 and 160. Allowed differences:

- new mesh data on the 93 declared part objects, with nothing else on them changed;
- the 14 declared terminal objects, their collection links and their displayed instances;
- five provenance properties on the 25 reference roots;
- the added terminal material;
- the new opening guide and revision properties.

The audit also checks that each terminal object attaches, links and displays like its sibling parts in all four views, and replays the 44 rear checks with 974 rays on both scenes.

`audit_kicad_models.py` replays `scripts/verify_kicad_blender_models.py`: all 491 placed KiCad models match the scene's native meshes. `audit_portability.py` replays the shared 106-check population and resource verifier.

`render_terminal_sheet.py` builds `../terminal-models.png`. It shows each model's own scene meshes in a temporary in-memory scene, in the model frame, with the footprint's drill rings coloured by the nominal-fit audit. `../render_scene.py` renders four standard views and the I/O underside detail. For that detail, the camera clips below the lowest lead and a shadowless upward light exists only in memory. `render-records.json` pins each image and the scene hash, `render-readonly-verification.json` confirms the saved scene bytes are unchanged, and `final-render-review.json` records the visual review and a pixel comparison with revision 15.

`summarize_revision.py` writes `independent-validation-summary.json` and `docs/terminal-completion.json` and asserts the stated outcomes.

These checks establish nominal geometry, preservation and native consistency. They do not qualify physical insertion, terminal fit, enclosure tolerances or fabrication.
