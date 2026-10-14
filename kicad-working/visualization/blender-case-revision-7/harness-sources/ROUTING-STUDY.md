# Qualified harness routing study

`../add_harness_routing_study.py` is a reusable Blender builder. Load the intended
revision 5 base scene, run this script, review the generated audit, and save only
from the owning scene build workflow. The script does not save any `.blend` file.
It refuses duplicate insertion and checks all 48 supplied native tips against the
currently loaded board instances before creating curves.

The display contains 24 separate insulation curves connecting J3–J7 at the same
numbered pins on both boards. In particular, J3.1 connects to J3.1 and J3.2 to J3.2;
USB signal names do not imply a physical pin swap. The independently verified
electrical source map is `verified-harness-map.json`.

The original instructions specify four three-conductor pieces and two
six-conductor pieces. Allocating those six-conductor pieces to J3 pins 1–6 and
7–12 is a reconstruction inference. Each group's low-number edge is dark in the
study. Midspan wire separation follows a transported 2.54 mm fanout row for clear
visual separation, an explicitly assumed display choice. The source establishes
actual 2.54 mm pad pitch; no particular manufactured ribbon web or stock pitch is
asserted by this display.

Every curve overlaps the original flat insulation tip by 0.05 mm, has a closed
cap, and departs along the native termination axis. The original native stubs
retain their full geometry, including the previously assumed 7.5 mm tip height.
The audit includes 48 native-tip checks and another 48 independent curve-end
position, overlap, cap and outward-tangent checks.

Frame 160 is explicitly titled **Wiring routing study — length/fit unverified**.
It uses the original assembled board poses. The mainboard body, top panel,
front control proxies, upper enclosure and standoffs are hidden for inspection;
the exact original mainboard outline and native endpoint axes appear as cyan
references. The I/O board and enclosure bottom remain visible. A dedicated camera
and readable review annotations identify the limits in the image itself. The
curves are hidden in the assembled, exploded and control inspection views. Their
visibility at frames 1, 80, 120, 159, 160 and 161 is checked independently.

This is a routing study. Original six-inch stock is 152.4 mm. Even the straight
J3 tip chord plus the two retained assumed stubs is about 154.44 mm, before bends.
The builder retains this conflict, measures every centerline and reports a stock
comparison. It does not trim or shrink the source stubs, move boards, or label
any path as a verified physical cable cut length.

`../harness-routing-study-audit.json` records the current build's measured paths,
source input hashes, source mesh hashes, unchanged existing inspection poses,
the 96 endpoint checks, source-surface candidate intersections and all 276
wire-pair spacing screens. Obstacle screening includes assembled native board
and component meshes, the enclosure, rear panel and standoffs. The original
J3–J7 stubs are excluded from obstacle screening because their tip overlap is
intentional. Screening uses centerline samples, insulation radius and surface
ray crossings; it is not a volumetric clearance or flexible cable qualification.
Any reported intersections remain unresolved. Different detailed component
models require rerunning the builder and screening before the final scene save.

The helper `render_study_preview.py` renders the study in memory and also does not
save the `.blend` file. For the final renderer, add the job
`('wiring-study', 160, bpy.data.objects['Camera / wiring routing study'])` after
unbinding timeline cameras in memory, as in the existing scene renderer.

The builder checks that all original raw mesh geometry, frames 1/80/120 poses and
visibility, and the saved base file's SHA-256 remain unchanged. It adds only
display geometry, annotations and the new inspection view to the loaded scene.
