# KiCad working revision 21 — Xicon XRL electrolytics

All 39 radial electrolytics now use Xicon XRL bodies, the Mouser house-brand family behind the original kit's light-blue capacitors. The parts page lists them only as "Generic"; search-engine extracts of the expanded BOM give 140-XRL part numbers, but that page itself could not be read (HTTP 403 and a Cloudflare check), so those numbers are recorded as unconfirmed in `electrolytic-quality/sources/electrolytic-evidence.json`. Can sizes come from the XRL datasheet XC-600178 (1/8/07, saved in `sources/`, page 2 inspected) and agree with the length-to-diameter ratios measured on the eight original kit photographs:

| Body | References | Parts |
|---|---|---|
| 5 x 11 mm, 0.5 mm leads | 29 mainboard E5-6, C60 C61 C203 C205 | 1uF 50V, 2.2uF 50V, 10uF 16V, 47uF 16V, 100uF 10V |
| 6.3 x 11 mm, 0.5 mm leads, vent | C7 C8 | 100uF 25V |
| 10 x 12.5 mm, 0.6 mm leads, vent | C43 | 1000uF 10V |
| revision-5 geometry, recoloured | C17 (5 x 11), C3 C5 (13 x 20) | 1uF 50V, 2200uF 16V |

The previous generic KiCad bodies were 5 mm and 10 mm tall at 2.50/5.00 mm pitch. The new models are built in the inherited KiCad model frames (offset -1.25 / -2.5 mm), so footprints, pads, copper and every model transform stay unchanged while the leads land on the exact 2.54/5.08 mm holes. The 6.3 and 10 mm cans' factory pitch (2.5 and 5.0 mm) is within the drawing's +/-0.5 mm of the holes, so their leads are straight; the 5 mm can's 2.0 mm factory pitch is not, so its leads leave the seal at 2.0 mm and are formed out to 2.54 mm above the board, as on the kinked leads in the kit photographs. Seat gaps (1.5 mm for 5 mm cans, 0.5 mm otherwise), the vent cross and colours sampled from uncalibrated photographs are illustrations. C17, C3 and C5 change only two COLOUR_RGB entities; their B-rep is byte-identical to revision 5.

`build_electrolytics.py` passes 272 solid, section, round-trip and per-reference pad checks. `install_electrolytic_models.py` changes only model path strings in seven files; C7/C8 take the 6.3 mm body as instance overrides while the I/O E5-6 cache keeps the 5 x 11 mm body of its other four placements. PCB value fields (47/16, 100/6.3, 1000/6.3) differ from the parts page and are left unchanged.

Fresh KiCad 10.0.7 ERC reports 0 errors/0 warnings; DRC violations, parity and ignored checks equal revision 20. The native audit finds a lead in every drilled hole of all 491 models; all 39 electrolytics fit with 0.25 mm (0.5 mm leads) or 0.2 mm (0.6 mm leads) radial margin and no board crossing away from their holes. The 11 known nominal fit findings are unchanged. `electrolytic-quality/check_native_colours.py` confirms the four XRL colours and the stripe side on all 39 native placements. See `../working-validation-summary-revision-21.json`. Physical assembly remains unqualified.
