# Remaining component-model source review

This is a bounded source review of the **revision 9** model plan. It changes no
geometry, board, footprint library, assignment, or Blender scene. The full
70-row inventory, inherited limitations, source hashes and seven inventory
checks are in `remaining-quality-inventory-and-source-review.json`.

There are **491 fitted references**, comprising 409 on the main board and 82 on
the IO board. Every one has a visual model. A populated model is not a claim
that its manufacturer, installation height or mechanical fit is verified.

| Inventory group | Instances | Interpretation |
| --- | ---: | --- |
| Generic package illustrations | 373 | Library or project generic envelopes; exact fitted part is unconfirmed. |
| Qualified earlier original illustrations | 45 | Preserve the previous source and installation limitations. |
| Earlier illustrations with primary package dimensions | 7 | Includes the two Abracon resonators. |
| Recent detailed replacements | 47 | The detailed families delivered through revision 9. |
| Earlier body-only illustrations | 7 | Four rear connectors, two PTCs and the regulator in this baseline. Other revision-10 workstreams may supersede these separately. |
| Wire and termination illustrations | 12 | Explicit wire/termination studies; no invented connector housing. |

These counts describe the baseline, not a fresh dimensional certification of
all 70 rows. This review examines the PTC, 2SC536F and resonator families below.

## Recommended next work

**The 24 historical 2SC536F transistors offer the largest remaining repeated
model improvement.** They currently use 21 stock TO-92 package illustrations
and three qualified asymmetric lead-form illustrations. Recover the original
Sanyo SP/NP drawing and compare the original project part photograph before
rebuilding their bodies. The two lead forms must preserve the board's original
2.54 mm pitch and asymmetric 2.54/3.302 mm offsets, respectively.

**The two Micro-Ohm PTCs are the strongest remaining dimensional uncertainty.**
The original manufacturer URL currently returns 404. Keep their body size and
stand-off visibly qualified until a mechanical drawing or physical measurement
is available. Adding guessed terminals would hide that uncertainty.

**The two Abracon resonators are suitable for a later modest visual-detail
pass.** Their current maximum body dimensions and lead pitch are already
grounded in the manufacturer drawing. Better taper, shoulders and materials
would improve appearance, with the undocumented profiles kept illustrative.

## Micro-Ohm LPTC12T21001

