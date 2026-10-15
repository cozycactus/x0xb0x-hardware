# Saved revision-14 checks

`run_verification.sh` regenerates every report, the section figure and the renders from the frozen saved scenes; it never saves a scene.

`audit_saved_scene.py` freshly opens both frozen revision-13 and revision-14 scenes. It compares all 1,661 object identities, stored data and properties, shaders, packed fonts, collections, animation, editable glyphs, texts and actual displayed instance matrices at frames 1, 80, 120 and 160. Allowed differences:

- the declared delta on the I/O placement, its study endpoints and labels;
- the parented hidden strip reference;
- every displayed I/O instance, which must move by exactly (0, −0.508, 0) mm in all four views;
- the last 20 mm of the 24 conductors;
- the new opening guide and revision properties.

Objects hidden in a frame are not evaluated by Blender, so their stored matrices there are stale. The audit counts those entries and checks those objects by `matrix_basis` and in the frames where they are visible. The tolerance is 1e-7 m, above float32 storage resolution. The audit also replays the 44 rear checks with 974 rays on both scenes.

`measure_rear_seating.py` is the revision-10 seating audit with only its repository path and output file changed, so both revisions are measured by identical code. `screen_io_contacts.py` lists every touching or intersecting triangle pair between the I/O board and the other rendered meshes. `extract_sections.py` cuts exact sections through the HEADPHONE0, DIN1 and CV0 axes, and `make_section_figure.py` draws `../rear-datum-sections.svg` from them.

`downloaded-din-plate-datum.json` records the user-downloaded SDS-50J mesh flange measured in the local comparison scenes, which remain unpublished. `audit_portability.py` replays the shared 106-check population and resource verifier. `summarize_revision.py` writes `independent-validation-summary.json` and `docs/rear-plate-datum-correction.json` and asserts the stated outcomes.

Rendering uses the frozen saved file without saving it. `render-records.json` pins each image and the scene hash, and `render-readonly-verification.json` confirms the saved scene bytes remain unchanged. A visual review follows rendering.

These checks establish nominal registration, preservation and sampled visual passages. They do not qualify physical insertion, terminal fit, enclosure tolerances or fabrication.
