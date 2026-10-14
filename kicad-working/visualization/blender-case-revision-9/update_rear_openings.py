"""Open rear presentation hardware, retaining all native KiCad geometry.

Run using Blender --background --python; baseline revision8 remains untouched.
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / 'blender-case-revision-8/x0xb0x-populated-with-case.blend'
OUTPUT = HERE / 'x0xb0x-populated-with-case.blend'
sys.path.insert(0, str(HERE / 'verification'))
from scene_snapshot import capture, sha, write_snapshot

REMOVED = [ref + ' / jack recess proxy' for ref in
           ('CV0', 'GATE0', 'HEADPHONE0', 'MIXIN0', 'MIXOUT0')]
HARDWARE = [ref + suffix for ref in ('HEADPHONE0', 'MIXIN0', 'MIXOUT0')
            for suffix in (' / black ABS washer proxy', ' / black PA6 nut proxy')]


def bounds(data):
    return [min(v.co[i] for v in data.vertices) for i in range(3)] + [
        max(v.co[i] for v in data.vertices) for i in range(3)]


def bore_hardware(obj, displayed, native):
    """Cut only inner geometry; keep six hardware objects and outer boundaries.

    The 9.6 mm nut bore is an illustrative nominal clearance for the installed
    drawing's 3/8-32 UNEF (9.525 mm) nose, not a manufacturer hardware size.
    The 11.3 mm washer bore is retained from the existing manufacturer-based
    hardware dimension manifest.
    Existing hardware axes sit 0.082 mm above the native socket axis, so place
    the cutter on the native axis without moving the exterior illustration.
    """
    matrix = Matrix(displayed)
    bore_diameter_mm = 11.3 if 'washer' in obj.name else 9.6
    native_matrix = Matrix(native)
    axis_world = native_matrix @ Vector((0, -8.5e-3, 8e-3))
    axis_local = matrix.inverted() @ axis_world
    axis_local.z = 0
    old_data = obj.data
    old_bounds = bounds(old_data)
    old_vertices = [list(v.co) for v in old_data.vertices]
    old_world = obj.matrix_world.copy()
    old_collections = set(obj.users_collection)
    # The retained rear source collection is instanced. Link temporarily for
    # Blender's native Boolean operator, then restore the original linkage.
    temporary_link = obj.name not in bpy.context.view_layer.objects
    if temporary_link:
        bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.update()
    bpy.ops.mesh.primitive_cylinder_add(vertices=128,
        radius=bore_diameter_mm / 2000, depth=.04,
        location=old_world @ axis_local)
    cutter = bpy.context.object
    cutter.name = 'TEMP / rear native-axis hardware bore'
    modifier = obj.modifiers.new('Native socket nose clearance', 'BOOLEAN')
    modifier.operation = 'DIFFERENCE'
    modifier.solver = 'EXACT'
    modifier.object = cutter
    bpy.context.view_layer.objects.active = obj
    with bpy.context.temp_override(object=obj, active_object=obj):
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    cutter_mesh = cutter.data
    bpy.data.objects.remove(cutter, do_unlink=True)
    if not cutter_mesh.users:
        bpy.data.meshes.remove(cutter_mesh)
    if temporary_link:
        bpy.context.scene.collection.objects.unlink(obj)
    bpy.context.view_layer.update()
    assert obj.matrix_world == old_world
    assert set(obj.users_collection) == old_collections
    new_bounds = bounds(obj.data)
    assert max(abs(a-b) for a, b in zip(old_bounds, new_bounds)) < 1e-8
    for vertex in old_vertices:
        assert any(max(abs(a-b) for a, b in zip(vertex, v.co)) < 1e-8
                   for v in obj.data.vertices), (obj.name, vertex)
    return dict(object=obj.name, bore_diameter_mm=bore_diameter_mm,
        native_thread_major_diameter_mm=9.525,
        native_thread_source='https://www.rean-connectors.com/media/12224/download/nys-216-1.dxf?v=1',
        retained_hardware_dimensions_source='https://www.rean-connectors.com/media/9014/download/nys-216.pdf?v=1',
        retained_hardware_dimensions_manifest='../blender-case-revision-7/bom-parts/scene-part-dimensions.json',
        mixed_drawing_revisions_and_thread_interchangeability_unqualified=True,
        bore_basis=('11.3 mm manufacturer washer bore retained from original dimension manifest' if 'washer' in obj.name else
                    'Illustrative 9.6 mm clearance for installed 2007 NYS216 3/8-32 UNEF nose; not a manufacturer nut bore'),
        cutter_axis_local=list(axis_local),
        outer_bounds_before=old_bounds, outer_bounds_after=new_bounds,
        original_outer_vertices=old_vertices,
        original_outer_vertices_retained=True, stored_pose_preserved=True)

assert not OUTPUT.exists(), 'Refusing to overwrite an existing saved scene'
baseline_sha = sha(BASELINE)
bpy.ops.wm.open_mainfile(filepath=str(BASELINE))
before = capture()
hardware_changes = []
for name in HARDWARE:
    reference = name.split(' / ', 1)[0]
    hardware_changes.append(bore_hardware(bpy.data.objects[name],
        before['frames']['1']['displayed'][name][0],
        before['frames']['1']['displayed']['IOBOARD/' + reference + '/mesh'][0]))
for name in REMOVED:
    obj = bpy.data.objects.get(name)
    assert obj is not None and obj.type == 'MESH', name
    assert not obj.get('source_reference') and obj.parent is None, name
    assert len(obj.users_collection) == 1 and obj.users_collection[0].name == (
        'SOURCE / Rear connector faces — presentation proxies, not ECAD models'), name
    bpy.data.objects.remove(obj, do_unlink=True)

guide_name = '00 START HERE — revision 9 assembly'
guide = (HERE / 'README.md').read_text()
assert guide_name not in bpy.data.texts
bpy.data.texts.new(guide_name).write(guide)
scene = bpy.context.scene
scene['visualization_revision'] = 9
scene['opening_notes_text'] = guide_name
scene['revision_9_baseline_scene_sha256'] = baseline_sha
scene['revision_9_geometry_basis'] = (
    'Preserved revision8 complete assembly; exactly five obsolete rear jack '
    'recess disks removed and six existing audio nut/washer illustrations bored '
    'on the native socket axes. All 491 native KiCad revision11 component '
    'assemblies and all other scene geometry are unchanged.')
scene['revision_9_removed_rear_proxy_count'] = len(REMOVED)
scene['revision_9_bored_rear_hardware_count'] = len(HARDWARE)
scene.frame_set(1)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
assert sha(BASELINE) == baseline_sha
after = capture()
write_snapshot(HERE / 'verification/before-scene.json.gz', before)
write_snapshot(HERE / 'verification/after-scene.json.gz', after)
record = dict(
    visualization_revision=9, kicad_revision=11,
    preserved_baseline_scene=str(BASELINE.relative_to(HERE.parent)),
    preserved_baseline_sha256=baseline_sha,
    saved_scene=OUTPUT.name, saved_scene_sha256=sha(OUTPUT),
    saved_scene_bytes=OUTPUT.stat().st_size,
    removed_objects=REMOVED, removed_object_count=len(REMOVED),
    bored_hardware_count=len(HARDWARE), hardware_changes=hardware_changes,
    rationale='Solid presentation disks obscure the already-open native rear connector models',
    native_geometry_changed=False, kicad_files_changed=False,
    current_opening_notes_text=guide_name,
    current_opening_notes_sha256=hashlib.sha256(guide.encode()).hexdigest(),
    physical_fit_qualified=False)
for row in hardware_changes:
    row['saved_mesh_signature'] = after['objects'][row['object']]['data']
(HERE / 'revision-9-change-record.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
