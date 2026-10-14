# DIN/MIDI connector sources and functions

The original x0xb0x BOM specifies four **CUI SDS-50J** right-angle, through-hole,
five-contact 180-degree DIN receptacles. **CP-2350-ND** is their historical
DigiKey distributor identifier. The old Eagle library/package is CP-2350 and
the placed value is CP2350. A community model's SMD wording is inconsistent
with the actual source family; its part number and drawing must govern.

## Functions from the original source

The preserved original Eagle 4.13 schematic and board were freshly inspected
as fixed-length binary records, independently of the Blender labels. Their pad
nets agree with the current KiCad PCB for the relevant MIDI/DIN-sync circuits.
The original schematic's named blocks corroborate those electrical chains.

| Reference | Actual function | Revision 11 text | Correct revision 12 text |
| --- | --- | --- | --- |
| DIN1 | MIDI OUT | MIDI IN | MIDI OUT |
| DIN2 | MIDI THRU | MIDI OUT | THRU |
| DIN3 | MIDI IN | THRU | MIDI IN |
| DIN4 | DIN SYNC | SYNC | SYNC |

THRU and SYNC are retained display abbreviations. Port positions and electrical
connections stay unchanged; only the first three presentation strings require
correction. This is not a mirroring or front/rear viewpoint ambiguity.

- DIN1 pin 5 reaches R13 and then MIDI_OUT/J3 pin 6. Pin 4 receives +5 V through
  R14.
- DIN2 pin 5 reaches R15 and the received stream at MIDI_IN/Q50/J3 pin 5. Pin 4
  receives +5 V through R18. This is the buffered THRU path.
- DIN3 pin 4 reaches R19 and IC24 optocoupler input pin 1; pin 5 reaches IC24
  input pin 2 and D48. The receiver then drives the MIDI_IN/Q50 circuit.
- DIN4 pins 1, 3, 4 and 5 reach the four DINSYNC lines through R24, R21, R23 and
  R22 respectively. Pin 2 returns through R20 to ground.

`function-source-evidence.json` records exact original Eagle and current KiCad
hashes, relevant original pad/pin memberships, raw 24-byte schematic record
bytes, original block labels and positions, and the decoder-table hash. The
default `inspect_din_functions.py` replay uses only checked-in files: it checks
those source hashes/raw record bytes and the current PCB connectivity. Passing
`--parser-source` with the local KiCad fork's `eagle_bin_parser.cpp` also
reproduces the full original binary interpretation through the existing source
inspector. The fork table is referenced by hash, not copied into this project.

## CAD availability on 2026-10-15