The [original project BOM](https://ladyada.net/make/x0xb0x/fab/parts.html)
identifies two 1 kOhm PTCs, R100A/R100B, as Microohm LPTC12T21001. They are
serialized as R100A0/R100B0 in the imported board. Its original link is
`http://www.micro-ohm.com/temperature/temprecflm.html`.

The original project photograph was inspected. It shows an axial coated body
with colour bands and metal leads, without a scale. It establishes appearance,
not dimensions. A local copy is `sources/original-PTC-photo.jpg`.

The current 7.62 x 2.54 mm envelope comes from the original footprint outline;
0.4 mm stand-off, tapered ends, band positions and colour are illustration
choices. Both unknown leads remain omitted. The board pitch is 10.16 mm.

The original HTTP/HTTPS endpoint and the unhyphenated alternative each returned
404. A bounded archive-index request timed out after 20 seconds. Exact-number
and manufacturer-site searches did not recover a mechanical drawing. A glass
LPTC/KTY part from another manufacturer, or an LPTC choke, is not acceptable
dimensional evidence for this part. These negative results are documented in
`endpoint-attempts.json`; they are not evidence that no drawing exists anywhere.

## Historical 2SC536F

The original BOM calls for 24 TO-92 NPN devices bearing a 536F marking. The
revision-9 inventory contains exactly those 24 references. This pass recovered
and visually distinguished the following sources:

| Source | What was actually found | Decision |
| --- | --- | --- |
| Previously downloaded unnamed 2SC536 candidate | The page footer identifies SEMTECH ELECTRONICS LTD., dated 07/12/2002. O/Y/G/L gain bins and a pin drawing; no dimensional outline. | Does not establish historical 536F geometry. |
| [Futurlec's Sanyo-labelled PDF](https://www.futurlec.com/Datasheet/Transistor/2SC536.pdf) | The document itself is **2SA608N/2SC536N**, ENN6324, NPA-WA package 2164. | Do not silently replace the original part with the N variant. F/G gain ranks within the N device do not establish package identity. |
| Historical Sanyo scan compilation | SP/NP listings and discontinued-parts table; no accepted package outline. | Historical context only. |
| NP-package search result download | The mirror returned a discontinued-transistor table, printed page 38, followed by advertising, rather than the desired outline. | Rejected for package dimensions. The filename and provenance record describe the actual content. |
| [JSCJ current 2SC536 drawing](https://www.jscj-elec.com/gallery/file/2SC536%20TO-92%20V2.pdf) | Page 3 gives a valid contemporary TO-92 outline. A retained rendered page was inspected. | Already supports the generic asymmetric model; does not identify historical Sanyo 536F geometry. |

The JSCJ drawing supports a **generic** maximum envelope of 4.7 mm width,
3.7 mm depth and 4.7 mm height, typical factory pitch 1.27 mm and maximum lead
section 0.55 x 0.51 mm. It must remain attributed to that current manufacturer.
No new historical-F dimensions are adopted in this review.

A useful subsequent lead is the historical Sanyo **No. 333H** SP/NP drawing.
Search text from a mirrored scan describes the relevant variants, but the
actual dimensional image was not recovered and inspected during this pass.
It is a research lead, not an accepted mechanical source. The original project
part photograph should then establish which package matches the intended
appearance. Body stand-off, lead bending and trimmed tails would still need
separate installation assumptions or evidence.

## Abracon AWCR-MD resonators

The [Abracon manufacturer drawing, revised 05.07.13, page 3](https://media.digikey.com/pdf/Data%20Sheets/Abracon%20Corp%20PDFs/AWCR_MD.pdf)
was rendered and inspected. Its local PDF hash matches the source already
used in revision 5. No newly recovered body dimension was found.

| Drawing feature | AWCR-6.00MD low-profile bulk | AWCR-16.00MD bulk |
| --- | ---: | ---: |
| Maximum width | 9.5 mm | 10.0 mm |
| Maximum depth | 4.0 mm | 5.0 mm |
| Maximum body height | 6.5 mm | 10.0 mm |
| Nominal lead pitch | 2.5 +/- 0.3 mm | 2.5 +/- 0.3 mm |
| Lead width | 0.5 +/- 0.1 mm | 0.5 +/- 0.1 mm |
| Lead thickness | 0.25 +/- 0.1 mm | 0.25 +/- 0.1 mm |
| Factory bulk lead length | 5.0 +/- 1.0 mm | 5.0 +/- 1.0 mm |

Both board pitches are 2.54 mm, within the published range. The front drawing
is pin 3/output, pin 2/ground, pin 1/input from left to right. The existing
XTL1 model has a 180-degree rotation to match its source pad order; XTL2 does
not. These mappings are already documented in the current assignments.

The existing 0.35 mm stand-off, 2.5 mm trimmed tails, blue colour and profile
radii remain illustration choices. The original BOM permits another 6 MHz
resonator and says its colour might be orange. Factory lead length must not be
presented as a specified installed tail length. The drawing's taper/shoulder
appearance supports a visual refinement, but its coordinates and exact radii
are not fully dimensioned.

## Evidence and delivery notes

- `remaining-quality-inventory-and-source-review.json` contains all 70 rows,
  all 491 reference names, the three targeted family reviews and file hashes.
- `rendered/` contains the visually inspected package pages. Blank pages from
  imperfect historical mirrors are retained as retrieval evidence and are not
  used for dimensional claims.
- Source PDFs and original photographs retain their respective copyrights.
- The pre-existing Semtech candidate filename is retained for provenance;
  the review now identifies its publisher explicitly.
- Raw downloaded HTML and mirror advertising are retrieval evidence only.
  They are unnecessary for a user-facing model package.
- No geometry change or mechanical-fit approval follows from this report.
