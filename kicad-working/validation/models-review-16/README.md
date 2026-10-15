# Working revision 16 — Grayhill 25L rebuilt from its drawing and a photograph

The two Grayhill 25LB22-H rotary switches (S3, S4) looked unlike the real part. A user-supplied photograph of a 25L hex-output encoder (label `8 4 2 1 C`, matching the BOM's 25LB22-H) showed several differences: a round drum top over the square base, two side lock lugs, a white label band, a green output board, and pins soldered through the board. The model's anti-rotation tab was also misplaced: the Series 25L drawing's front view puts it on the vertical centre line, 10.16 mm from the axis, opposite the pins, not at the side.

`grayhill-quality/build_grayhill.py` rebuilds the body.

**Kept from the drawing:**
- the 21.97 mm square body and output board;
- the 25.91 mm board depth with the 14.97 mm tongue;
- the 1.14 mm board, with the mounting face 8.71 mm above the seat;
- the 3/8-32 bushing, 6.35 mm long with 8.13 mm flats;
- the 6.35 mm shaft to 27.76 mm, with its 6.35 × 5.56 mm flat toward the pins;
- the 3.05 × 1.73 mm non-turn tab.

The output board, bushing and shaft solids are the revision-8 ones unchanged.

**From the photograph:**
- a 20.2 mm drum from 4.3 mm up to the mounting face, with a rounded top edge;
- two lock lugs reaching the square edge;
- an 84-degree white band reading `8 4 2 1 C`;
- green FR4 with gold lands and solder fillets.

These proportions are photo-derived, not dimensioned. The tab height equals its printed thickness, which is an assumption. The label is 0.17 mm thick: KiCad tessellates that radius in 12-degree facets, and with a thinner label the drum showed through at the facet centres. The body passes 18 checks.

`terminal-quality/build_terminals.py` adds the five 0.64 mm square pins at their dimensioned positions. They now rise 0.8 mm through the solder joints, as in the photograph, and pass 22 checks. `audit_terminal_joins.py` confirms that all 62 terminals of the 12 terminal models join their bodies.

The four MT holes stay empty. They serve the optional 25J5155 mounting bracket, and the BOM part 25LB22-H has no `-Z` (with bracket) suffix. `docs/drill-fit-allowances.json` now records that reason.

`install_terminal_models.py` changes only the two mainboard model paths and the GH3074 footprint-cache path. It verifies that every non-model node and transform is identical.

## Native checks

- **Fit:** the pins fit their drills with 0.047 mm margin, and the same 11 nominal interferences remain elsewhere.
- **Collisions:** the relocated tab clears the top panel, and the only S3/S4 overlaps are the shafts inside their knobs, unchanged from revision 18.
- **ERC/DRC:** fresh ERC on both boards has zero errors and warnings, and both DRC reports equal revision 15.
- **Other checks:**
  - The I/O board is unchanged and its 214 function checks pass.
  - All 491 models resolve.
  - The summary records 289 core files.

These are nominal model checks. They do not qualify physical assembly or fabrication readiness.
