"""Isolated native GLB bounds/palette audit and closeup; no scene saving."""
from pathlib import Path
import hashlib
import json
import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE/'heatsink-quality-manifest.json').read_text())
part = manifest['parts'][0]
step = Path(part['step'])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = sha(step)
glb = HERE/'native-probes/heatsink-with-regulator.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=str(glb))
roots = {o.name.split('.')[0]: o for o in bpy.data.objects
         if o.name.split('.')[0] in ['KK1', 'IC20']}
assert set(roots) == {'KK1', 'IC20'}


def meshes(root):
    return [o for o in root.children_recursive if o.type == 'MESH']


def canonical_bounds(root):
    inv = root.matrix_world.inverted()
    positions = [(inv @ mesh.matrix_world @ v.co) * 1000
                 for mesh in meshes(root) for v in mesh.data.vertices]
    return [min(v[i] for v in positions) for i in range(3)] + [
        max(v[i] for v in positions) for i in range(3)]


bounds = canonical_bounds(roots['KK1'])
error = max(abs(a-b) for a, b in zip(bounds, part['geometry']['exact_bounds_mm']))
native_delta = (roots['IC20'].matrix_world.translation
                - roots['KK1'].matrix_world.translation) * 1000
colors = sorted({tuple(material.diffuse_color)
                 for obj in meshes(roots['KK1']) for material in obj.data.materials})
audit = {
    'scope': 'Fresh isolated native KiCad export and Blender GLB import. '
             'Actual PCB and delivered scenes were not opened for editing.',
    'source_step': str(step), 'source_sha256': before,
    'native_GLB': str(glb), 'native_GLB_sha256': sha(glb),
    'exact_STEP_bounds_mm': part['geometry']['exact_bounds_mm'],
    'native_canonical_mesh_bounds_mm': bounds,
    'maximum_bounds_error_mm': error,
    'native_KK1_mesh_count': len(meshes(roots['KK1'])),
    'native_KK1_vertex_count': sum(len(m.data.vertices) for m in meshes(roots['KK1'])),
    'native_KK1_color_count': len(colors), 'native_material_colors': colors,
    'all_KK1_primitives_have_materials': all(o.data.materials for o in meshes(roots['KK1'])),
    'native_IC20_relative_translation_mm': list(native_delta),
    'expected_IC20_relative_translation_mm': [0, -1.27, 0],
    'source_hash_unchanged': before == sha(step) == part['source_sha256'],
}
audit['passed'] = (error < .01 and len(colors) == 1
                   and audit['all_KK1_primitives_have_materials']
                   and max(abs(a-b) for a,b in zip(native_delta, [0,-1.27,0])) < .00001
                   and audit['source_hash_unchanged'])
(HERE/'native-probes/native-export-audit.json').write_text(
    json.dumps(audit, indent=2)+'\n')

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x = 1800
scene.render.resolution_y = 1050
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
scene.world = bpy.data.worlds.new('Review studio')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.32,.32,.32,1)


def material(name, color, metal=0, alpha=1):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, alpha)
    mat.use_nodes = True
    shader = mat.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (*color, alpha)
    shader.inputs['Metallic'].default_value = metal
    shader.inputs['Roughness'].default_value = .32
    shader.inputs['Alpha'].default_value = alpha
    return mat


def standalone_copy(source, name, translation):
    group = bpy.data.objects.new(name, None)
    scene.collection.objects.link(group)
    group.location = translation
    inv = source.matrix_world.inverted()
    for old in meshes(source):
        obj = old.copy()
        obj.data = old.data.copy()
        scene.collection.objects.link(obj)
        obj.parent = group
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_basis = inv @ old.matrix_world
    return group


# All displayed models are copies of the verified native import. Their
# translations only arrange this standalone comparison image.
left = standalone_copy(roots['KK1'], 'Detailed source drawing candidate', (-.033,0,0))
middle = standalone_copy(roots['KK1'], 'Original pose heatsink', (0,0,0))
reg_mid = standalone_copy(roots['IC20'], 'Original pose regulator', (0,-.00127,0))
right = standalone_copy(roots['KK1'], 'Interference transparent heatsink', (.033,0,0))
reg_right = standalone_copy(roots['IC20'], 'Interference transparent regulator', (.033,-.00127,0))
glass_heat = material('Illustration x-ray heatsink', (.16,.20,.23), alpha=.22)
glass_reg = material('Illustration x-ray regulator', (.65,.68,.72), alpha=.28)
for group, mat in [(right, glass_heat), (reg_right, glass_reg)]:
    for obj in group.children:
        obj.data.materials.clear()
        obj.data.materials.append(mat)
red = material('Exact BRep intersection witness', (.8,.025,.012))
bpy.ops.wm.stl_import(filepath=str(HERE/'nominal-regulator-intersection.stl'),
                      global_scale=.001)
witness = bpy.context.object
witness.name = '48.642693 mm3 nominal intersection witness'
witness.location = (.033,0,0)
witness.data.materials.append(red)
for root in roots.values():
    for obj in meshes(root):
        obj.hide_render = True

caption_mat = material('Caption ink', (.025,.025,.025))
for x, text in [
    (-.033, '574502B00000G\ncontinuous folded candidate'),
    (0, 'Unchanged native pose\nnominal IC20 illustration'),
    (.033, 'Nominal intersection: 48.64 mm3\ninstallation / spring fit unqualified'),
]:
    curve = bpy.data.curves.new(text, 'FONT')
    curve.body = text
    curve.size = .00135
    curve.align_x = 'CENTER'
    obj = bpy.data.objects.new('Caption '+text, curve)
    scene.collection.objects.link(obj)
    obj.location = (x,-.014,.0001)
    curve.materials.append(caption_mat)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0,0,-.0002))
bpy.context.object.data.materials.append(material('Floor', (.48,.50,.52)))
for location, energy, size in [((-.045,-.05,.08),.18,.06),
                                ((.04,.04,.08),.12,.05)]:
    bpy.ops.object.light_add(type='AREA', location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = 'DISK'
    light.data.size = size
    light.rotation_euler = (Vector((0,0,.01))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.017,-.085,.061))
camera = bpy.context.object
camera.rotation_euler = (Vector((0,0,.008))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = .105
camera.data.clip_start = .0001
camera.data.clip_end = 10
scene.camera = camera
scene.render.filepath = str(HERE/'heatsink-native-contact-review.png')
bpy.ops.render.render(write_still=True)
assert before == sha(step)
print(json.dumps(audit, indent=2))
