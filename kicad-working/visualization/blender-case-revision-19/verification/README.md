# Saved revision-19 checks

`run_verification.sh` regenerates every report, the terminal sheet and the renders from the frozen saved scenes; it never saves a scene.

`../update_grayhill.py` produced the scene from revision 18 and the native KiCad revision-16 GLB exports recorded in `kicad-working/validation/models-review-16/native-export-record.json`. It names the existing S3/S4 part objects from the revision-15 native export they came from. Matching parts receive the new mesh, the removed land part is deleted, and four new parts are added beside their siblings. Before saving, it asserts:

- the placement frames and part transforms equal the native export;
- no previous material is modified;
- only the five new materials are added;
- only the declared objects change.

`audit_saved_scene.py` freshly opens both frozen scenes. It compares all object identities, stored data and properties, shaders, packed fonts, collections, animation, editable glyphs, texts and actual displayed instance matrices at frames 1, 80, 120 and 160. Allowed differences:

- new mesh data on the 12 declared part objects;
- the 8 added and 2 removed part objects, with their collection links and instances;
- five provenance properties on the two roots;
- the five added materials and the two materials that only the old Grayhill parts used;
- the new opening guide and revision properties.

Added objects must attach, link and display like their siblings. The audit also replays the 44 rear checks with 974 rays on both scenes.

`audit_kicad_models.py` replays `scripts/verify_kicad_blender_models.py`: all 491 placed KiCad models match the scene's native meshes. `audit_terminal_joins.py` replays `scripts/verify_terminal_joins.py`: all 133 placed terminal pieces join their bodies. `audit_portability.py` replays the shared 106-check population and resource verifier.

`render_terminal_sheet.py` builds `../terminal-models.png`. It shows each model's own scene meshes in a temporary in-memory scene, in the model frame, with the footprint's drill rings coloured by the nominal-fit audit. `render_grayhill.py` renders the rebuilt S3 close up into `../grayhill-25l.png`. `../render_scene.py` renders four standard views and the I/O underside detail. For that detail, the camera clips below the lowest lead and a shadowless upward light exists only in memory. `render-records.json` pins each image and the scene hash, `render-readonly-verification.json` confirms the saved scene bytes are unchanged, and `final-render-review.json` records the visual review and a pixel comparison with revision 18.

`summarize_revision.py` writes `independent-validation-summary.json` and `docs/grayhill-25l-rebuild.json` and asserts the stated outcomes.

These checks establish nominal geometry, preservation and native consistency. They do not qualify physical insertion, terminal fit, enclosure tolerances or fabrication.
