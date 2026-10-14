# Rear connector quality candidates, revision 10

Two independent drawing-derived model families replace the coarse body illustrations at **CV0, GATE0 and POWER0**. The generated STEP files retain the original zero offset/rotation and unity scale. No source board, footprint, existing model or scene was edited.

The MJ-3536N now has sloped molded side rails, a recessed open center, a full nonthreaded nickel bushing, a rear bridge and visible internal contact illustrations. The PJ-202AH now has separate rounded housing/rear cover, rim recesses, retention reliefs and visible mating contact details around the full 2 mm center pin.

Published dimensions govern the full envelopes:

| Candidate | Canonical bounds in mm | Body envelope | Mating geometry |
|---|---|---|---|
| MJ-3536N | X -5..5, Y -3..15.8, Z 0..10 | 10 x15.8 x10 | Bushing diameter6, projection3; bore3.6; axisZ5.5 |
| PJ-202AH | X -4.5..4.5, Y -14.4..0, Z 0..11 | 9 x14.4 x11 | Bore6.5; pin2.0; axisZ6.5; nominal insertiondepth9 |

Unsized roof slopes, window/recess positions, cover seams, contact curvature, stock thickness and minor reliefs are explicit appearance interpretations. They are not manufacturing dimensions. Full envelope sizes are preserved, and no feature was reduced to create artificial board or case clearance.

**Below-seat terminals remain omitted.** The MJ historical and current diagrams imply nominal terminal centers(0,2.3), (0,16), (5.2,13.5) mm; the original board has Ø2.54 round drills at slightly different centers. In the historical dimension chain,11.2 is terminal1-to-terminal3, not terminal1-to-terminal2. The current PDF records reengineering in2023 and2024 and gives distinct slot lengths. The PJ manufacturer drawing specifies a3.0mm-wide side tab while original P$3 is a Ø2.8mm round hole. These differences are recorded without moving or thinning terminals to make a fit. Neither candidate establishes historical variant equivalence, actual installed seating or toleranced PCB fit.

Source comparison uses locally retained2020/current MJ and2015/current PJ manufacturer PDFs, all rendered and visually inspected. A2010 MJ primary PDF was read as indexed webtext, but its binary/render could not be recovered; this is distinguished in the source review. The current PDFs retain the original2005 release dates in their revision histories.

**Manufacturer CAD is not incorporated.** Same Sky's retained CAD terms reserve ownership and describe engineering-reference use; no express redistribution grant was found. The already downloaded `sources/Same_Sky_MJ-3536N.zip` was not read as geometry and must be excluded from all deliverable archives. No new CAD agreement or download form was submitted. Original reconstruction geometry and scripts are CC0-1.0; manufacturer drawings and branding retain their respective rights.

**Use `rear-connector-quality-corrected-manifest.json` for active assignments.** It contains compatible assignment rows, exact source hashes, canonical frames, dimensions, improvements and limitations. `final-geometry-audit.json` freshly verifies43 saved-file checks on the corrected active pair. The earlier `rear-connector-quality-review.json` records29 checks on the superseded first pair and is historical only. These reviews check valid positive-volume solids, closed per-feature meshes, a closed exterior-union combined STL, exact nominal bounds, colored STEP round-trip integrity and source PCB guards. The STEP retains separate material solids. The combined monochrome STL is their exterior union so shared internal material faces cannot produce duplicate sheets.

`native-quality-audit.json` checks the frozen candidates through native KiCad10 GLB export. Both full envelopes and all4MJ/3PJ palette roles survive; the maximum role-bound residual is0.0151923mm from native tessellation of the rounded PJ mating pin. Native export is visual evidence and does not qualify physical fit.

See `source-revision-and-fit-review.json` for exact drawing revisions, source file hashes, original drill comparisons and CAD distribution exclusions. The immutable baseline board is only read for isolated native probes; its source hash is recorded in `native-probe-plan.json`.

The final PJ rearcover has no drilled recess. The Ø1.5 manufacturer callout belongs to a terminal eye, which is omitted with the other below-seat terminals. The first PJ candidate mistakenly illustrated that eye as a plastic recess; `pj-rear-cover-correction.json` records its removal. The original frozen candidate remains review evidence only. Native export was repeated for the corrected STEP and124 checks pass.
