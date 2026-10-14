# Saved revision-13 checks

`audit_saved_scene.py` freshly opens both frozen revision-12 and revision-13 scenes. It compares all 1,661 object identities, stored data and properties, shaders, packed fonts, collections, animation, editable glyphs, and actual displayed instance matrices at frames 1, 80, 120 and 160. Four native DIN mesh datablocks and six declared source metadata fields on each corresponding root may change. All other scene objects and data are retained.

The corrected DIN-180 contact-center test deliberately fails on revision 12 at the two outer contacts of each DIN. Its failure is retained in `baseline-corrected-contact-regression.json`. The current scene passes all 44 rear checks and 974 rays. Historical aperture reports used the incorrect outer center angles and are retained as historical evidence rather than accepted as current contact-pattern validation.

`audit_portability.py` replays the shared 106-check population and resource verifier. The MIDI audit reuses the preserved circuit-function derivation from revision 12 and compares the current PCB against original Eagle membership records. It retains four correct editable port labels. Fresh I/O electrical checks are recorded separately in the KiCad revision-12 summary.

Rendering uses the frozen saved file without saving it. `render-records.json` pins each image and the scene hash, and `render-readonly-verification.json` confirms the saved scene bytes remain unchanged. A visual review follows rendering.

These checks establish nominal model interpretation, preservation and sampled visual passages. They do not qualify physical insertion, terminal fit, enclosure tolerances or fabrication.
