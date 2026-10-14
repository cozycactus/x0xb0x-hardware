# x0xb0x assembly — Blender revision 9 / KiCad revision 11

Open `x0xb0x-populated-with-case.blend`. All 491 fitted components are embedded: 409 mainboard and 82 I/O. No external board exports are required to view the assembly. Revision 8 remains unchanged alongside this version for comparison.

## Rear connector correction

Five obsolete solid presentation disks covered the already-open native connector mouths: CV OUT (`CV0`), GATE OUT (`GATE0`), HEADPHONE (`HEADPHONE0`), MIX IN (`MIXIN0`) and MIX OUT (`MIXOUT0`). Exactly those five ` / jack recess proxy` objects are removed. The six existing nuts and washers for the three audio connectors also lacked bores; the nuts now have nominal 9.6 mm clearance holes and the washers have their original manufacturer-based 11.3 mm holes, all on the native socket axes. Their original outer boundaries, poses and material links remain. The installed drawing-derived NYS216 model has a 3/8-32 UNEF (9.525 mm major diameter) nose from the recovered 2007 drawing; 9.6 mm is an illustrative nut clearance choice, not a manufacturer hardware dimension. The later 2015 M11 drawing is not treated as interchangeable.

The original native connector models, bores, bushings and contacts are retained in full. Connector cavities have finite depth; the power jack still has its intended center contact and the MIDI sockets have their intended contact insert.

The retained hardware dimensions come from `../blender-case-revision-7/bom-parts/scene-part-dimensions.json` and the [2015 manufacturer NYS216 PDF](https://www.rean-connectors.com/media/9014/download/nys-216.pdf?v=1). The native connector nose comes from the separate [2007 revision-C manufacturer DXF](https://www.rean-connectors.com/media/12224/download/nys-216-1.dxf?v=1), preserved with its provenance under `../blender-case-revision-7/quality-model-sources/rear-quality/`. This mixed historical illustration basis is explicit; threaded hardware interchangeability is not established.

Native connector bodies and contacts, panel cutouts and all component positions are preserved. Only the specified presentation disks and hardware bores change. This correction changes only the Blender assembly. KiCad remains revision 11, with its previous geometry and validation findings unchanged.

## Preserved assembly

Apart from the six bored hardware meshes, every remaining mesh, material, transform, hierarchy, source collection, animation curve, editable label, camera and wire is preserved from revision 8. All 40 complete PCB-mounted LED assemblies and their clear unlit shaders remain. All 23 button caps retain their PCB parent and assembled pose. The historical Sanyo transistor and Abracon resonator improvements from revision 8 remain, with their documented dimensional and fitted-part qualifications.

## Views

- Frame 1: assembled enclosure.
- Frame 80: exploded enclosure and boards; LEDs and caps follow the PCB.
- Frame 120: control-side inspection with the panel and caps hidden.
- Frame 160: wiring study with caps hidden; physical routing and wire length remain qualified.

The rear camera is also available. `rear.png` is the normal rear view. `rear-openings-closeup.png` is an additional read-only diagnostic render; its camera is not added to the saved scene.

## Verification and limits

`verification/final-saved-scene-audit.json` compares both saved scenes and allows exactly the five named disk removals, six hardware bore corrections, explicit revision metadata and this embedded guide. `revision-9-change-record.json` records the preserved baseline and saved scene hashes. Independent rear opening checks are recorded separately. The original panel drawings and design license remain at `../blender-case-revision-7/source/`.

Fresh KiCad revision-11 ERC/DRC findings remain recorded separately. The existing three connection gaps and board/parity warnings remain. Exact spacer molding, cap sockets/travel, historical fitted parts, installed lead forming, enclosure tolerances and physical assembly remain unqualified. No physical connector fit, wire-routing or fabrication certification follows from this visual correction.
