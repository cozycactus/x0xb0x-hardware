# Open a fresh download

The editable projects were verified with KiCad 10.0.7 and Blender 5.0.0 on macOS. Their project-local paths and filename case are also checked without consulting global KiCad libraries. Other operating systems have not been tested in their native applications.

## Download and open

1. Sign into the GitHub account that has access to this private repository. Download and extract the complete repository, or clone it using Git.
2. For the main PCB, open `kicad-working/mainboard/mainboard.kicad_pro` in KiCad. For the I/O PCB, open `kicad-working/ioboard/ioboard.kicad_pro`. Each project includes its schematic, PCB, symbols, footprints and models; keep its folder contents together.
3. To inspect the complete enclosure, open `kicad-working/visualization/blender-case-revision-18/x0xb0x-populated-with-case.blend` in Blender. The board geometry is embedded. The omitted board GLB exports are not needed to view it.
4. Select frame 1 for the assembled case, frame 80 for the exploded assembly, frame 120 for control-side inspection, or frame 160 for the wiring study. Button caps are intentionally hidden in the two inspection views.

All 40 LED lenses belong to PCB-mounted LED assemblies. All 23 button caps stay attached to the PCB switches when the case is exploded. The external spacer mold, cap sockets and switch travel remain unmodeled; alignment in the scene does not certify physical fit.

## Optional verification

From the repository folder, with Python 3.9 or later:

```sh
python3 scripts/verify_project.py
python3 scripts/verify_kicad_dependencies.py
python3 kicad-working/validation/models-review-15/verify_current_functions.py
```

All three commands print JSON with a `passed` result and return a nonzero exit status on failure. None needs KiCad or Blender. To inspect another checkout, append `--root /path/to/checkout` to either of the two `scripts/` commands. The hash check detects changes from this recorded snapshot; intentional edits require updating the corresponding evidence and manifest.

To inspect the saved scene with native Blender, run:

```sh
blender --background kicad-working/visualization/blender-case-revision-18/x0xb0x-populated-with-case.blend \
  --python-exit-code 1 --python scripts/verify_blender_scene.py
```

On the verified macOS installation, replace `blender` with `/Applications/Blender.app/Contents/MacOS/Blender`. The `--python-exit-code 1` option makes verification errors fail the command. Blender prints its normal log as well as the JSON result. The checker restores the current frame in memory and never saves the scene.

To check the rear connector passages, use the same command with `--python scripts/verify_rear_openings.py`. This additional checker casts rays through the evaluated assembled scene and distinguishes open passages from expected recessed contacts, the power pin and USB tongue. It detects the old revision-8 obstruction and the old DIN outer-center error, and checks the current geometry without saving the scene.

To confirm that the scene embeds exactly the current KiCad 3D models, use the same command with `--python scripts/verify_kicad_blender_models.py`. It exports both PCBs with KiCad's `kicad-cli` into a temporary folder, using a private KiCad configuration, and compares every placed model's footprint frame and geometry with the scene's native mesh of the same designator. It also checks that both PCB files are unchanged. KiCad 10.0.7 is expected at `/Applications/KiCad/KiCad.app`; set `KICAD_CLI` to point elsewhere. Revision 18 matches all 491 models exactly. On revision 17 the check reports exactly the 15 references whose terminals gained formed legs in KiCad revision 15.

To check every placed model's leads against the real drills, run `blender --background --factory-startup --python-exit-code 1 --python scripts/verify_drill_fit.py` (no scene is needed). It exports both PCBs with `kicad-cli` into a temporary folder, reads the drilled pads from the PCB files, and requires a lead in every drilled hole. Any interference or board crossing beyond the sourced exceptions in [drill-fit-allowances.json](drill-fit-allowances.json) fails; allowances no longer needed are listed. Set `KICAD_CLI` as above.

To check that every drawing-derived terminal joins its component body, run `blender --background --factory-startup --python-exit-code 1 --python scripts/verify_terminal_joins.py` (no scene is needed). It exports both PCBs with `kicad-cli` and fails if any terminal piece stands apart from its body.

The Blender portability check covers population, embedded geometry, full LED lead envelopes, visible and hidden cap attachment behavior, and unpacked external resources. The dependency checker covers local library/model resolution. These checks do not run ERC, DRC, tolerance analysis or physical assembly testing. Historical KiCad revision-10 fresh-download checks are in [fresh-clone-verification.json](fresh-clone-verification.json); Current KiCad15 model checks and fresh ERC/DRC for both boards are in [working validation](../kicad-working/validation/working-validation-summary-revision-15.json). Blender revision 9's opening correction is recorded in [rear-opening-correction.json](rear-opening-correction.json), revision 10's nut refinement in [nys216-hardware-refinement.json](nys216-hardware-refinement.json), revision 11's legend seating correction and remaining fit limits in [rear-seating-and-legends.json](rear-seating-and-legends.json), revision 12's corrected MIDI functions in [din-midi-correction.json](din-midi-correction.json), revision 13's corrected contact pattern in [din-contact-correction.json](din-contact-correction.json), revision 14's rear plate datum in [rear-plate-datum-correction.json](rear-plate-datum-correction.json), revision 15's rear height datum in [rear-height-datum-correction.json](rear-height-datum-correction.json), revision 16's drawing-derived terminals in [terminal-completion.json](terminal-completion.json), revision 17's corrected terminals and remaining hole conflicts in [terminal-drawing-correction.json](terminal-drawing-correction.json), and revision 18's formed terminal legs in [terminal-join-correction.json](terminal-join-correction.json).

## If something is missing

Use a complete extraction and preserve filename case. A failed dependency check names the affected component or library and its expected local path. Global library installation is not needed to resolve the included project assets. The optional BA662A at `IC15A0` and seven mechanical-only mainboard footprints intentionally have no 3D model.

Historical model-building and audit scripts may require their original baselines and macOS tools. The saved projects and Blender scene can be inspected without running those scripts. Existing electrical connection gaps and mechanical uncertainties remain documented in the main README and source notes.
