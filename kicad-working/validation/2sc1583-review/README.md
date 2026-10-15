# Mitsubishi2SC1583 source archive and retained-model audit

The original Mitsubishi datasheet cited by the existing Q12/Q21/Q26 model was recovered from the older conversion workspace and added to `sources/mitsubishi-2sc1583.pdf`. Its SHA256 exactly matches the source hash already recorded by the model assignment. The PDF's first page was rendered and visually inspected. This closes a missing-source-file gap in a fresh repository download.

The existing model passes83 fresh exact BRep and PCB checks:8.1x3.6x5.6mm maximum body,2x2mm rear-top bevel,1.4mm rear-edge-to-lead-row dimension, five0.45mm round leads,1.25mm native pitch and original2.286mm installed PCB pitch. All15 actual native PCB pads at Q12/Q21/Q26 and all zero/unity model transforms were checked. Separate lead solids do not intersect. Each model, PCB and saved-scene input hash remains unchanged.

The2.8mm body standoff, formed lead curves,0.12mm embedding and2.5mm cut tails remain installation illustrations. The source specifies10.5mm minimum uncut lead length. Maximum package dimensions are not measurements of the physically fitted devices. Source pin roles are1/B1,2/C1,3/common emitter,4/C2,5/B2. This check does not certify circuit operation, tolerance, manufacturing or assembly.

`existing-model-audit.json` records source provenance, dimensions, pin sections, actual pads and checks; `audit_existing_model.py` replays them with FreeCAD's bundled Python. Original source rights are retained.
