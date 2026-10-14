# Independent revision-10 model review

**PASS for the qualified local visual-model update: 746 independent checks,
zero failures.** This is the final review of the authoritative candidate with
45 updated references, including the corrected PJ model and all 40 LEDs.
The complete checks, source hashes and inherited limitations are in
`independent-quality-review.json`.

No candidate, live project, source geometry or Blender scene was edited by
this reviewer. Temporary read-only audit programs and intermediate results
were written outside the project; only this report and its companion JSON
were written in the revision-10 review workspace.

## Project preservation

- All **243 immutable revision-9 input files** match their input-manifest
  hashes. All baseline files remain present.
- **232 prior files are byte-identical**. Exactly **11 planned existing
  files** change: two PCB files, five footprint model-path caches, and the
  two model-provenance/README pairs.
- Exactly **seven planned new files** exist: five STEP assets and two
  board-specific source records. The candidate has **250 project files**.
- All **75 PCB/footprint non-model ASTs** are identical. Copper, pads,
  drills, nets, placement and outline are preserved. Schematics and project
  settings are byte-identical. Every model offset, rotation, scale and
  ordering is preserved.
- All **491 fitted references** remain populated: **409 mainboard / 82 IO**.
  Exactly **45** references change model assets, with **446 unchanged**.
- The changes are LED1-LED40, IC20, KK1, CV0, GATE0 and POWER0.
- Optional IC15A0 and seven actual non-plated mounting holes retain their
  earlier model-free state. The heterogeneous SSIP5 cache stays unchanged
  and model-free.
- All prior STEP assets and earlier provenance entries remain byte-identical.
  Native `.kicad_prl` preferences and transient `~*.lck` files are explicitly
  excluded as session artifacts; no other candidate file is ignored.

## Fresh geometry review

All five final STEP assets were freshly loaded in FreeCAD. Each contains
valid, positive-volume solids, the intended solid count and matching
optimized surface bounds/manifest volume. Bounds are compared with a
0.000001 mm numerical tolerance; the folded heatsink's optimized bound
includes about 0.0000001 mm of kernel tolerance.

| Final asset / fitted references | Solids | Faces | Volume, mm3 |
| --- | ---: | ---: | ---: |
| Bent IC20 body/tab | 2 | 13 | 486.063483 |
| Bent KK1 complete folded spring | 1 | 86 | 797.077410 |
| MJ-3536N, CV0/GATE0 | 5 | 57 | 1133.123461 |
| Corrected PJ-202AH, POWER0 | 5 | 50 | 1048.635554 |
| Raised generic LED, LED1-LED40 | 3 | 20 | 156.292282 |

The exact source/candidate hashes are pinned in the JSON. The active PJ hash
is `5d933e75182d55843d288f0a54383960b5f897a1db058c6c1dc1efe75817908e`.
The active LED hash is
`2a61af0d1b2a4ef8f4e8ddda40651a13ee141cf824938d16ae99e5583483d987`.

## LED installation and appearance

Fresh independent exact BRep comparison confirms that the complete official
generic LED geometry above its old Z=3 mm lower-body plane is retained under
a rigid **+3.096 mm lift**. The new lower-body seat is **6.096 mm** and the
tip is **14.696 mm** in the original source frame. No body scaling or head
shrinking occurs.

Both full **0.4 x 0.4 mm** square leads retain their original source axes at
X=0 and X=2.54 mm, with continuous tails from Z=-2.5 to Z=6.096 mm. Fresh
sections at eight depths per lead confirm the full 0.16 mm2 section. The
two-lead pitch and stock-head shape remain unchanged. All 40 placed models
retain the earlier native **offset [1.27, 0, 0], rotation [0, 0, 180] and
unity scale**.

The linked source audit checks all **80 original 1 mm holes** and polarity
mapping. Their nominal square-corner radial margin is **0.217157 mm**. This
is nominal geometry, not a tolerance or fitted-part certification.

The primary BOM explicitly names **0.24-inch VCC STD240B** spacers; the
original sequencer table instead says **0.22 inch**. Both were checked in
the retained original text. The selected **6.096 mm** seat therefore remains
qualified against the **5.588 mm** alternative. No exact spacer outline was
recovered, and no invented black spacer solid is included. Clear/unlit lens
appearance and Blender optics remain presentation choices; the actual LED
manufacturer, package tolerances and installed cut lengths are unresolved.

