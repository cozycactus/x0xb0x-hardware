"""Read-only native Q22 probe audit and standalone package closeup."""
from pathlib import Path
import hashlib
import json
import math
import sys
import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE/'legacy-quality-manifest.json').read_text())
part = manifest['parts'][0]
step = Path(part['step'])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = sha(step)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
glb = HERE/'native-probes/2SC2291-Q22.glb'
bpy.ops.import_scene.gltf(filepath=str(glb))
root = next(o for o in bpy.data.objects if o.name.split('.')[0] == 'Q22')
objects = [o for o in root.children_recursive if o.type == 'MESH']
inverse = root.matrix_world.inverted()


def bounds(obj):
    m = inverse @ obj.matrix_world
    points = [(m @ v.co)*1000 for v in obj.data.vertices]
    return [min(v[i] for v in points) for i in range(3)] + [
        max(v[i] for v in points) for i in range(3)]


points = []
parents = []
polygons = []
welded = {}


def find(i):
    while parents[i] != i:
        parents[i] = parents[parents[i]]
        i = parents[i]
    return i


def union(a,b):
    parents[find(a)] = find(b)


for obj in objects:
    matrix = inverse @ obj.matrix_world
    offset = len(points)
    for vertex in obj.data.vertices:
        point = (matrix @ vertex.co)*1000
        index = len(points)
        points.append(point)
        parents.append(index)
        key = tuple(round(v,5) for v in point)
        if key in welded:
            union(index,welded[key])
        else:
            welded[key] = index
    for polygon in obj.data.polygons:
        indices = [offset+i for i in polygon.vertices]
        for index in indices[1:]:
            union(indices[0],index)
        polygons.append(indices)
components = {}
for index,point in enumerate(points):
    components.setdefault(find(index),[]).append(point)
rows = []
for index,vertices in components.items():
    box = [min(v[i] for v in vertices) for i in range(3)]+[
        max(v[i] for v in vertices) for i in range(3)]
    rows.append({'name':'Native connected component '+str(index),
                 'bounds_mm':box,'vertices':len(vertices),
                 'polygons':sum(find(p[0])==index for p in polygons)})
body = next(r for r in rows if r['bounds_mm'][5] > 8.59)
leads = sorted([r for r in rows if r is not body],
               key=lambda r:r['bounds_mm'][0])
ordered = [body]+leads
for row, source in zip(ordered, part['features']):
    row['source_feature'] = source['name']
    row['exact_STEP_bounds_mm'] = source['exact_bounds_mm']
    row['maximum_bounds_error_mm'] = max(abs(a-b) for a,b in zip(
        row['bounds_mm'],source['exact_bounds_mm']))
overall = [min(r['bounds_mm'][i] for r in rows) for i in range(3)] + [
    max(r['bounds_mm'][i] for r in rows) for i in range(3,6)]
colors = sorted({tuple(mat.diffuse_color) for obj in objects
                 for mat in obj.data.materials})
predicted = Matrix.Translation((.04,-.04,.001595)) @ Matrix.Rotation(math.pi,4,'Z')
pose_error = max(abs(predicted[i][j]-root.matrix_world[i][j])
                 for i in range(4) for j in range(4) if (i,j)!=(2,3))
audit = {'scope':'Isolated installed KiCad GLB export and fresh Blender import; '
                 'no actual project or delivered scene saved.',
         'source_step':str(step),'source_sha256':before,
         'native_GLB':str(glb),'native_GLB_sha256':sha(glb),
         'exact_STEP_optimal_bounds_mm':part['exact_bounds_mm'],
         'native_canonical_bounds_mm':overall,
         'mesh_count':len(objects),'connected_source_solid_count':len(rows),
         'component_method':'Native vertices welded at0.00001mm solely for '
                            'read-only topology grouping. Original native mesh '
                            'is unchanged. KiCad combines six source solids '
                            'into one mesh with two material groups.',
         'color_count':len(colors),
         'native_material_colors_linear':colors,
         'source_feature_records':ordered,
         'maximum_feature_bounds_error_mm':max(r['maximum_bounds_error_mm'] for r in ordered),
         'native_FCu_angle180_rotation_and_XY_pose_max_matrix_error':pose_error,
         'observed_minimal_probe_FCu_model_origin_z_mm':root.matrix_world.translation.z*1000,
         'probe_stackup_limit':'Minimal isolated probe uses KiCad default '
                               'layer stack; its measured model plane is '
                               'recorded separately above. '
                               'The real board export uses its actual stackup. '
                               'This audit removes parent pose to check source '
                               'canonical dimensions and checks angle/XY; it '
                               'does not certify real-board model seat height.',
         'source_hash_unchanged':sha(step)==before==part['source_sha256']}
audit['passed'] = (len(rows)==6 and len(colors)==2 and pose_error<1e-6
                   and audit['maximum_feature_bounds_error_mm']<.01
                   and audit['source_hash_unchanged'])
(HERE/'native-probes/native-export-audit.json').write_text(
    json.dumps(audit,indent=2)+'\n')
if '--audit-only' in sys.argv:
    print(json.dumps(audit,indent=2))
    sys.exit(0)

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x = 1400
scene.render.resolution_y = 950
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
scene.world = bpy.data.worlds.new('Package review studio')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.32,.32,.32,1)


def material(name,color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color,1)
    mat.use_nodes = True
    p = mat.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color,1)
    p.inputs['Roughness'].default_value = .35
    return mat


for index, (x,angle) in enumerate([(-.0105,0),(.0105,math.pi)]):
    group = bpy.data.objects.new('Reviewed native package '+str(index),None)
    scene.collection.objects.link(group)
    group.location = (x,0,0)
    group.rotation_euler.z = angle
    for source in objects:
        obj = source.copy()
        obj.data = source.data.copy()
        scene.collection.objects.link(obj)
        obj.parent = group
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_basis = inverse @ source.matrix_world
for obj in objects:
    obj.hide_render = True
ink = material('Caption ink',(.025,.025,.025))
for x,text in [(-.0105,'Mitsubishi 2SC2291\nMAX body / illustrated formed leads'),
               (.0105,'Opposite side / 2 x 2 mm bevel\n3 mm stand-off is an assumption')]:
    curve = bpy.data.curves.new(text,'FONT')
    curve.body = text
    curve.size = .00085
    curve.align_x = 'CENTER'
    obj = bpy.data.objects.new('Caption '+text,curve)
    scene.collection.objects.link(obj)
    obj.location = (x,-.008,-.0025)
    curve.materials.append(ink)
bpy.ops.mesh.primitive_plane_add(size=1,location=(0,0,-.0026))
bpy.context.object.data.materials.append(material('Floor',(.48,.50,.52)))
for location,energy,size in [((-.028,-.04,.055),.12,.04),
                             ((.03,.03,.045),.07,.035)]:
    bpy.ops.object.light_add(type='AREA',location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = 'DISK'
    light.data.size = size
    light.rotation_euler = (Vector((0,0,.002))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.008,-.045,.031))
camera = bpy.context.object
camera.rotation_euler = (Vector((0,0,.002))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = .043
camera.data.clip_start = .0001
camera.data.clip_end = 10
scene.camera = camera
scene.render.filepath = str(HERE/'2sc2291-native-package-review.png')
bpy.ops.render.render(write_still=True)
assert sha(step)==before
print(json.dumps({k:audit[k] for k in ['passed','mesh_count','color_count',
                  'maximum_feature_bounds_error_mm','source_hash_unchanged']},indent=2))