The manufacturer's usable dimensioned PDF is
[SDS-J, page 3](https://www.sameskydevices.com/product/resource/sds-j.pdf), already
retained under Blender revision 7's rear-quality sources. It gives SDS-50J a
20 mm width, 15.8 mm maximum depth, 21.1 mm overall height and 1.8 mm flange,
with a 7 mm contact circle and three 1.6 mm holes on a 19 mm circle. This is a
mechanical PDF, not a recovered STEP or mechanical DXF.

The exact legacy [SketchUp Warehouse listing](https://embed-3dwarehouse-classic.sketchup.com/model/ud381698a-9942-4e9b-b609-bd38fc2b6597/MIDI-SMD-female-plug-5-pin-DIN-part-number-SDS-50J)
is a useful lead. Uploader Filipe D. says it is a lightly adjusted/grouped
manufacturer model; that provenance is an uploader claim until an actual file
can be inspected. The listing is dated March 22, 2015 and reports millimeter
units, 725 polygons, 17 materials and 16 by 21 by 25 mm bounds. The refreshed
page displayed 216 KB, while an earlier classic view displayed 293 KB; neither
display is an obtained file's byte count.

The refreshed guest Download action required sign-in. The user subsequently
provided **MIDI+SMD.zip** and the native **MIDI+SMD.skp** through their own Chrome
download. The ZIP contains a COLLADA `model.dae` and a texture. All original
downloaded files and standalone conversions stay outside the published
repository. No credentials or account details are stored in these reports.

Fresh independent XML inspection resolves the COLLADA scene hierarchy and
affine matrices and applies its explicit **inch unit, 0.0254 meters per unit**
once. The actual exported world envelope is approximately **20.7 by 15.7 by
24.9 mm**, including projecting leads. It contains **44 geometry instances,
4,122 triangles, 2,362 line segments and 10 material entries**. Those actual
export counts and units differ from the listing's polygon/material/unit
metadata; neither set should silently replace the other. The file declares
SketchUp 15.3.331 and December 13, 2019 export timestamps. The separate SKP
header identifies SketchUp model version 21.0.0. These are export/container
metadata, not manufacturer release dates or verified factory provenance.

The front flange-like mesh cluster spans approximately **20.7 mm wide,
2.0 mm deep and 21.4 mm high**, compared with the current drawing's printed
20 mm width, 1.8 mm flange and 21.1 mm height. Lead geometry extends about
3.5 mm below the body bottom. The overall 24.9 mm height must therefore not be
compared directly with a 21.1 mm above-board body height. These differences
require a separate candidate review, without shrinking or trimming the model
to force a match. Its arbitrary geometry IDs supply no electrical pin-number
mapping.

The front flange-like group also uses a material named
`Metal_Aluminum_Anodized`, while the current SDS-50J drawing specifies a black
PBT housing. The uploader explicitly describes painting/texturing changes;
the export's material names cannot establish the actual molded part material
or prove the exact family/revision. No active model or scene is replaced by
this research.

`user-model-inspection.json` records the actual file hash, unit interpretation,
per-group/per-instance world bounds, materials and primitive counts.
`inspect_downloaded_dae.py` independently reproduces that read-only inspection
when given the local supplied DAE path. The parent also imported a standalone
conversion in Blender and obtained the same physical envelope; that evidence
does not change the still-qualified provenance or historical fit.

The older official DigiKey-model route on Same Sky redirects to an error page
and returns 404. The old cui.com route redirects to Bel Fuse and ends at 403.
The current exact product page lists a datasheet and PCB footprint, without a
verified downloadable 3D file. DigiKey's model page currently reports no model,
and the exact Ultra Librarian entry reports no 3D model; its DXF-2D export is
ECAD symbol/footprint data rather than a mechanical drawing of the connector.
These are bounded availability observations, not proof that no original CAD
exists anywhere.

No adjacent variant is accepted as exact: SDS-51J uses a 240-degree contact
arrangement, SD-50J is cable mounted, and SDF-50J has a different front shield.
The original BOM permits alternate jacks when their front pins match, which
does not establish identical bodies, seating, mold revision or plug engagement.

`cad-source-evidence.json` records the URLs, retained source hashes, family and
variant limits, guest barrier and subsequently supplied file receipts. The
parent research note is summarized here so this evidence remains in the
private repository. No third-party CAD file is incorporated or redistributed.

The existing four DIN openings and nominal source-derived body illustrations
remain unchanged. Existing scene checks describe flange contact at the panel's
inner face, a nominal 1.5748 mm recess, clear contact mouths and zero nominal
panel intersections. They do not qualify historical terminal registration,
complete plug engagement, mating forces or manufacturing tolerances.

Primary references:

- [Original BOM](https://www.ladyada.net/make/x0xb0x/fab/parts.html)
- [Official SDS-50J product](https://www.sameskydevices.com/product/interconnect/connectors/din-connectors/sds-50j)
- [Official dimensioned PDF](https://www.sameskydevices.com/product/resource/sds-j.pdf)
- [Official historical model route](https://www.sameskydevices.com/product/resource/digikey3dmodel/sds-50j)
- [DigiKey model availability](https://www.digikey.com/en/models/97033)
- [Exact Ultra Librarian entry](https://app.ultralibrarian.com/details/a50fd83e-bc57-11ed-b159-0a34d6323d74/Same-Sky/SDS-50J)

Manufacturer documents and model geometry retain their respective rights.
The original Eagle design retains Limor Fried/Adafruit's MIT notice. Original
audit code and notes are CC0-1.0. The supplied model's own terms and provenance
must be checked before redistributing it with the project.