The native LED preview was visually inspected: continuous full-width leads
connect the nominal PCB holes to the raised head. Final full-scene panel
projection and removal of duplicate presentation lenses belong to the
separate saved-Blender validation, not this read-only candidate review.

## Bent regulator and heatsink

The retained original-author instruction says to bend IC20 back before
fitting the heatsink. The place/soldered photos were inspected and support a
body/tab approximately parallel to the PCB, extending beyond its edge.
They do not measure the exact **90-degree bend** or **2 mm vertical datum**;
those remain explicit installation illustrations.

The complete full-size regulator body/tab and revision-9 heatsink are retained
by rigid transforms. The heatsink's **21.84 x 10.03 x 19.05 mm** source
envelope, **0.63 mm** sheet and correct **11.81 mm** hole datum are retained.
The relative native footprint datum remains **1.27 mm**, independently
checked by the pair export. No source body, fold, finger or neighboring part
was shrunk or trimmed to improve the screen.

The pair retains **1.729422 mm3** of free-state spring-finger intersection
with the regulator, with **zero intersection outside the finger mask**.
All six exact comparisons against **C3, C4 and C5** have zero intersection.
The separate native saved-scene screen reports no new neighbor/case surface
pairs in its stated scope.

These results do not simulate spring deflection, clamp force, thermal contact
or physical tolerances. IC20 leads remain omitted because their original
vendor, forming and hole fit remain unresolved.

## Rear connector source interpretation

The retained MJ 2020/current mechanical pages and PJ 2015 page were visually
inspected. The MJ historical **11.2 mm** line is terminal 1-to-terminal 3;
current nominal terminal stations at **2.3, 13.5 and 16 mm** from the front
datum agree with that chain. The final source notes retain this interpretation
and the manufacturer's reengineering caveat. Equal nominal dimensions do not
prove unchanged molds or tolerances.

The MJ body remains **10 x 15.8 x 10 mm**, with the correct **nonthreaded
6 mm bushing**, **3.6 mm aperture** and **5.5 mm axis height**. The PJ body
remains **9 x 14.4 x 11 mm**, with **6.5 mm aperture/axis height** and
**2 mm mating pin**. Minor rails, windows, contact leaves, stock gauges,
seams and radii remain unsized visual interpretations.

The final PJ reconstruction removes the unsupported plastic rear recess.
The manufacturer's **diameter 1.5 mm callout belongs to a terminal eye**.
The superseded PJ asset is absent from the active candidate, while its
historical frozen file is preserved outside the active portable assets.

Below-seat terminals and locators remain omitted. Original round PCB drills
and the manufacturer's slot recommendations differ; neither narrowed leads
nor displaced source holes were introduced to conceal that discrepancy.

The manufacturer CAD ZIP was not incorporated into these reconstructed
models. It is absent from the candidate and explicitly excluded by both
delivery scripts. Archive-level exclusion belongs to the final packaging check.

## Linked current evidence

These independent checks verify the active source hashes and link the current
family reports. Their internal check counts are separate from the 746 checks
in this review.

- [Bent-pair source geometry audit: 33 checks](heatsink-fit-research/bent-pair-geometry-audit.json)
- [Independent rigid geometry / neighbor audit: 15 checks](independent-rigid-pair-audit.json)
- [Bent-pair native export](heatsink-fit-research/native-probes/native-export-audit.json)
- [Bent-pair full-scene surface screen](heatsink-fit-research/bent-pair-native-scene-screen.json)
- [Corrected rear geometry audit: 43 checks](rear-connector-quality/final-geometry-audit.json)
- [Corrected rear native audit: 124 checks](rear-connector-quality/native-quality-audit.json)
- [LED source geometry / 80-hole audit: 233 checks](led-assembly-quality/led-assembly-geometry-audit.json)
- [LED native export](led-assembly-quality/native-probes/native-export-audit.json)

Fresh ERC/DRC, final full-board exports, saved-Blender checks, render review
and archive integrity are separate validation layers. This report approves
the qualified visual update within its stated scope; it does not certify
electrical readiness, fabrication, fitted tolerance or physical assembly.
