# x0xb0x original BOM controls and exterior dimensions

These source references support the **separate Blender presentation parts**. The actual KiCad boards and their 425 native model instances are unchanged.

The requested [original parts page](https://ladyada.net/make/x0xb0x/fab/parts.html) returned HTTP 403 for direct retrieval. Its public x0xb0x project mirror at pinned commit `1910f746d2d8758f2651596b00c08f76c847c926` was retrieved and preserved as `original-parts-page-mirror.html`; `original-parts-provenance.json` records the URL and hash. `original-control-parts.json` contains the relevant table rows, original references, quantities, links and image paths.

| Separate presentation part | Original BOM references | Supported nominal dimensions | Evidence |
| --- | --- | --- | --- |
| Eagle 450-4760 small knob | VR2–VR8 and S2, 8 total | 13.2 mm circular body diameter, 15.4 mm height, 10 mm top diameter, 3.3 mm lower collar; white pointer adds 0.8 mm radial projection | [Eagle EPD-200220 manufacturer drawing](https://www.mouser.com/catalog/specsheets/EPD-200220.pdf); local university mirror rendered and visually checked |
| Davies 1510AH switch knob | S3/S4, 2 total | 0.75 in diameter = 19.05 mm; 0.56 in height = 14.224 mm | [Davies manufacturer catalog table](https://daviesmolding.com/catalog/series/knobs/control/1510/) |
| ITT PE/WHT and PE/BLK rectangular caps | S5–S27, 8 white and 15 black total | 12.1 × 5.9 × 11 mm full cap size | [C&K PVA drawing](https://www.ckswitches.com/media/1343/pva.pdf), [C&K PN drawing](https://www.ckswitches.com/media/1413/pn.pdf) |
| NKK B12AB lever A | BOM SW1, actual scene S1 | 2.6 mm diameter, 10 mm length, 26° throw | [NKK B-series drawing](https://www.nkkswitches.com/pdf/Btoggles.pdf), A14–A15 |
| REAN NYS216 exterior hardware | MIXOUT0/MIXIN0/HEADPHONE0 | Nut 17.5 mm outer diameter, 15 mm across flats, 5 mm thick; washer 15.3/11.3 mm OD/ID, 1.2 mm thick | [Official NYS216 drawing](https://www.rean-connectors.com/media/9014/download/nys-216.pdf?v=1), local PDF visually checked |
| CUI MJ-CP3536N/current MJ-3536N face | CV0/GATE0 | Bushing 6 mm OD, 3.6 mm aperture, 3 mm projection from 10 × 10 mm body face | [Same Sky drawing](https://www.sameskydevices.com/product/resource/mj-3536n.pdf), page 2 visually checked |
| CUI PJ-202AH power face | POWER0 | 9 × 11 mm face; 6.5 mm aperture; 2 mm center pin | [Same Sky drawing](https://www.sameskydevices.com/product/resource/pj-202ah.pdf), page 2 visually checked |
| CUI SDS-50J/current Same Sky DIN face | DIN1–DIN4 | Current body face 20 × 21.1 mm, flange 1.8 mm; contacts on 7 mm pitch circle over 180° | [Same Sky SDS-J drawing](https://www.sameskydevices.com/product/resource/sds-j.pdf), page 3 visually checked |

`scene-part-dimensions.json` is the machine-readable record, with source URLs and limitations for each part. Scalar fields are stored inside each part's `dimensions_mm` object and repeated directly in the part record for simple Blender consumers. Angles are explicitly named in degrees.

The Eagle drawing is more specific than rounded current distributor metadata of 14 mm diameter and 16 mm height. Its 13.2 mm body plus pointer projection explains a larger overall width. The original BOM links EPD-200219, which describes the T18 shaft series; EPD-200220 explicitly lists 450-4760 with a 6 mm D-shaft.

The NYS216 nut and washer are black polymer, according to the manufacturer material table. NKK B12AB uses an unthreaded polymer bushing; this BOM does not establish a toggle washer. The SDS-50J's 19 mm callout is its three-hole mounting circle, so it must not be used as a supposedly verified outer mating-recess diameter.

Cap height includes the hidden stem. Its projection above the panel, shaft insertion, all seating depths, detailed snap sockets and exact historical family variants remain presentation assumptions. The BOM supplies the total cap colors without mapping them to individual switch references. No exact manufacturer CAD was recovered in this bounded increment.

The original tempo encoder is **CTS 290VAA5F201B2**, while the actual imported board footprint uses the **PEC11** family. Likewise, the original tact switches are E-Switch TL1100F160Q while the board footprint is B3F-40XX; original USB is Kobiconn 154-2442-E while the board footprint is PN61729. Exterior knobs or caps can follow the BOM without implying a verified replacement of these full component bodies or lead geometry.

Original design attribution remains Copyright (c) Limor Fried and Adafruit Industries; see `../source/LICENSE-original-design.txt`. Manufacturer drawings retain their own copyrights. No claim is made that those documents are MIT-licensed or that these dimensions certify physical fit.
