#!/usr/bin/env python3
"""Read-only model preview from frozen per-feature STL assets.

Run with Blender --background --python; no project or existing scene is read.
SPDX-License-Identifier: CC0-1.0
"""
from pathlib import Path
import hashlib
import json
import math
import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'resonator-quality-manifest.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=48
scene.render.resolution_x=1800
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('NeutralStudio')
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.15,.17,.20,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.8
scene.view_settings.view_transform='AgX'


def material(name,color,metal=0):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    node=m.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value=tuple(color)+(1,)
    node.inputs['Metallic'].default_value=metal
    node.inputs['Roughness'].default_value=.32 if metal else .38
    return m


def label(text,pos,size=1):
    curve=bpy.data.curves.new(text,'FONT')
    curve.body=text
    curve.align_x='CENTER'
    curve.size=size
    obj=bpy.data.objects.new(text,curve)
    scene.collection.objects.link(obj)
    obj.location=pos
    obj.rotation_euler=(math.pi/2,0,0)
    obj.data.materials.append(material(text+'Ink',(.90,.93,.98)))
    return obj


for i,row in enumerate(manifest['parts']):
    x=-11 if i==0 else 11
    for feature in row['features']:
        path=HERE/Path(feature['stl']).name
        assert hashlib.sha256(path.read_bytes()).hexdigest()==feature['sha256']
        bpy.ops.wm.stl_import(filepath=str(path))
        obj=bpy.context.object
        obj.location.x=x
        obj.data.materials.append(material(row['id']+feature['name'],feature['color_rgb'],
                                           1 if feature['role']=='lead' else 0))
        for poly in obj.data.polygons:
            poly.use_smooth=feature['role']!='lead'
    label(f"{6 if i==0 else 16} MHz family illustration",(x,-2,-4.8),.85)
    label('Max body '+('9.5 x 4 x 6.5 mm' if i==0 else '10 x 5 x 10 mm'),
          (x,-2,-6.2),.65)
label('Drawing-supported taper and shoulders; exact profile is illustrative',
      (0,-2,-8.4),.64)
label('Original 0.6 x 0.35 mm leads, 2.54 mm pitch and mounting datum retained',
      (0,-2,-9.5),.64)
bpy.ops.object.camera_add(location=(15,-65,24))
camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO'
camera.data.ortho_scale=48
scene.camera=camera
for pos,power,size in [((-15,-22,35),18000,25),((22,-8,20),9000,18),((0,18,25),14000,20)]:
    bpy.ops.object.light_add(type='AREA',location=pos)
    light=bpy.context.object
    light.data.energy=power
    light.data.shape='DISK'
    light.data.size=size
    light.rotation_euler=(Vector((0,0,3))-light.location).to_track_quat('-Z','Y').to_euler()
scene.render.image_settings.file_format='PNG'
output=HERE/'resonator-quality-contact-sheet.png'
scene.render.filepath=str(output)
bpy.ops.render.render(write_still=True)
(HERE/'resonator-quality-render-record.json').write_text(json.dumps(dict(
    preview=str(output),sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
    models={r['id']:r['source_sha256'] for r in manifest['parts']},
    pixels=[1800,900],geometry_modified=False,illustrative_materials=True),indent=2)+'\n')
