# Working revision 12 — SDS-50J contact correction

The enlarged front drawing on page 3 of the retained [SDS-J datasheet](../../visualization/blender-case-revision-7/quality-model-sources/rear-quality/source/sds50j.pdf) shows the two outer contact centers on the horizontal diameter. Its 25-degree leaders describe the elongated slot directions. The earlier reconstruction mistakenly placed those centers at 25 and 155 degrees.

The corrected center angles are 0, 180, 225, 270 and 315 degrees on the existing 3.5 mm radius, with the mating axis at Z=10 mm. Outer slot tilts are independent ±25-degree rotations from vertical. The three lower centers and their slot directions remain unchanged.

`din-contact-quality/build_corrected_din.py` retains the old housing, rear cover and three lower sleeves as exact solids. It reconstructs the insert and two outer sleeves from the primary drawing, retaining the original colors and nominal 20 × 15.8 × 21.1 mm envelope. Its 29 solid checks include reproduction of the old two-center error. The native KiCad tessellation of the actual updated PCB passes 32 frame, envelope and contact-mouth checks.

`install_corrected_din.py` changes only four embedded PCB model paths and one corresponding CP-2350 footprint-library model path. It verifies all non-model S-expression nodes are identical. Original Eagle files, schematics, copper, nets, pads, drills, footprint poses and project rules are preserved. The older STEP remains available.

Fresh KiCad 10.0.7 I/O ERC reports zero errors and warnings under the retained project rules. The I/O DRC report is exactly equal to the prior report: 348 violation warnings, one separate unconnected MIXOUT0/GND error and 45 separate schematic-parity warnings. Mainboard files remain byte-identical; its earlier native electrical evidence is retained and was not rerun for this model-only update.

`verify_current_functions.py` replays the 214 original-source and current-PCB MIDI function checks with the current board hash. It preserves original source records; the previous frozen function proof remains historical at its previous PCB hash.

The user-supplied Warehouse geometry was inspected in two separate local full-case scenes without scaling or reshaping. Its flange-like cluster is 20.7 × 2.0 × 21.4 mm, compared with the current drawing's 20 × 1.8 × 21.1 mm. At the panel-front registration, four of seven full terminal sections extend beyond nominal drill circles. A rigid 0.12 mm outward shift gives a minimum nominal corner margin of only 0.0104 mm while moving the flange 0.12 mm into the existing panel material. These are measured nominal conflicts, not evidence of a mechanically valid historical variant. Electrical pin-number correspondence and the uploader's factory-origin claim remain unverified. Received standalone CAD and local comparison scenes remain outside the published repository.

The active STEP is our corrected drawing-derived illustration. Slot widths, sleeve sizes, cavity depths, keys and minor molding details remain illustrative; solder terminals and locators remain omitted. The update does not qualify physical assembly or fabrication readiness.
