# Additional integrated-circuit and resonator illustrations

Five original CC0 STEP illustrations support **seven component positions**:

| Component | References | Body dimension basis | Exact PCB lead pitch |
|---|---|---|---|
| Sanyo LA4140 | IC14 | Printed 22.3 × 3.0 mm, maximum 5.7 mm height |2.54 mm|
| ROHM BA6110 | IC15B0 | Nominal 21.8 × 2.8 × 5.8 mm, each ±0.2 mm |2.54 mm|
| Mitsubishi 2SC1583 | Q12,Q21,Q26 | Maximum 8.1 × 3.6 × 5.6 mm |2.286 mm, explicitly fanned from native1.25 mm|
| Abracon AWCR-6.00MD | XTL2 | Maximum 9.5 × 4 × 6.5 mm |2.54 mm, within manufacturer2.5 ±0.3 mm|
| Abracon AWCR-16.00MD | XTL1 | Maximum 10 × 5 × 10 mm |2.54 mm, within manufacturer2.5 ±0.3 mm|

The source Eagle value `LA44140` identifies LA4140 through the original BOM;
the value field is not changed. Optional BA662A/IC15A0 remains without a model
and its population metadata stays unchanged. Q22/2SC2291 also remains without
a model because no primary-authored package dimensions were recovered. Its
shared SSIP5 footprint name does not establish the same body as2SC1583.

These are **original parametric illustrations**, not exact manufacturer CAD
or measurements of fitted physical parts. Max-body envelopes and nominal
bodies are distinguished in the manifest. Mounting standoff, trimmed lead
length, lead bending, body drafts/rounding, colors and omitted printed marks
are explicitly documented illustration choices.

The 2SC1583 native drawing has 1.25 mm lead pitch and 0.45 mm round leads, while the
board holes use2.286 mm pitch. Its model shows deliberate lead fan-out above
the PCB. The body stands 2.8 mm above the top surface, and the five leads become
vertical before reaching it. The drawing's 10.5 mm minimum uncut leads allow
forming and trimming, but the chosen installed height/bend is not a physical
assembly measurement.

Pin identities follow primary drawings. SIP pin1 and2SC1583 pin1/B1 are at
negative model X. The 2SC1583 flat front points toward negative model Y and its
sloped upper rear toward positive Y. Abracon's front view has pin3 at negative X,
pin2/GND in the middle and pin1 at positive X. XTL2 directly matches that order.
XTL1 uses a 180 degree model rotation to place manufacturer pin1 on source
pad1 at negative footprintX. Its original net identities remain unchanged.

SIP9 and SSIP5 are shared library footprints for different components. These
models require **per-instance assignments**. They must not be applied as one
shared cache default to optional BA662A or unsupported2SC2291. No footprint
ID, placement, pad, drill, net, rule or routing change is part of this work.

Sources:

- [Sanyo LA4140 ENN528D,page1](https://static.chipdip.ru/lib/301/DOC000301904.pdf),
  retained in the previous review with readable package dimensions.
- [ROHM BA6110/BA6110FS,page7](https://datasheet.datasheetarchive.com/originals/library/Datasheet-0103/DSA003839.pdf),
  retained in the previous review.
- [Original Mitsubishi 2SC1583 Japanese datasheet,page1](https://www.radioradar.net/en/files.html?fid=502807),
  retained locally in `reference/2SC1583-Mitsubishi.pdf`.
- [Abracon AWCR-MD,revised2013-05-07,page3](https://media.digikey.com/pdf/Data%20Sheets/Abracon%20Corp%20PDFs/AWCR_MD.pdf),
  retained in `validation/reference-pdfs/awcr-md.pdf`.
- [Original expanded BOM](https://wiki.ladyada.net/x0x/billofmaterials),
  identifying AWCR-16.00MD at XTAL1 and AWCR-6.00MD at XTAL2.

`integrated-model-manifest.json` supplies per-reference model paths, hashes,
transforms, classifications, source records and limitations.
`integrated-model-records.json` records the generator/helper hashes, body and
lead dimensions, exact pad-center checks against the actual PCB, colors and
geometry validity. `integrated-full-thickness-audit.json` independently reads
the exported STEP and samples lead cross sections at seven planes through
the nominal 1.6 mm board thickness, using actual placed-pad drill diameters.

The generator and STEP presentation helper are self-contained in this folder.
Run `generate_integrated_illustrations.py`, followed by
`audit_integrated_full_thickness.py`, with the bundled FreeCAD Python. They
write only these review artifacts and read the actual PCB files.

No fabrication, selected-part tolerance, socket, enclosure or physical
assembly approval is implied by a clean modeled-lead check.
