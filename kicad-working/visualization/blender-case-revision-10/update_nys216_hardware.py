"""Refine only three presentation nuts, retaining every native connector mesh."""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / 'blender-case-revision-9/x0xb0x-populated-with-case.blend'
OUTPUT = HERE / 'x0xb0x-populated-with-case.blend'
SOURCE_DIR = HERE.parents[1] / 'validation/nys216-hardware-quality'
PARAMETERS = SOURCE_DIR / 'hardware-parameters.json'
sys.path.insert(0, str(HERE.parent / 'blender-case-revision-9/verification'))
from scene_snapshot import mesh_signature, props, sha

REFERENCES = ('HEADPHONE0', 'MIXIN0', 'MIXOUT0')
NAMES = [ref + ' / black PA6 nut proxy' for ref in REFERENCES]
ANGULAR_SEGMENTS = 192


def topology(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    closed = all(edge.is_manifold for edge in bm.edges)
    volume = bm.calc_volume(signed=False)
    unseen = set(bm.verts)
    components = 0
    while unseen:
        components += 1
        pending = [unseen.pop()]
        while pending:
            vertex = pending.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in unseen:
                    unseen.remove(other)
                    pending.append(other)
    bm.free()
    return dict(closed_manifold=closed, connected_components=components,
                volume_mm3=volume * 1e9)


def hex_radius(theta, apothem):
    # Existing mesh has vertical flats (+/-X) and corners at +/-Y.
    distance = (theta + math.pi / 6) % (math.pi / 3) - math.pi / 6
    return apothem / math.cos(distance)


def make_outer_mesh(name, center, profile):
    flange = profile['flange']
    wrench = profile['wrench']
    front = profile['front_treatment']
    apothem = wrench['across_flats_mm'] / 2
    corner = wrench['circumscribed_diameter_mm'] / 2
    face_radius = front['front_diameter_mm'] / 2
    # Revolve the rounded envelope, then use exact planar clipping. Sampling
    # min(hex radius, curve radius) directly leaves zigzag shading boundaries.
    # The 0.05 mm hidden overlap enables a robust flange union; it does not
    # change either exposed axial plane or the declared flange thickness.
    stations = [dict(z=wrench['z_min_mm']-.05, type='circle', radius=corner),
                dict(z=front['cap_start_z_mm'], type='circle', radius=corner)]
    for index in range(1, front['quarter_arc_segments'] + 1):
        theta = index / front['quarter_arc_segments'] * math.pi / 2
        stations.append(dict(z=front['cap_start_z_mm'] + front['axial_depth_mm'] * math.sin(theta),
            type='rounded', radius=face_radius + (corner - face_radius) * math.cos(theta)))
    vertices = []
    for station in stations:
        for index in range(ANGULAR_SEGMENTS):
            theta = index / ANGULAR_SEGMENTS * 2 * math.pi
            radius = station['radius']
            vertices.append((center.x + radius / 1000 * math.cos(theta),
                             center.y + radius / 1000 * math.sin(theta), station['z'] / 1000))
    faces = [tuple(reversed(range(ANGULAR_SEGMENTS)))]
    smooth = [False]
    for band in range(len(stations) - 1):
        for index in range(ANGULAR_SEGMENTS):
            following = (index + 1) % ANGULAR_SEGMENTS
            faces.append((band * ANGULAR_SEGMENTS + index,
                          band * ANGULAR_SEGMENTS + following,
                          (band + 1) * ANGULAR_SEGMENTS + following,
                          (band + 1) * ANGULAR_SEGMENTS + index))
            smooth.append(True)
    faces.append(tuple((len(stations) - 1) * ANGULAR_SEGMENTS + index
                       for index in range(ANGULAR_SEGMENTS)))
    smooth.append(False)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for polygon, flag in zip(mesh.polygons, smooth):
        polygon.use_smooth = flag
    return mesh, stations


def hex_prism(center, apothem_mm):
    radius = apothem_mm / math.cos(math.pi / 6) / 1000
    vertices = [(center.x + radius*math.cos(math.pi/6+i*math.pi/3),
                 center.y + radius*math.sin(math.pi/6+i*math.pi/3), z)
                for z in (-.01, .01) for i in range(6)]
    faces = [tuple(reversed(range(6))), tuple(range(6,12))]
    faces += [(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)]
    mesh = bpy.data.meshes.new('TEMP / exact SW15 planar wrench clip')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    return mesh


def boolean_mesh(obj, mesh, operation):
    temporary = bpy.data.objects.new('TEMP / NYS216 '+operation, mesh)
    bpy.context.scene.collection.objects.link(temporary)
    temporary.matrix_world = obj.matrix_world.copy()
    modifier = obj.modifiers.new('Exact '+operation+' profile boundary', 'BOOLEAN')
    modifier.operation = operation
    modifier.solver = 'EXACT'
    modifier.object = temporary
    bpy.context.view_layer.objects.active = obj
    with bpy.context.temp_override(object=obj, active_object=obj):
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(temporary, do_unlink=True)
    if not mesh.users:
        bpy.data.meshes.remove(mesh)


def refine(obj, old_bore, profile):
    old_mesh = obj.data
    original_signature = mesh_signature(old_mesh)
    original_world = obj.matrix_world.copy()
    original_collections = set(obj.users_collection)
    original_props = props(obj)
    center = Vector(old_bore['cutter_axis_local'])
    center.z = 0
    new_mesh, stations = make_outer_mesh(old_mesh.name + ' / rounded flange', center, profile)
    for material in old_mesh.materials:
        new_mesh.materials.append(material)
    for key, value in old_mesh.items():
        new_mesh[key] = value
    obj.data = new_mesh
    temporary_link = obj.name not in bpy.context.view_layer.objects
    if temporary_link:
        bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.update()
    boolean_mesh(obj, hex_prism(center, profile['wrench']['across_flats_mm']/2), 'INTERSECT')
    flange = profile['flange']
    bpy.ops.mesh.primitive_cylinder_add(vertices=ANGULAR_SEGMENTS,
        radius=flange['diameter_mm']/2000,
        depth=(flange['z_max_mm']-flange['z_min_mm'])/1000,
        location=original_world @ Vector((center.x,center.y,
            (flange['z_min_mm']+flange['z_max_mm'])/2000)))
    flange_obj = bpy.context.object
    flange_mesh = flange_obj.data.copy()
    for vertex in flange_mesh.vertices:
        vertex.co += Vector((center.x,center.y,
            (flange['z_min_mm']+flange['z_max_mm'])/2000))
    for polygon in flange_mesh.polygons:
        polygon.use_smooth = len(polygon.vertices)==4
    unused = flange_obj.data
    bpy.data.objects.remove(flange_obj, do_unlink=True)
    if not unused.users:
        bpy.data.meshes.remove(unused)
    boolean_mesh(obj, flange_mesh, 'UNION')
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=profile['bore']['diameter_mm'] / 2000,
                                      depth=.04, location=original_world @ center)
    cutter = bpy.context.object
    cutter.name = 'TEMP / NYS216 retained native-axis bore'
    modifier = obj.modifiers.new('Retained plain native-axis bore', 'BOOLEAN')
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
    assert obj.matrix_world == original_world and set(obj.users_collection) == original_collections
    assert props(obj) == original_props
    assert list(obj.data.materials) == list(old_mesh.materials)
    geometry = topology(obj.data)
    assert geometry['closed_manifold'] and geometry['connected_components'] == 1 and geometry['volume_mm3'] > 0, geometry
    bounds = [min(v.co[i] for v in obj.data.vertices) for i in range(3)] + [
        max(v.co[i] for v in obj.data.vertices) for i in range(3)]
    expected = [center.x-.00875, center.y-.00875, -.0025,
                center.x+.00875, center.y+.00875, .0025]
    assert max(abs(a-b) for a, b in zip(bounds, expected)) < 1e-8, (bounds, expected)
    # Printed SW15 remains at the six mid-body flat stations.
    mid_body = [v.co for v in obj.data.vertices if abs(v.co.z - .00195) < 1e-8]
    assert len(mid_body) >= 6
    assert abs(max(v.x for v in mid_body) - center.x - .0075) < 1e-8
    assert abs(min(v.x for v in mid_body) - center.x + .0075) < 1e-8
    return dict(object=obj.name, source_reference=obj.name.split(' / ', 1)[0],
                old_mesh_signature=original_signature,
                saved_mesh_signature=mesh_signature(obj.data),
                original_object_matrix=[list(row) for row in original_world],
                original_collections=sorted(c.name for c in original_collections),
                profile_center_local_m=list(center),
                exterior_mesh_center_shift_mm=[x*1000 for x in center],
                original_object_origin_and_pose_preserved=True,
                bore_diameter_mm=profile['bore']['diameter_mm'],
                profile_stations_mm=stations, angular_segments=ANGULAR_SEGMENTS,
                topology_method='Exact six-plane Boolean intersection of revolved quarter-ellipse, union with circular flange, retained plain bore; flat faces remain flat, curved faces smooth',
                topology=geometry, bounds_local_m=bounds,
                physical_fit_qualified=False)


