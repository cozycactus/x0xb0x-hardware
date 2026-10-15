# Revision21 verification

Reports pin the saved scene and native source hashes. `audit_saved_scene.py` compares revision20 with21; the other Blender audit wrappers replay the shared repository checks against the loaded revision21 scene. Run Blender with `--background`, `--python-exit-code 1` and the relevant `--python` script; native model/drill checks also require KiCad10.0.7. Rendering is read-only and its image hashes are recorded separately.

Nominal geometry checks and visual inspection do not qualify tolerances, material deformation, soldering, mating hardware or physical assembly.
