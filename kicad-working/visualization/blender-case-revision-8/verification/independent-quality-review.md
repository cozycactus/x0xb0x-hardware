# Independent revision-11 model and integration review

**PASS: 4,041 checks; zero failures.** This review independently reads the
historical source images, STEP geometry, all original/candidate PCB data and
both complete native KiCad exports. It imports no model-generator code and
makes no project changes.

The historical Sanyo No.333H drawing distinguishes SP2000B from NP2003A and
labels NP as TO-92. The original unscaled project photo has a near-square
front and is consistent with the NP choice; it does not authenticate the
fitted vendor or rear mold. The handbook's printed page 40 explicitly makes
unspecified dimensions **typical**. Consequently the NP body **5 x 4 x 5 mm**,
lead stock **0.45 x 0.44 mm** and factory pitch **1.3 mm** are typical dimensions,
not maximum clearance envelopes. F is the 160-320 gain rank and does not
identify a package.

Fresh STEP reimports have four valid material-role solids and one connected
union. All lead sections at Z = -2, -1, -0.1 and 0 mm retain the full
0.45 x 0.44 mm stock at the original axes. Sections normal to each formed
strip also retain at least 0.198 mm2 of stock area. None of the leads were
narrowed. The independent original-symbol review confirms pad 1/B, pad 2/C
and pad 3/E; the source bottom-view orientation and STEP Y = -PCB Y convention
retain the flat face and B at positive X / E at negative X mapping.
All 24 transistor references retain their exact board pad axes, original
offsets/rotations/scales, stand-offs and trimmed-tail bounds. Normal assets
remain centered at X = 2.54 mm with offset -2.54 mm; asymmetric assets remain
centered at X = 0.

The combined candidate retains all 491 fitted references and changes 26 model
assignments. Every non-model AST in 75 PCB/footprint files is unchanged;
original schematic, symbol and project-setting files are byte-identical.
Earlier models and provenance are retained. There are 11 planned existing
file changes and seven new project files. Root's separately executed
4,943-check candidate audit is hash-linked.

Both complete native KiCad GLB exports are tied to the reviewed candidate
hashes. All 26 updated reference roots and both material-role bounds are
present; native reference translations and rotations retain the actual
footprint and model transforms. The maximum measured updated-role bound
residual is 0.000000268 mm.

The full 0.6 x 0.35 mm Abracon leads and primary maximum resonator envelopes
are linked to the separate 60 + 68 check resonator review. This reviewer
created those resonator candidates, so their modeling provenance is
distinguished from the independent transistor inspection and candidate
integration review.

The source body curve, front recess, lead bends, coating/plating colors,
exact manufacturer identity, body seating, lead length after trimming,
source tolerances, solder joints and physical installed fit remain
qualified. This is a visual-model and integration-preservation review;
it does not approve physical assembly or fabrication. Native ERC/DRC outcomes
are reported separately by root's fresh project checks.

The JSON contains every check, exact input/candidate hashes, normal-strip
section measurements and native-role bound residuals. The source drawings
and images retain publisher rights; original model reconstruction code and
geometry use CC0-1.0, without manufacturer CAD incorporation.