assert not OUTPUT.exists(), 'Refusing to overwrite an existing saved scene'
parameters_sha = sha(PARAMETERS)
parameters = json.loads(PARAMETERS.read_text())
profile = parameters['build_profile']
assert parameters['object_names'] == NAMES
assert profile['front_treatment']['curve_profile'] == 'quarter-ellipse'
baseline_sha = sha(BASELINE)
baseline_record = json.loads((BASELINE.parent / 'revision-9-change-record.json').read_text())
old_bores = {row['object']: row for row in baseline_record['hardware_changes']}
bpy.ops.wm.open_mainfile(filepath=str(BASELINE))
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
object_names = set(bpy.data.objects.keys())
material_names = set(bpy.data.materials.keys())
changes = [refine(bpy.data.objects[name], old_bores[name], profile) for name in NAMES]
assert set(bpy.data.objects.keys()) == object_names
assert set(bpy.data.materials.keys()) == material_names
assert sum(bool(o.get('source_reference')) for o in bpy.data.objects) == 491
assert sha(PARAMETERS) == parameters_sha, 'Source parameter contract changed during build'
guide_name = '00 START HERE — revision 10 assembly'
guide = (HERE / 'README.md').read_text()
assert guide_name not in bpy.data.texts
bpy.data.texts.new(guide_name).write(guide)
scene = bpy.context.scene
scene['visualization_revision'] = 10
scene['opening_notes_text'] = guide_name
scene['revision_10_baseline_scene_sha256'] = baseline_sha
scene['revision_10_geometry_basis'] = (
    'Preserved revision9 complete assembly; only three exterior NYS216 mounting '
    'nut meshes refined to SW15 flats,17.5mm circular flange and illustrative '
    'rounded front. Mesh profiles aligned with retained native-axis9.6mm bores; '
    'all native KiCad revision11 models and all other objects are unchanged.')
scene['revision_10_refined_nut_count'] = len(changes)
scene.frame_set(1)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
assert sha(BASELINE) == baseline_sha
record = dict(visualization_revision=10, kicad_revision=11,
    preserved_baseline_scene='blender-case-revision-9/' + BASELINE.name,
    preserved_baseline_sha256=baseline_sha, saved_scene=OUTPUT.name,
    saved_scene_sha256=sha(OUTPUT), saved_scene_bytes=OUTPUT.stat().st_size,
    refined_nut_count=len(changes), refined_objects=NAMES, hardware_changes=changes,
    source_parameters='../../validation/nys216-hardware-quality/hardware-parameters.json',
    source_parameters_sha256=parameters_sha,
    source_evidence_sha256=sha(SOURCE_DIR / 'source-evidence.json'),
    current_opening_notes_text=guide_name,
    current_opening_notes_sha256=hashlib.sha256(guide.encode()).hexdigest(),
    native_geometry_changed=False, kicad_files_changed=False,
    washers_changed=False, physical_fit_qualified=False)
(HERE / 'revision-10-change-record.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({key: value for key, value in record.items() if key != 'hardware_changes'}, indent=2))
