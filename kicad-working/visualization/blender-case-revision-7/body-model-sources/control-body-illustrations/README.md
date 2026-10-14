# Original-BOM control bodies

These six original body illustrations populate 34 mainboard references: 23 E-Switch TL1100F160Q tactile switches; five Panasonic EVUF2LFL3 pots; two Alpha RV112BCF-40 pots; the CTS 290VAA5F201B2 encoder; the NKK B12AB toggle; and two Grayhill 25LB22-H rotary switches. The original x0xb0x parts list identifies the parts. The preserved manufacturer drawings establish their dimensions.

`control-body-manifest.json` contains both `parts[]` for Blender and `assignments[]` for the parent integrator. Each family has one complete STEP and one complete STL, plus separate STL segments for material assignment and actuator visibility. Units are millimetres. Generated illustration geometry is CC0-1.0; manufacturer drawings retain their original rights.

The canonical frame follows the original **F.Cu footprint library**, before any placed-board side flip: X is library X, Y is negative library Y, and Z points outward. The rear housing datum is Z=0. Offset and rotation overrides are zero. Apply KiCad's actual footprint rotation and side transformation once. In particular, the Grayhill output tongue belongs on canonical negative Y; no placed B.Cu flip is baked into the asset.

The STEP models are original published-envelope illustrations, rather than recovered manufacturer CAD. Nominal complete housing dimensions and shaft lengths are preserved. Historical seating gap, trimmed shafts, formed terminals, molding details and fit qualification are outside this work. Parts are suitable for intentional visual population and remain identified as body illustrations. Segment material suggestions are included in the manifest because the headless STEP export may display viewer default colors.

Three dimensional details affect assembly interpretation:

- Panasonic's FL3 shaft L=21.5 mm starts at the front of its 8.5 mm housing, so the complete shaft tip is Z=30.0 mm.
- Alpha's L=25 mm starts at the rear housing plane, so its shaft tip is Z=25.0 mm. The historical BOM 25F suffix is retained; current 25A flat detail is marked as a current-family illustration.
- NKK's bracketed housing and bushing together measure 13.1 mm. The bushing projects 2.7 mm, leaving a 10.4 mm housing envelope. The 10.0 mm dimension is the lever length. Its neutral illustrative pose preserves this length; an installed ON-NONE-ON lever has two end positions within the published total 26 degree throw.

The CTS illustration follows the original A unthreaded bushing and A5 15 mm shaft options. It does not substitute the preserved but different 290VBC0F201B2 manufacturer model, or treat the PEC11-S footprint name as a Bourns part identity.

`control-body-audit.json` records six valid STEP readbacks, matching exported bounds, STL integrity, 34 unique references, original front-library frames and unchanged input boards/libraries during generation. These checks validate the exported illustrations. They do not qualify terminal, enclosure or physical assembly fit. The separate review renders show the six bodies at the same camera scale.

Sources: [original parts list](https://ladyada.net/make/x0xb0x/fab/parts.html), [pinned public parts-list mirror](https://raw.githubusercontent.com/x0xb0x/x0xb0x.github.io/1910f746d2d8758f2651596b00c08f76c847c926/pages/ladyada.net/make/x0xb0x/fab/parts.html), [TL1100F160Q drawing](https://configured-product-images.s3.amazonaws.com/2D/specs/TL1100F160Q.pdf), [Panasonic EVU drawing](https://hkjdwchip.com/image/files/panasonicelectroniccomponents-evue2af25d14-datasheets-6366.pdf), [Alpha RV112B drawing](https://static.chipdip.ru/lib/521/DOC013521571.pdf), [CTS290 drawing](https://www.ctscorp.com/Files/DataSheets/Encoders/encoders-290-datasheet.pdf), [NKK B toggles drawing](https://www.nkkswitches.eu/pdf/toggle_B.pdf), [Grayhill25L drawing](https://grayhill.com/wp-content/uploads/media/25l-datasheet.pdf). Local drawing paths, hashes and pages are recorded per family in the manifest.
