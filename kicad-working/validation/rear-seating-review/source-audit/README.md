# Rear connector seating: source basis

This is a read-only review for the current Blender revision 10 assembly. It
separates original manufacturing dimensions and assembly instructions from the
presentation's chosen PCB/body datums. It makes no PCB, STEP, scene or placement
change, and does not establish physical fit.

The original author's download page specifies **0.062 inch sheet**, equivalent
to **1.5748 mm**. The PacTec PT-10 drawing agrees and gives the rear plate as
8.580 by 2.070 inches. The retained original rear DXF contains nine circular
cuts and two rectangles, with no separate DIN flange screw pattern. Fresh
checks compare every circular and rectangular cut's retained handles and
coordinates against the original DXF bytes.

The original finishing manual attaches the rear panel through the three
quarter-inch audio jacks. The I/O manual directs the builder to hold the DIN
faces flush with the PCB edge while soldering, using a strong mechanical solder
bond. Neither instruction supplies a numerical rear-PCB setback or an explicit
audio washer-side sequence. Body shoulder, panel, washer, then nut is a
reasonable assembly interpretation; it must remain identified as an
interpretation rather than a measured historical stack.

| Connector | Existing source datum | What the source establishes |
| --- | --- | --- |
| Three NYS216 audio jacks | Canonical body shoulder Y = 0; nose Y = -8.5 mm; axis Z = 8 mm | The older DXF gives the 8.5 mm nose and 3/8-32 thread. Registration of that reconstructed shoulder at the old footprint origin is not confirmed terminal-fit evidence. |
| Four SDS-50J DIN jacks | Front flange Y = 0; back Y = 1.8 mm; axis Z = 10 mm | Current family flange thickness is printed. The original manual seats its front flush with the PCB edge; the face need not be flush with the outer panel face. |
| CV/GATE MJ-3536N | Body shoulder Y = 0; nonthreaded bushing tip Y = -3 mm; axis Z = 5.5 mm | Printed 3 mm projection and 6 mm bushing diameter. No external mounting nut is established for this family. |
| PJ-202AH power jack | Front Y = 0; body extends to Y = -14.4 mm; axis Z = 6.5 mm | Printed body and mouth geometry, with the actual footprint's 180-degree rotation applied externally. No panel-clamping nut. |
| Generic USB-B | Front Y = 0; body into +Y; nominal illustration axis Z = 5.31 mm | The envelope comes from original-BOM 154-2442-E. Half-height 5.31 mm is a presentation choice, not a recovered PCB-to-port center datum or proof of PN61729 identity. |

Canonical Y directions here are model coordinates; each actual footprint and
the assembly transform must be applied before comparing with the rear panel.
The machine-readable report records actual native assignments and their hashes.

If the audio body shoulder were seated on the inner panel face, the combined
nominal stack would leave **0.7252 mm** of the 8.5 mm nose beyond the outer nut:
8.5 - 1.5748 - 1.2 - 5. This arithmetic combines the older nose with newer
hardware dimensions. It does not certify their different threads, historical
hardware identity or physical engagement. Similarly, a 3 mm MJ bushing seated
at the inner face would project **1.4252 mm** past the outer panel, and a DIN
front at the inner face would remain **1.5748 mm recessed**. These are
conditional examples, not required placement corrections.

## Remaining registration uncertainty

The earlier display placed PCB Y = 0 at the panel's inner face. All three
original audio footprints and a detached historical Dimension strip instead
have their front datum at KiCad Y = +0.508 mm. The strip might represent a panel
cross-section, but its width and thickness differ from the original panel and
its identity is unproven. This evidence supports investigating an axial datum
mismatch; it does not justify an arbitrary board translation or a change to
native geometry.

The earlier height choice based on the MJ axis gives the seated PCB top
6.184 mm above the panel bottom, while the NYS216 drawing gives 6.351 mm. The
0.167 mm difference remains a nominal family/seating ambiguity. Existing notes
saying that no connector CAD was installed are historical: detailed native
connector illustrations now exist, but historical terminal registration and
seating are still unqualified.

The case's rear-panel depth was traced from PacTec section C-C, rather than a
printed setback; its stated visualization uncertainty is approximately
plus or minus 0.5 mm. The lower-edge placement uses detail D and retains a
conflicting undimensioned rear-silhouette reading. Those uncertainties must not
be silently converted into exact seating evidence.

## USB drawing refresh

The primary KC-301021 PDF is now available as indexed web text. It confirms the
154-2442-E body at 12.04 by 16 by 10.62 mm, aperture 8.45 by 7.78 mm, recommended
PCB thickness 1.57 mm and maximum panel thickness 2.67 mm. Local binary retrieval
failed with an HTTP/2 error; a bounded HTTP/1.1 retry received no bytes and was
stopped. No valid PDF was saved or visually inspected in this refresh, and no
new front-lip, PCB-to-body or aperture-center datum is asserted. The original
BOM permits different through-hole USB-B jacks, so the existing PN61729
footprint does not establish an exact 154-2442-E part identity.

