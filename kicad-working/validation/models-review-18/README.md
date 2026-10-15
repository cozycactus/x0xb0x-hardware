# KiCad working revision18 — BOM USB correction

The user supplied the Kobiconn154-2442-E KC-301021 drawing from Mouser. Its side view identifies a **0.38mm body-to-PCB gap**, **2.91mm signal-terminal projection**, and **3.72mm board-lock projection**. Revision18 corrects the previous mixed-source USB model to these dimensions. The drawing is archived with provenance under `usb-quality/sources/`.

The original XY terminal axes, body envelope and mating cavity are retained. The four signal pins now clear the conductive shell and exit through illustrative white insulator skirts. Four illustrative gold mating strips improve the front view. Terminal stock, lock fork shape, shell gauge, skirts and contact-strip dimensions are not dimensioned by the source and remain documented assumptions. This is independent drawing-derived CAD, not manufacturer CAD or identification of the physically fitted part.

Only USB0's model path and its cached footprint model path change in the native files. Copper, pads, drills, footprint placements and model transforms are preserved. Both projects retain their original electrical rules.

Fresh KiCad10.0.7 ERC reports show0 errors/0 warnings under those rules. DRC violations and parity results match revision17, including the existing three missing connections. `native-terminal-audit.json` passes32 checks over491 models and retains11 known nominal fit findings. The USB board locks still exceed the original nominal hole wall by about0.2392mm; the source recommends2.30mm mounting drills whereas Eagle has2.2mm. No hole was changed. Physical fit and tolerance qualification remain open.

The FreeCAD build and31-check solid audit are in `usb-quality/`; `native-usb-audit.json` separately checks actual KiCad-exported geometry. Installation evidence, native export records, local dependency checks and214 current function checks are retained here. The current combined result is `../working-validation-summary-revision-18.json`.
