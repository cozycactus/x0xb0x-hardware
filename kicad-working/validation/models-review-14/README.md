# Working revision 14 — terminal corrections from the drawings

An independent source review of revision 13's 19 nominal hole interferences found that four terminal models did not follow their drawings. Revision 14 corrects them. The other eight terminal models keep their revision-13 STEP files.

| Model | References | Revision 13 | Revision 14 | Source |
| --- | --- | --- | --- | --- |
| Alpha RV112 | VR4, VR6 | snap-in tabs at ±6.5 mm | ±5.5 mm | The retained RV112BCF-40 drawing's 13.0 runs across the outer edges of the two 2.0 mm slots; revision 13 misread it as the centre spacing |
| Panasonic EVUF2L | VR2, VR3, VR5, VR7, VR8 | tabs at ±5.30 mm | ±4.50 mm | Same convention on the retained 2005 No. 8 piercing plan: 10.60 across the outer edges of 1.6 mm slots |
| PJ-202AH | POWER0 | terminal 2 3.0 mm wide | 2.50 mm | Same Sky 2025 front view dimensions both blades (2.50 and 3.00), the 2015 CUI drawing draws them nested, and the layout slots are 3.5 and 3.0 |
| SDS-50J | DIN1–DIN4 | signal pins 0.70 × 1.00, earth legs 1.00 × 0.21 | 0.5 × 1.0, earth legs 1.0 × 0.32 | Period CUI SDS-50J rev D (2006): signal pins dimensioned 1.0 deep and drawn 0.5 wide; earth legs dimensioned 1.0 wide |

The 2006 drawing is retained as `terminal-quality/sources/sds50j-cui-rev-d-2006.pdf` (from the Octopart datasheet mirror, sha256 `46975c33…`). The other drawings were already in the repository. The 2006 part shows screw bosses rather than locating pegs, which supports leaving the pegs out.

`terminal-quality/terminal_spec.py` holds all 12 entries, with the four corrections marked in `CHANGED`. `terminal-quality/build_terminals.py` rebuilds only those four models from the same original body sources. Its 69 checks confirm unchanged body solids, colours and named parts, and the specified tip depths. Tab and terminal sections that are not dimensioned remain labelled assumptions.

`install_terminal_models.py` changes only the 12 corresponding PCB model paths and four footprint-cache paths. It verifies that every non-model S-expression node and model transform is identical.

## Native checks

`audit_native_terminals.py` repeats the revision-13 audit on fresh native exports. Every fitted model still has a lead in every drilled hole except the four Grayhill bracket holes. The nominal interferences fall from 19 to 11:

| Model | Pads | Worst margin | Status |
| --- | --- | --- | --- |
| NYS216 | all 6 | −0.28 mm | Unresolved: every manufacturer drawing puts the rows at 4.00 / 10.35 / 16.70 mm, and Eagle sits exactly 0.35 mm further back |
| USB | M2, P$2 | −0.24 mm | Designed press fit: FCI recommends Ø2.30 holes and its barbs are wider still; Eagle drilled Ø2.2. The fitted part is unresolved |
| SDS-50J | 1, 2 | −0.06 mm | Eagle grid positions (pin 1 at 7.62 vs 7.5, pin 2 at 12.68 vs 12.5), within the drawing's ±0.2 tolerance |
| PJ-202AH | P$3 | −0.04 mm | Eagle places the side terminal at 4.6 / 10.862 vs the drawing's 4.7 / 10.7, within ±0.2 |

Alpha, Panasonic, PJ-202AH terminal 2 and SDS-50J pins 3–5 now fit.

Fresh ERC on both boards has zero errors and warnings. Both boards' DRC violations, parity findings and ignored checks equal the revision-13 reports, and the same two connection gaps remain. KiCad now names the S22 +5V gap's ends as a 0.97 mm track ending on S22 pad 1 and the 19.56 mm +5V track; it picks varying representative items of the same islands. `verify_current_functions.py` replays the 214 MIDI function checks on the current I/O board, `local-dependencies.json` confirms that all 491 models resolve, and the revision-14 validation summary records 279 core files.

These are nominal model checks. They do not qualify physical assembly or fabrication readiness.
