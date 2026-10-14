"""Blender visual review of isolated body assets; does not touch delivered scene."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE / 'control-body-manifest.json').read_text())
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640
scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.world.color = (0.3, 0.3, 0.3)
scene.view_settings.view_transform = 'Standard'
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False

bpy.ops.object.camera_add(location=(48, -70, 50))
camera = bpy.context.object
camera.rotation_euler = (Vector((0, 0, 13)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 42
scene.camera = camera

for name, position, power, size in [
    ('Key', (15, -40, 65), 180000, 45),
    ('Fill', (-30, 15, 35), 110000, 35),
    ('Rim', (35, 35, 45), 100000, 30)]:
    bpy.ops.object.light_add(type='AREA', location=position)
    light = bpy.context.object
    light.name = name
    light.data.energy = power
    light.data.shape = 'DISK'
    light.data.size = size
    light.rotation_euler = (Vector((0, 0, 10)) - light.location).to_track_quat('-Z', 'Y').to_euler()

bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.1))
plane = bpy.context.object
floor = bpy.data.materials.new('ReviewFloor')
floor.diffuse_color = (0.72, 0.74, 0.76, 1)
plane.data.materials.append(floor)

for part in manifest['parts']:
    imported = []
    for segment in part['mesh_parts']:
        bpy.ops.wm.stl_import(filepath=segment['stl'])
        obj = bpy.context.object
        obj.name = segment['name']
        material = bpy.data.materials.get(segment['material'])
        if material is None:
            props = part['material_color_suggestions'][segment['material']]
            material = bpy.data.materials.new(segment['material'])
            material.diffuse_color = props['rgba']
            material.use_nodes = True
            bsdf = material.node_tree.nodes.get('Principled BSDF')
            bsdf.inputs['Base Color'].default_value = props['rgba']
            bsdf.inputs['Metallic'].default_value = props['metallic']
            bsdf.inputs['Roughness'].default_value = props['roughness']
        obj.data.materials.append(material)
        imported.append(obj)
    scene.render.filepath = str(HERE / (part['id'] + '_review.png'))
    bpy.ops.render.render(write_still=True)
    for obj in imported:
        bpy.data.objects.remove(obj, do_unlink=True)
