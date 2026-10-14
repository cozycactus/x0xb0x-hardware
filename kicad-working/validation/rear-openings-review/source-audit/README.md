# Installed rear connector openings

The installed source STEP models have open mating faces. This independent check
covers five families and all eleven rear connector references in KiCad revision
11, without changing the projects, models, scene or routing. It is separate from
the Blender scene check: duplicate presentation hardware can still obstruct an
otherwise open source model.

The exact BRep review passes 61 checks. It reads the actual model assignments
from the current I/O board, checks all zero/unity model transforms, verifies that
each installed front faces the rear edge, and probes real solid geometry along
the mating passages. All installed STEP and PCB hashes remain unchanged.

| Family | References | Source opening |
| --- | --- | --- |
| NYS216 | HEADPHONE0, MIXIN0, MIXOUT0 | Open 6.35 mm bore through the nose, continuous central passage through the ribbed housing. Contact strips occupy one side. |
| SDS-50J | DIN1-DIN4 | Open recessed socket face and five open contact mouths. The reconstructed holes are blind behind the insert at canonical Y = 7.4 mm. Their depth remains illustrative. |
| MJ-3536N | CV0, GATE0 | Open 3.6 mm bore and continuous central passage. An upper contact leaf intrudes into the bore further inside; this is not a closed face. |
| PJ-202AH | POWER0 | Open 6.5 mm mouth around the recessed 2 mm center pin. The pin correctly obstructs the centerline, while the annular plug passage remains open. |
| Generic USB-B | USB0 | Open chamfered shell/insulator mouth around its recessed tongue. The central tongue is expected connector geometry. |

No source-model correction is needed to resolve a closed mating face. The next
correction belongs to any solid presentation disks, washers or nuts in the
Blender scene that overlap these existing openings. Do not remove the actual
PJ center pin or USB tongue to make a centerline ray pass.

The exact reviewed input hashes, canonical probe dimensions and all check
results are in `source-opening-audit.json`. Run the accompanying
`audit_source_openings.py` using the local FreeCAD Python runtime to reproduce
the checks. It writes only its report in this directory.

## Source and dimension limits

The retained manufacturer drawings were reviewed visually. The current
[SDS-J drawing, page 3](https://www.sameskydevices.com/product/resource/sds-j.pdf)
shows the five socket mouths and the 7 mm contact circle. Contact-hole depth,
socket stock and other small internal details in the source reconstruction are
unsized illustrations. These probes prove a visible geometric opening, not
physical plug insertion or electrical contact.

The audio source uses the retained older
[REAN NYS216 DXF](https://www.rean-connectors.com/media/12224/download/nys-216-1.dxf?v=1),
drawing 3102 ST 22 01, revision C (2007), which calls out a 3/8-32 UNEF thread.
Its source nose major diameter is therefore 9.525 mm. The retained
[2015 manufacturer PDF](https://www.rean-connectors.com/media/9014/download/nys-216.pdf?v=1)
instead calls out M11 x 1.25 for the same named family. This is a documented
revision discrepancy; hardware for those threads must not be claimed
interchangeable. That PDF's washer section clearly dimensions the inner bore
as 11.3 mm, outer diameter as 15.3 mm and thickness as 1.2 mm. The scene's three
washers retain that 11.3 mm through-bore and their previous exterior envelopes.
The three nuts instead use a 9.6 mm plain through-bore, chosen as illustrative
clearance around the installed older 9.525 mm source nose; this is not a
manufacturer nut specification or a modeled female thread. The resulting
scene hardware combines retained washer dimensions from the newer drawing
with nominal clearance for the older native nose. True thread compatibility,
historical hardware identity and installed seating remain unqualified.

The [MJ-3536N drawing](https://www.sameskydevices.com/product/resource/mj-3536n.pdf)
and [PJ-202AH drawing](https://www.sameskydevices.com/product/resource/pj-202ah.pdf)
show open mouths and their expected contacts. The current body reconstructions
retain those nominal diameters. Their unsized reconstructed spring stock does
not establish operating contact travel. The generic USB-B source retains the
original BOM envelope from the saved KC-301021 PDF text extraction; an exact
historical PN61729 factory model has not been recovered.

Generated audit code is CC0-1.0. Manufacturer source drawings retain their
respective rights.
