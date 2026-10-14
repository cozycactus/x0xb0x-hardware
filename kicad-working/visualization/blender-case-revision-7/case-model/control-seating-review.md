# Read-only knob and switch seating review

The stable assembled scene was measured at frame 1 without saving it. Its SHA256 is `fea4edc23e4da7e4e157292348cc2c5c59e06aefd4bacc92a31610d5d6214f0b`. Heights below use the top panel's local outward normal, with underside Z=0 and outer surface Z=1.5748 mm.

Five full nominal EVU shafts (VR2, VR3, VR5, VR7, VR8) extend approximately 0.604 mm above their black knob tops, or 0.444 mm above the white pointer. The other soft-knob shafts do not protrude. The original Grayhill shaft tips sit 0.460 mm below the black rotary knob tops.

The final presentation proposal is to elevate all eight matching soft-knob groups by **1.7 mm**, and both Grayhill rotary knob groups by **1.2 mm**, along the panel normal. Move each reference's skirt, knob and pointer objects together. The JSON supplies all 38 exact object names and both source-frame and world translation vectors. Labels and all native PCB geometry, panels and case remain fixed. No shaft is shortened or scaled.

For this proposal, a **0.5 mm roof thickness** and **0.5 mm minimum internal top clearance** are explicit presentation assumptions. The current solid knob proxies contain no modeled bore; the manufacturer sources do not establish bore depth, grip length, roof thickness or fitted seating. “Insertion” below is the nominal envelope overlap between shaft tip and knob underside.

| Reference | Elevation | New panel gap | Nominal insertion | Assumed internal top clearance | Knob underside above bushing |
|---|---:|---:|---:|---:|---:|
| VR2 | 1.7 mm | 2.300 mm | 14.304 mm | 0.596 mm | 2.196 mm |
| VR3 | 1.7 mm | 2.300 mm | 14.304 mm | 0.596 mm | 2.196 mm |
| VR4 | 1.7 mm | 2.300 mm | 9.304 mm | 5.596 mm | 3.796 mm |
| VR5 | 1.7 mm | 2.300 mm | 14.304 mm | 0.596 mm | 2.196 mm |
| VR6 | 1.7 mm | 2.300 mm | 9.304 mm | 5.596 mm | 3.796 mm |
| VR7 | 1.7 mm | 2.300 mm | 14.304 mm | 0.596 mm | 2.196 mm |
| VR8 | 1.7 mm | 2.300 mm | 14.304 mm | 0.596 mm | 2.196 mm |
| S2 | 1.7 mm | 2.300 mm | 5.504 mm | 9.396 mm | 4.496 mm |
| S3 | 1.2 mm | 1.800 mm | 12.564 mm | 1.160 mm | 0.136 mm |
| S4 | 1.2 mm | 1.800 mm | 12.564 mm | 1.160 mm | 0.136 mm |

The 1.7 mm soft-knob elevation leaves the longest EVU tips approximately 0.596 mm below the assumed internal roof, while keeping matching knob tops aligned. S2 retains approximately 5.504 mm nominal insertion on its 6 mm shaft, all within its published 7 mm flatted end. That is a plausible visual seat; no sourced minimum grip establishes a physical retention claim. VR4/VR6 retain approximately 9.304 mm insertion. EVU and Alpha overlap extends approximately 2.304 mm below the published flatted section into the round shaft envelope, so the unknown underside entry/recess and D-socket length remain a fit limitation.

The Grayhill elevation is 1.2 mm because 0.6 mm would satisfy the roof criterion but leave the knob underside 0.464 mm below the full nominal bushing top. With 1.2 mm, the underside clears that bushing by approximately 0.136 mm, avoiding reliance on an unmodeled underside counterbore. Approximately 12.564 mm of the published 12.7 mm shaft beyond the bushing remains within the knob envelope.

The 23 switch caps can retain their current visual seats. They remain 11 mm high, with 2.5 mm visible above the panel, and fit within the original rectangular DXF openings with approximately 0.300 mm/0.225 mm edge margins. Native actuator tips are approximately 2.404 mm above the cap bottoms and 8.596 mm below cap tops. The solid cap bottoms extend 0.604 mm below the actuator base's top, while staying 0.496 mm above the switch cover. Their actual hollow socket, snap engagement and stroke are unknown; these are envelope measurements, not physical cap fit validation.

S1 is supplied by the full native NKK body and neutral 10 mm lever; no superseded presentation lever remains. Its tip projects approximately 9.704 mm above the panel, and the 6 mm bushing ends approximately 0.296 mm below the panel's outer surface. The original 6.35 mm hole supplies a nominal 0.175 mm radial bushing clearance. Keep the native geometry and pose. Full lever throw, panel tolerance and actual mounting seat remain unqualified.

The machine-readable recommendations include current and proposed heights, all exact proxy names, native and proxy bounds, maximum-height witness points, source URLs, the source manifest hashes, and the interpretation limits. The scene hash was unchanged at the end of review.
