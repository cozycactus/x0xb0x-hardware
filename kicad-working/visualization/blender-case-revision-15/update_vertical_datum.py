"""Seat the I/O board on the original rear-DXF height datum, retaining the assembly.

Every cutout in the original rear-panel DXF is measured from a component
mounting plane 0.250 in (6.350 mm) above the plate's lower edge: both
rectangular POWER/USB cutouts start exactly there, the three audio holes sit
8.001 mm above it (NYS216 axis 8.0 mm) and the four DIN holes 9.982 mm above
it (SDS-50J axis 10.0 mm). Revision 14 placed the mounting plane 6.269 mm
above the plate edge, leaving the POWER/USB bodies 0.081 mm below their
cutouts.

One world-space delta (0, 0, +dz) is applied, with dz measured so the plane
lands on 6.350 mm: to the I/O board placement empty, its 24 wiring-study
endpoint ghosts and 5 labels, and to the three audio nut proxies, which
thread onto the jack bushings (expressed in their instanced collection
space). The 24 conductors blend only their last 20 mm onto the moved
endpoints. Washers stay centred on the plate holes. No mesh, material,
keyframe, plate, case or mainboard pose changes.

Run once from the repository root:
  Blender --background kicad-working/visualization/blender-case-revision-14/\
x0xb0x-populated-with-case.blend --python-exit-code 1 \
    --python kicad-working/visualization/blender-case-revision-15/update_vertical_datum.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / 'blender-case-revision-14/x0xb0x-populated-with-case.blend'
OUTPUT = HERE / 'x0xb0x-populated-with-case.blend'
sys.path.insert(0, str(HERE / 'verification'))
from scene_snapshot import sha  # noqa: E402

TARGET_PLANE_MM = 6.35        # 0.250 in above the plate lower edge (original DXF)
BLEND_LENGTH_MM = 20.0
IO_EMPTY = 'I/O board — rear mounting approximation'
PLATE = 'Rear panel — original DXF'
REAR_FACES = 'Rear faces — presentation proxies'
NUTS = [f'{r} / black PA6 nut proxy' for r in ('HEADPHONE0', 'MIXIN0', 'MIXOUT0')]
GHOST = re.compile(r'STUDY / ioboard J\d+\.\d+ native endpoint ghost$')
LABEL = re.compile(r'STUDY / ioboard J\d+ label$')
WIRE = re.compile(r'STUDY / (J\d+)\.(\d+) → .* conductor$')


def mounting_plane_mm():
    """Component mounting plane height in the plate frame (Y up from lower edge)."""
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    inv = bpy.data.objects[PLATE].matrix_world.inverted()
    heights = [(inv @ inst.matrix_world.translation).y * 1000
               for inst in bpy.context.evaluated_depsgraph_get().object_instances
               if inst.object.original.name in ('IOBOARD/HEADPHONE0/mesh', 'IOBOARD/CV0/mesh',
                                                'IOBOARD/DIN1/mesh', 'IOBOARD/USB0/mesh')]
    assert len(heights) == 4 and max(heights) - min(heights) < 1e-6, heights
    return sum(heights) / 4


assert Path(bpy.data.filepath).resolve() == BASELINE.resolve()
assert not OUTPUT.exists(), 'Keep the frozen saved scene immutable'
baseline_sha = sha(BASELINE)
scene = bpy.context.scene
old_objects = set(bpy.data.objects)
plate_up = bpy.data.objects[PLATE].matrix_world.to_3x3() @ Vector((0, 1, 0))
assert (plate_up - Vector((0, 0, 1))).length < 1e-6, plate_up  # float32 rotation
plane_before = mounting_plane_mm()
dz_mm = TARGET_PLANE_MM - plane_before
assert 0.080 < dz_mm < 0.082, dz_mm
delta = Vector((0.0, 0.0, dz_mm / 1000.0))

io_empty = bpy.data.objects[IO_EMPTY]
moved = [io_empty] + [o for o in bpy.data.objects if GHOST.match(o.name) or LABEL.match(o.name)]
assert len(moved) == 30
for obj in moved:
    assert obj.parent is None, obj.name
    obj.delta_location = obj.delta_location + delta
rear_faces = bpy.data.objects[REAR_FACES]
nut_delta = rear_faces.matrix_world.to_3x3().inverted() @ delta
for name in NUTS:
    nut = bpy.data.objects[name]
    assert nut.parent is None and nut.users_collection[0] == rear_faces.instance_collection, name
    nut.delta_location = nut.delta_location + nut_delta

wires = []
for obj in bpy.data.objects:
    if not WIRE.match(obj.name):
        continue
    spline = obj.data.splines[0]
    assert obj.type == 'CURVE' and len(obj.data.splines) == 1 and spline.type == 'POLY'
    world = obj.matrix_world
    local_delta = world.inverted().to_3x3() @ delta
    points = [world @ p.co.xyz for p in spline.points]
    # Each conductor runs mainboard -> I/O; its last point is the I/O end.
    remaining = [0.0] * len(points)
    for i in range(len(points) - 2, -1, -1):
        remaining[i] = remaining[i + 1] + (points[i + 1] - points[i]).length
    shifted = 0
    for point, distance in zip(spline.points, remaining):
        t = max(0.0, 1.0 - distance * 1000.0 / BLEND_LENGTH_MM)
        weight = t * t * (3.0 - 2.0 * t)
        if weight <= 0.0:
            continue
        co = point.co.copy()
        co.xyz = co.xyz + local_delta * weight
        point.co = co
        shifted += 1
    wires.append(dict(name=obj.name, points=len(points), shifted_points=shifted))
assert len(wires) == 24
plane_after = mounting_plane_mm()

guide_name = '00 START HERE — revision 15 assembly'
guide = bpy.data.texts.new(guide_name)
guide.write('''x0xb0x enclosure assembly — Blender revision 15 / KiCad revision 12

The I/O board now sits on the height datum of the original rear-panel
DXF: a component mounting plane 0.250 in (6.350 mm) above the plate's
lower edge. Both rectangular POWER/USB cutouts start there, and the audio
and DIN holes sit their part axis heights above it (within 0.001 and
0.018 mm). The POWER/USB bodies rest on their cutout edges instead of
0.081 mm below them, and the audio jacks are centred in their holes.

Only the I/O board placement moved, 0.081 mm upward, with its wiring-study
endpoints and the three audio nuts that thread onto the jacks. Revision
14's axial plate datum, all 491 fitted native component references, PCB
placement and copper, case and plate geometry, 40 PCB LEDs, 23 button
caps, washers, shaders, cameras and four assembly views are preserved.

Frames: 1 assembled; 80 exploded; 120 control-side switch inspection;
160 illustrative wiring study. The rear camera shows the connections.

The original CV/GATE holes imply a 5.334 mm jack axis, while the current
MJ-3536N drawing gives 5.5 mm, so their modelled bushings clear the holes
by only 0.005 mm. See revision-15-change-record.json and verification.
This scene does not qualify physical fit or fabrication.
''')
scene['visualization_revision'] = 15
scene['opening_notes_text'] = guide_name
scene['revision_15_baseline_scene_sha256'] = baseline_sha
scene['revision_15_geometry_basis'] = ('Preserved revision14 complete assembly; I/O board placement, its '
                                       'wiring-study endpoints, conductor ends and the three audio nuts '
                                       'raised onto the original rear-DXF 0.250 in datum')
scene['revision_15_height_datum'] = ('Component mounting plane 6.350 mm (0.250 in) above the rear plate '
                                     'lower edge, as used by every original rear DXF cutout')
scene['revision_15_IO_board_delta_mm'] = [0.0, 0.0, dz_mm]
scene['revision_15_KiCad_revision'] = 12
scene.frame_set(1)
bpy.context.view_layer.update()
assert set(bpy.data.objects) == old_objects
assert len([o for o in bpy.data.objects if o.get('source_reference')]) == 491
assert sha(BASELINE) == baseline_sha
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True, check_existing=False)
record = dict(passed=True, visualization_revision=15, kicad_revision=12,
              baseline_sha256=baseline_sha, stable_scene_sha256=sha(OUTPUT),
              stable_scene_bytes=OUTPUT.stat().st_size,
              mounting_plane_before_mm=plane_before, mounting_plane_after_mm=plane_after,
              target_plane_mm=TARGET_PLANE_MM, world_delta_mm=[0.0, 0.0, dz_mm],
              delta_meaning='I/O board raised so its component mounting plane lies 6.350 mm (0.250 in) '
                            'above the rear plate lower edge.',
              moved_objects=[o.name for o in moved], moved_hardware=NUTS, hardware_instancer=REAR_FACES,
              hardware_collection_delta_mm=[x * 1000 for x in nut_delta],
              wire_end_blend_length_mm=BLEND_LENGTH_MM, wires=wires,
              stored_object_count=len(old_objects), native_reference_count=491,
              opening_guide=guide_name,
              opening_guide_sha256=hashlib.sha256(guide.as_string().encode()).hexdigest(),
              downloaded_CAD_geometry_incorporated=False, physical_fit_qualified=False)
(HERE / 'revision-15-change-record.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({k: v for k, v in record.items() if k not in ('wires', 'moved_objects')}, indent=2))
