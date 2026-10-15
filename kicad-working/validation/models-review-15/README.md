# Working revision 15 — terminals joined to their bodies

Looking in the KiCad 3D viewer, the user noticed that some potentiometer pins did not come out of the pots. Isolated edge-on renders and a solid-distance audit confirmed it. In six models, 24 terminals stopped just above the seat, 0.03–2.4 mm beside the body:

| Model | References | Terminals | Gap before |
| --- | --- | --- | --- |
| Alpha RV112 | VR4, VR6 | six signal pins | 2.4 mm |
| CTS 290 | S2 | all seven | 0.37–1.86 mm |
| SDS-50J | DIN1–DIN4 | pins 4, 5 | 1.0 mm |
| Panasonic EVUF2L | VR2, VR3, VR5, VR7, VR8 | three signal pins | 0.65 mm |
| NKK B12AB | S1 | four bracket legs | 0.48 mm |
| MJ-3536N | CV0, GATE0 | tip and tip shunt | 0.03–0.1 mm |

The drawings show these terminals leaving the edge of the base and turning down to the board. Revisions 13 and 14 modelled only the part below the seat.

`terminal-quality/terminal_spec.py` lists them in `FORMED_LEGS` with the drawing view for each. `terminal-quality/build_terminals.py` gives each one a formed leg with the terminal's own section: a riser, then a horizontal leg into the nearest body edge, entering it by 0.3 mm. Each leg sits at the lowest height where body material exists. The legs are 0.5–2.85 mm long and lie between 0.4 and 1.4 mm above the seat. Leg height and bend are assumptions, because the drawings show the path but do not dimension it. Pin positions, sections and lengths are unchanged.

The build passes 146 checks, including a join check for every terminal of the six models. `terminal-quality/audit_terminal_joins.py` then checks all 12 current terminal models: all 62 terminals touch or enter their bodies.

`install_terminal_models.py` changes only 15 PCB model paths and six footprint-cache paths. It verifies that every non-model S-expression node and transform is identical.

## Native checks

`scripts/verify_terminal_joins.py` repeats the join check on KiCad's own native export of both boards. It splits each drawing-derived terminal model's tin-coloured terminal geometry into connected pieces: 133 pieces at 25 references, one per placed terminal. Every piece intersects or touches its body. On the revision-14 boards it fails exactly on the 50 placed free-standing terminals.

`audit_native_terminals.py` still finds a lead in every drilled hole, apart from the four empty Grayhill bracket holes. The legs cross no board geometry, and the same 11 nominal hole interferences remain. `scripts/verify_drill_fit.py` passes on all 489 models.

Fresh ERC on both boards has zero errors and warnings. Both boards' DRC violations, parity findings and ignored checks equal revision 14, and the same two connection gaps remain. The 214 MIDI function checks pass on the current I/O board, all 491 models resolve, and the revision-15 summary records 287 core files.

These are nominal model checks. They do not qualify physical assembly or fabrication readiness.
