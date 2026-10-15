# Working revision 17 — TL1100F legs coloured as metal

In the KiCad 3D viewer, the 23 TL1100F tact switches (S5–S27) showed black legs between the switch body and the board. The model is the publisher's TL1100F CAD, which is one grey solid. Revision 8 coloured its faces by position, giving terminal metal only to faces lying wholly below the seat. That left 24 faces per switch black: the faces where the legs leave the 12 × 12 mm housing and rise up to 1.45 mm above the board.

`tl1100-colour/recolour_tl1100.py` re-points only those faces' `STYLED_ITEM` entries to the existing terminal style. The rule: a face is terminal metal if it lies wholly below the seat, or if any part of it lies outside the housing outline (|x| or |y| > 6.0 mm). Every other STEP entity is byte-for-byte unchanged, and the reloaded B-rep is identical to revision 8. Role counts move exactly 24 faces from housing to terminals.

`tl1100-colour/check_native_colours.py` reads KiCad's own export of all 23 switches. On each, every triangle outside the housing outline uses the terminal colour, 368 triangles changed colour, and the triangle geometry equals revision 16.

`install_tl1100_colour.py` changes only the 23 PCB model paths and the B3F-40XX footprint-cache path. It verifies that every non-model node and transform is identical. The revision-8 STEP remains.

Fresh ERC on both boards has zero errors and warnings, and both DRC reports equal revision 16. The I/O board is unchanged and its 214 function checks pass. The fit audit, the drill-fit check and the terminal join check are unchanged, as expected for a colour-only update. The summary records 291 core files.

The legs keep the publisher's free-state shape and their recorded drill-fit allowance. These are nominal model checks, not physical fit qualification.
