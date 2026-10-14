# Revision 5 passive/discrete illustrations

**Integration ready: 45 additional instances, 15 original STEP assets.**
The manifest is `passive-assignments.json` and `generation_complete` is true.
It selects 36 mainboard and 9 I/O instances. Every additional model uses offset
0,0,0; rotation 0,0,0; and scale 1,1,1. Actual project and candidate files were
not changed by this work.

The original BOM resolves the misleading imported package names. In particular
**C42 and C62 are Kemet T350 tantalum drops**, despite their inherited E2,5-7
package name. C17 uses the Xicon XRL family and C3/C5 use the 2200 uF XRL family.
The ceramic/film reference groups identify AVX SR205, Xicon PM and Xicon PF
families. The three asymmetric transistor positions are 2SC536F-family devices.
[Original parts list](https://www.ladyada.net/make/x0xb0x/fab/parts.html),
[expanded original BOM](https://ladyada.net/wiki/x0x/billofmaterials).

| Illustration family | Instances | Documented body width x depth x height | Factory pitch / actual source pitch |
|---|---:|---|---|
| AVX SR205 ceramic | 16 | 5.08 x 3.175 x 5.08 mm | 2.54 / 2.54 mm |
| Xicon PM2A102 | 3 | 5.5 x 3 x 7.5 mm | 3.5 / 3.556 mm |
| Xicon PM2A103 | 5 | 6 x 3.5 x 7.5 mm | 3.5 / 4.064 mm |
| Xicon PM2A333 | 5 | 6.5 x 4 x 9 mm | 3.5 / 4.064 or 5.08 mm |
| Xicon PF2A183 | 1 | 7 x 4 x 12 mm | 4 / 4.064 mm |
| Xicon PM2A104 | 3 | 8.5 x 6 x 11.5 mm | 5 / 5.08 mm |
| Xicon PM2A224 | 1 | 11.5 x 7 x 13 mm | 7.5 / 7.62 mm |
| Xicon PF2A683 | 1 | 9.5 x 5 x 13 mm | 7.5 / 7.62 mm |
| Xicon PM2A473 | 1 | 7.5 x 4 x 9.5 mm | 5 / 5.08 mm |
| Xicon PF2A682 | 1 | 6 x 3.5 x 10.5 mm | 3.5 / 3.81 mm |
| Kemet T350A105K035AT | 2 | 4.5 diameter x 7.1 height mm | 2.54 / 2.54 mm |
| Xicon XRL50V1.0 | 1 | 5 diameter x 11 height mm | 2 / 3.556 mm |
| Xicon XRL16V2200 | 2 | 13 diameter x 20 height mm | 5 / 5.08 mm |
| Generic 2SC536-family TO92 | 3 | 4.7 x 3.7 x 4.7 mm | 1.27 mm stems formed to +2.54, 0, -3.302 mm holes |

The PM333 family has two assets because C26 has a different actual source
pitch. **C18 shares an imported footprint name with other capacitors but uses
a distinct PF183 body**; the manifest deliberately assigns it separately rather
than forcing one body onto the entire footprint cache.

Primary dimensional drawings are:

- [KYOCERA AVX SR series](https://datasheets.kyocera-avx.com/SR-Series.pdf), SR20 body/lead tables and package drawings.
- [Xicon PM manufacturer datasheet](https://www.mouser.com/datasheet/2/70/pm-190464.pdf), 100 V body/pitch/0.5 mm lead tables.
- [Xicon PF XC-600181](https://www.mouser.com/ds/2/70/XC-600181-187468.pdf), 50/100 V body/pitch/0.5 mm lead tables.
- [Kemet T350A105K035AT manufacturer specification](https://search.kemet.com/component-documentation/download/specsheet/T350A105K035AT), 4.5 mm diameter, 7.1 mm seated height, 2.54 +/-0.38 mm pitch and 0.50 +/-0.05 mm leads.
- [Xicon XRL XC-600178, 2007 revision](https://www.mouser.com/datasheet/2/231/XC-600178-1174881.pdf), can size, lead pitch and lead diameter tables. Its 13 mm can uses **0.6 mm leads**; this is a newly generated documented-family illustration, not a thinned version of the previously rejected stock model's 0.9 mm leads.
- [JSCJ 2SC536 manufacturer drawing](https://www.jscj-elec.com/gallery/file/2SC536%20TO-92%20V2.pdf), maximum TO92 envelope and 0.55 x 0.51 mm rectangular leads. This supports a generic TO92 illustration and does not identify the historical F-bin manufacturer.

AVX, Kemet and JSCJ PDFs were saved and their relevant drawings rendered and
visually inspected. Their download hashes are under `reference-documents`.
Xicon manufacturer-authored documents were available through indexed primary
PDF content, but local PDF downloads returned distributor blocks/HTTP 403;
no local Xicon PDF copy or visual PDF inspection is claimed. The selected
numerical rows and URLs are recorded explicitly in the generator and records.

## Lead geometry and polarity

The generator reads the immutable revision-4 input snapshot and verifies every
actual instance's local pad centers, drill diameters, pad names and net metadata.
The manifest records the PCB hash, local footprint hash and per-reference
pad-geometry hash. The STEP leads terminate at those exact source hole centers.

Lead forming occurs above the board; the entire modeled board thickness retains
straight leads centered in the holes. After STEP export/reimport, closed sections
are checked at 18 depths from Z=0 through Z=-1.6 mm, including the independent
audit planes **-0.05, -0.8 and -1.5 mm**. Each section's center and circumscribed
radius are checked against the original drill. Every generated body, marking
and lead is valid, and fusing all pieces produces one valid connected solid.
Export/reimport solid counts and volumes are checked.

Tantalum model positive lead and the curved positive `+` annotation map to the
actual source pad `+` at negative X. The XRL negative lead and negative stripe
map to actual source pad `-` at positive X. These checks use the saved pad names,
not an assumed numeric convention. TO92 flat sides remain at positive PCB Y,
while stems bend to the original asymmetric pad positions. Electrical pad
numbers and nets are not changed.

## Body envelopes and explicit illustration choices

Manufacturer dimensions are retained even where the old silk is smaller.
Each manifest row and dimensional record lists the affected references and the
**documented body width/depth minus the historical silk width/depth**. These
differences do not justify changing the PCB or silently shrinking the models.
The source footprints do not provide component heights.

The can and body dimensions above come from primary drawings; mounting gaps,
fillets, ellipsoidal drop silhouette, colors, marker typography and detailed
lead paths are explicit illustration choices. PM/PF mounting gaps are 1.5 mm,
with 2.0 mm for the C26 formed-lead variant. The AVX gap is 0.5 mm. The tantalum
gap is 0.35 mm and its curved positive annotation uses an approximately 0.01 mm
paint layer. C17's formed-lead gap is 2.0 mm; C3/C5 use 0.8 mm. The asymmetric
TO92 model uses a 3.2 mm gap to accommodate its explicit formed leads.

XRL values are nominal can dimensions; the manufacturer's +/-1 mm diameter,
and +/-1.5 mm length tolerances remain unmodeled. These illustrations do not
establish the dimensions, series revision, forming or mounting heights of real
fitted components, assembly tolerances, panel/enclosure fit or fabrication
readiness. Body collision review belongs to the integrated candidate and cannot
be inferred from this package-local validation.

The two thermistors R100A0/R100B0 remain unassigned. The original BOM identifies
Microohm LPTC12T21001, but no authoritative body drawing was recovered. A generic
resistor or thermistor body was not substituted.

## Reproduction and license

Run `generate_passive_illustrations.py` with FreeCAD's bundled Python. The script
reads only the input snapshot and writes this review directory. Its SHA-256,
FreeCAD version, per-asset dimensions, all depth sections and model hashes are
in `passive-dimensional-records.json`. Logs are retained.

All new generator code and generated STEP geometry are original CC0-1.0 work.
Primary manufacturer documents remain their authors' material and are excluded
from that dedication. No stock model geometry was copied, scaled or thinned.
