"""Seat the rear plate on the original Eagle datum, retaining the saved assembly.

The original I/O board carries a detached Dimension-layer strip whose inner
edge lies 0.508 mm (0.020 in) outside the PCB rear edge, exactly at all three
REAN footprint origins. The finishing manual clamps the rear plate with those
three jacks. Revision 13 instead placed the plate inner face on the PCB rear
edge, so the audio shoulders ran 0.508 mm into the plate.

Only one world-space delta (0, -0.508 mm, 0) is applied, to the I/O board
placement empty, its 24 wiring-study endpoint ghosts and 5 I/O labels. The
24 illustrative conductors keep their mainboard end and blend only their last
20 mm onto the moved endpoints. No mesh, material, keyframe, plate, case,
hardware or mainboard pose changes.

Run once from the repository root:
  Blender --background kicad-working/visualization/blender-case-revision-13/\
x0xb0x-populated-with-case.blend --python-exit-code 1 \
    --python kicad-working/visualization/blender-case-revision-14/update_panel_datum.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / 'blender-case-revision-13/x0xb0x-populated-with-case.blend'
OUTPUT = HERE / 'x0xb0x-populated-with-case.blend'
sys.path.insert(0, str(HERE / 'verification'))
from scene_snapshot import sha  # noqa: E402

SHIFT_MM = 0.508
BLEND_LENGTH_MM = 20.0
IO_EMPTY = 'I/O board — rear mounting approximation'
GHOST = re.compile(r'STUDY / ioboard J\d+\.\d+ native endpoint ghost$')
LABEL = re.compile(r'STUDY / ioboard J\d+ label$')
WIRE = re.compile(r'STUDY / (J\d+)\.(\d+) → .* conductor$')

assert Path(bpy.data.filepath).resolve() == BASELINE.resolve()
assert not OUTPUT.exists(), 'Keep the frozen saved scene immutable'
baseline_sha = sha(BASELINE)
scene = bpy.context.scene
old_objects = set(bpy.data.objects)

delta = Vector((0.0, -SHIFT_MM / 1000.0, 0.0))
io_empty = bpy.data.objects[IO_EMPTY]
assert io_empty.parent is None and io_empty.instance_collection
moved = [io_empty] + [o for o in bpy.data.objects if GHOST.match(o.name) or LABEL.match(o.name)]
assert len(moved) == 1 + 24 + 5, len(moved)
for obj in moved:
    assert obj.parent is None and tuple(obj.delta_location) == (0.0, 0.0, 0.0), obj.name
    obj.delta_location = delta

wires = []
for obj in bpy.data.objects:
    if not WIRE.match(obj.name):
        continue
    assert obj.type == 'CURVE' and len(obj.data.splines) == 1
    spline = obj.data.splines[0]
    assert spline.type == 'POLY'
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

guide_name = '00 START HERE — revision 14 assembly'
guide = bpy.data.texts.new(guide_name)
guide.write('''x0xb0x enclosure assembly — Blender revision 14 / KiCad revision 12

The rear plate inner face now lies on the datum drawn in the original
Eagle I/O board: a detached Dimension strip 0.508 mm (0.020 in) behind the
PCB rear edge, where all three REAN footprint origins sit. The plate is
clamped by those three jacks, so their shoulders now seat on its inner
face instead of running 0.508 mm into it. DIN and MJ fronts, which the
original manual keeps flush with the PCB edge, sit 0.508 mm behind it.

Only the I/O board placement moved, 0.508 mm toward the case front, with
its wiring-study endpoints. All 491 fitted native component references,
PCB placement and copper, case and plate geometry, 40 PCB LEDs, 23 button
caps, hardware, shaders, cameras and four assembly views are preserved.

Frames: 1 assembled; 80 exploded; 120 control-side switch inspection;
160 illustrative wiring study. The rear camera shows the connections.

Reading the strip as the plate section is an interpretation: it is wider
than the plate. POWER and USB bodies still sit 0.081 mm below their
rectangular cutouts. See revision-14-change-record.json and verification.
This scene does not qualify physical fit or fabrication.
''')
scene['visualization_revision'] = 14
scene['opening_notes_text'] = guide_name
scene['revision_14_baseline_scene_sha256'] = baseline_sha
scene['revision_14_geometry_basis'] = ('Preserved revision13 complete assembly; I/O board placement, its '
                                       'wiring-study endpoints and conductor ends moved 0.508 mm toward '
                                       'the case front')
scene['revision_14_plate_datum'] = ('Plate inner face on original Eagle detached Dimension strip, '
                                    'KiCad I/O Y=+0.508 mm (REAN footprint origins)')
scene['revision_14_IO_board_delta_mm'] = [0.0, -SHIFT_MM, 0.0]
scene['revision_14_KiCad_revision'] = 12
scene.frame_set(1)
bpy.context.view_layer.update()
assert set(bpy.data.objects) == old_objects
assert len([o for o in bpy.data.objects if o.get('source_reference')]) == 491
assert sha(BASELINE) == baseline_sha
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True, check_existing=False)
record = dict(passed=True, visualization_revision=14, kicad_revision=12,
              baseline_sha256=baseline_sha, stable_scene_sha256=sha(OUTPUT),
              stable_scene_bytes=OUTPUT.stat().st_size,
              world_delta_mm=[0.0, -SHIFT_MM, 0.0],
              delta_meaning='I/O board moves 0.508 mm toward the case front; KiCad I/O Y=+0.508 mm '
                            'now lies on the plate inner face.',
              moved_objects=[o.name for o in moved], wire_end_blend_length_mm=BLEND_LENGTH_MM,
              wires=wires, stored_object_count=len(old_objects), native_reference_count=491,
              opening_guide=guide_name,
              opening_guide_sha256=hashlib.sha256(guide.as_string().encode()).hexdigest(),
              downloaded_CAD_geometry_incorporated=False, physical_fit_qualified=False)
(HERE / 'revision-14-change-record.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({k: v for k, v in record.items() if k not in ('wires', 'moved_objects')}, indent=2))
