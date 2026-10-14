# Historical NP transistor candidates

These two original models improve the 24 historical 2SC536F positions using
the recovered Sanyo No.333H NP2003A drawing. They are independent CC0 geometry,
not manufacturer CAD. Source documents and photographs retain publisher rights.
See `../transistor-research/README.md` for package selection and source hashes.

The original BOM explicitly calls these parts TO-92. No.333H names NP2003A
as TO-92, and the original near-square front photograph is consistent with it.
The actually fitted manufacturer, package revision and rear mould remain
unverified. The smaller SP2000B is a separate family and is not silently used.

The body is **5 x 4 x 5 mm typical**, with **0.45 x 0.44 mm typical full stock
leads**. These are not published maximum toleranced envelopes. The unsized rear
profile, flat-face datum, shallow front recess, rounded lead joins and colors
are explicitly illustrative. The former source body-seat and tail heights are
retained: 2.5/-2.7 mm for the normal inline form, 3.2/-2.5 mm for the asymmetric
form. Factory 14 mm lead length does not specify the installed tail length.

| Candidate | Original assignments | Original transforms |
| --- | --- | --- |
| Inline form | 20 mainboard + IO Q50 | Offset -2.54,0,0 mm; rotation 0; scale 1 |
| Asymmetric form | Mainboard Q17/Q19/Q23 | Offset 0; rotation 0; scale 1 |

Pin **1=B, 2=C, 3=E** is checked against both original imported symbol families.
Normal STEP source lead axes are X5.08/2.54/0, which the unchanged -2.54 mm
offset maps to original PCB X2.54/0/-2.54. Asymmetric source axes are
X2.54/0/-3.302 at offset0. Factory exits retain 1.3 mm spacing at the body;
qualified installed bends fan out to these existing pads. The flat face remains
negative STEP Y, corresponding to positive PCB Y. No footprint is moved.

Each conductor has a full 0.45 mm ribbon width normal to its straight bend
segments and 0.44 mm depth. Rounded unions at bends add material rather than
thinning the stock. Board-through sections are exactly 0.45 x0.44 mm at every
sampled height, centered in the original 1 mm drills. The nominal radial corner
margin is about 0.1853 mm. This is a geometric check, not tolerance qualification.

`build_transistors.py` writes only these candidates and reports 162 checks:
source pin names, all24 reference transforms and drills, factory exits, valid
connected solid geometry, absence of interlead intersections, closed meshes,
STEP reimport bounds/volume and immutable source PCB hashes. Each colored STEP
has four feature solids; their union is one connected valid solid.

`audit_transverse_stock.py` adds 20 checks against the reimported STEP files,
cutting each lead normal to all three straight centerline segments. Both the
diagonal and vertical portions retain 0.45 x 0.44 mm cross-sections and
0.198 square mm area. The rounded joins add material without thinning it.

`check_native_export.py` generates isolated original-footprint probes and imports
the frozen STEP files through the native KiCad exporter. Its 101 checks verify
the two material roles and complete canonical geometry to better than 0.001 mm.
The actual maximum envelope residual was 0.000000268 mm. The source PCB remains
unchanged. `render_native_review.py` renders the native exported facets into a
new Blender scene and never opens or saves the delivered assembly.

`transistor-quality-manifest.json` has two model families and three assignment
rows. The inline family is shared across the two boards; `references_by_board`
and `source_refs` retain that distinction. Integration, assembly clearance and
fresh complete-board verification are the parent task's next steps. These
candidates make no installed or physical-fit approval.