`seating-source-audit.json` supplies retained source hashes, original hole
geometry, current model assignments, conditional stack arithmetic and bounded
action recommendations. `usb-primary-retrieval.json` records the USB refresh
and its limits. `collect_seating_sources.py` reproduces both reports from
read-only inputs and writes only to this folder. The independent scene audit
must supply actual evaluated axial gaps, intersections and cutout clearances
before any presentation correction is selected.

## Current scene findings and limited presentation correction

The independent scene reviewer reports the three audio body shoulders
penetrating 0.508 mm past the panel's inner plane. This is an actual
intersection in the current model, even though historical shoulder/terminal
registration does not establish one universal physical correction. POWER0 and
USB0 also have approximately 0.081 mm of nominal body overlap below the
original rectangular opening's lower edge. Exact mesh intersections and port
clearances are measured in the separate scene audit. The existing audio
washers and nuts already sit outside the panel in the chosen order.

These per-port conflicts remain documented. Blender revision 11 will preserve
the native connectors, PCB, enclosure, panel and hardware positions. The
available source evidence does not justify moving the whole board to hide one
family's mismatch or changing the original openings.

The original rear DXF contains manufacturing annotations, but **no actual
control legend or silkscreen artwork**. The current editable rear text is
presentation artwork. Its selected correction places the same glyph geometry
on the rear plate with a 0.01 mm outward rendering offset, preserving text,
font, material and in-plane position. A flat physical plate supports the flat
legend placement; the offset and existing typography are not manufacturer
dimensions or recovered original artwork. This visual correction does not
resolve or conceal the connector seating conflicts.

## MJ-3536N axis height (follow-up to Blender revision 15)

Blender revision 15 seats the I/O board on the rear DXF's 0.250 in datum.
The CV0/GATE0 holes sit 0.460 in above the plate edge, which is 0.21 in
(5.334 mm) above that datum, against the modelled 5.5 mm jack axis. The two
manufacturer sheets already retained in
`kicad-working/validation/models-review-10/rear-connector-quality/sources/`
date that axis:

| Sheet | SHA256 (prefix) | Axis above body bottom | Tolerance |
| --- | --- | --- | --- |
| `mj3536n-2020.pdf` (CUI, 2020-02-10) | `09fc1510` | 5.5 [0.217] mm | X.X ±0.2 mm |
| `mj-3536n-current.pdf` (Same Sky, 2024-09-12) | `aa1de851` | 5.50 mm | X.XX ±0.20 mm |

The revision history in both sheets lists the 2005-11-17 initial release, PCB
slot dimensions added on 2010-10-07 and only a brand update on 2020-02-10.
Re-engineering is recorded only from 2023. The mechanics drawn in 2020,
including the 5.5 mm axis and Ø6.00 mm bushing, therefore stand for the part
available in 2007. The 2023/2024 re-engineering kept the same 5.50 mm axis.
The 2010 sheet itself was not retrieved; the revision-10 source review records
the same limit.

The 0.21 in hole position therefore reads as an inch rounding of the 5.5 mm
axis, 0.166 mm low and inside the part's ±0.2 mm tolerance. It is not evidence
of a lower historical axis. Revision 15 keeps the 5.5 mm model, so the nominal
Ø6.00 mm bushing clears the Ø6.35 mm hole by about 0.005 mm. That is a
tolerance stack in the original design, not a modelling error, and no
geometry change follows. This supersedes the revision-15 README's remark that
the question needed the period drawing.

Primary references: [original downloads](https://www.ladyada.net/make/x0xb0x/download.html),
[original finishing](https://www.ladyada.net/make/x0xb0x/fab/finish/index.html),
[original I/O assembly](https://www.ladyada.net/make/x0xb0x/fab/ioboard/),
[PacTec drawing](https://www.farnell.com/datasheets/1483254.pdf),
[NYS216 older DXF](https://www.rean-connectors.com/media/12224/download/nys-216-1.dxf?v=1),
[NYS216 newer PDF](https://www.rean-connectors.com/media/9014/download/nys-216.pdf?v=1),
[SDS-J drawing](https://www.sameskydevices.com/product/resource/sds-j.pdf),
[MJ-3536N drawing](https://www.sameskydevices.com/product/resource/mj-3536n.pdf),
[PJ-202AH drawing](https://www.sameskydevices.com/product/resource/pj-202ah.pdf),
[USB BOM drawing](https://www.mouser.com/catalog/specsheets/KC-301021.pdf).

Manufacturer sources retain their respective rights. Original panel design
files retain Limor Fried/Adafruit's MIT design notice. Original audit code and
notes are CC0-1.0.
