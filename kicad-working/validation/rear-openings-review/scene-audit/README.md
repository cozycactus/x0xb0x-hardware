# Rear connector opening diagnosis, saved Blender revision 8

The assembled scene contains five obsolete solid recess disks across the three 1/4-inch audio and two 3.5 mm sockets. In addition, the three separate exterior nut and washer pairs are solid illustrations without bores. Removing only the five disks leaves all three large audio sockets blocked by their hardware.

The audit used frame 1 evaluated dependency-graph collection-instance matrices, not the source collection coordinates. Per-instance native BVH raycasts enter from external +world Y and accumulate all surface intersections. All 11 rear ports face outward correctly. The 119 sampled rays found no panel or enclosure obstruction across these mating apertures. The saved revision 8 scene bytes were unchanged.

| Port | Erroneous presentation blockers | Native center behavior after ignoring blockers |
| --- | --- | --- |
| POWER0 | None | 1.0227 mm |
| HEADPHONE0 | HEADPHONE0 / jack recess proxy; HEADPHONE0 / black ABS washer proxy; HEADPHONE0 / black PA6 nut proxy | Open beyond modeled body |
| MIXIN0 | MIXIN0 / jack recess proxy; MIXIN0 / black ABS washer proxy; MIXIN0 / black PA6 nut proxy | Open beyond modeled body |
| MIXOUT0 | MIXOUT0 / jack recess proxy; MIXOUT0 / black ABS washer proxy; MIXOUT0 / black PA6 nut proxy | Open beyond modeled body |
| CV0 | CV0 / jack recess proxy | 17.1 mm |
| GATE0 | GATE0 / jack recess proxy | 17.1 mm |
| USB0 | None | 1.3 mm |
| DIN1 | None | 5.8 mm |
| DIN2 | None | 5.8 mm |
| DIN3 | None | 5.8 mm |
| DIN4 | None | 5.8 mm |

The CV and GATE sockets correctly have a blind rear wall 17.100 mm behind the mating face. The audio socket models have a through bore. Power has the intended 2 mm center pin; its rounded nose is 1.023 mm behind the face while the annular opening remains clear. USB-B has the intended insulating tongue 1.300 mm behind the face with surrounding mating space visible. Each DIN socket has its intended insert recessed 5.800 mm, and each of its five contact-hole axes clears that insert to at least 7.400 mm. These surfaces must be preserved.

The minimal correction is to remove the five recess disks and bore the six exterior nut/washer illustrations. Hardware bores must accommodate the native 9.525 mm threaded bushing, rather than merely the 6.35 mm plug aperture. Preserve the outer hardware geometry and actual connector poses. No native connector, PCB, panel or case geometry requires a change for this visual obstruction.

Detailed per-ray world coordinates and ordered intersections are in `rear-ray-audit.json`. Current source SHA256: `69aee3594bd9d836f5216a61f8a9bf1cd7e41c4287eb4cb1f5e1a0f6fa23bf27`.

These checks establish the modeled openings and visible geometry. They do not qualify physical seating, thread tolerance, connector insertion force, cable clearance or historical component variant compatibility.

## Corrected scene and reusable regression

Revision 9 removes exactly the 5 obsolete disks and opens the 6 retained audio hardware illustrations at the actual native axes: a 9.6 mm nominal nut bore and an 11.3 mm nominal washer bore. The three native 9.525 mm threaded noses and 6.35 mm mating bores remain unchanged.

The same unmodified `scripts/verify_rear_openings.py` ran against both saved scenes. Revision 8 fails 11 geometric groups (all 5 affected passages and all 6 solid hardware pieces), with native exit code 1. Revision 9 passes all 44 checks comprising 974 raycasts, with exit code 0. It checks all 11 ports, 600 dense hardware rays, the 5 bores of each DIN insert, USB space around its retained tongue and the power jack's annular mating space around its retained pin. It restores the initial frame, writes no files and verifies that saved scene bytes remain unchanged.

The verifier uses all evaluated displayed mesh geometry for aperture tests; simply deleting or renaming a proxy cannot pass it while other geometry still closes an opening. Hardware checks isolate retained nut/washer geometry around the native threaded nose envelope. Physical installed fit remains unqualified.

Machine-readable results: `reusable-before.json`, `reusable-after.json` and `rear-openings-regression.json`.

The separate detailed 119-ray diagnostic confirms that revision 9 has zero recess disks, zero exterior hardware intersections across the sampled mating bores and zero panel/case blockers. Its full ordered ray intersections are retained in `rear-ray-audit-after.json`, alongside the original revision 8 `rear-ray-audit.json`. The isolated 600-ray hardware audit fails all six pieces before correction and passes all six afterward (`audio-hardware-bore-before.json` / `audio-hardware-bore-after.json`). Both saved scene hashes remain unchanged by inspection.
