#!/usr/bin/env python3
"""Read-only native KiCad GLB preview in a fresh Blender scene.
SPDX-License-Identifier: CC0-1.0
"""
from pathlib import Path
import json
import struct
import bpy
from mathutils import Vector

H=Path(__file__).resolve().parent
M=json.loads((H/'transistor-quality-manifest.json').read_text())
R=json.loads((H/'native-export-audit.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=True
s.render.resolution_x=1600;s.render.resolution_y=1050;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('Studio');s.world.use_nodes=True
s.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.65,.65,1)
s.world.node_tree.nodes['Background'].inputs[1].default_value=.65
s.view_settings.view_transform='AgX'


def mat(name,rgba,metal=False):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=rgba
    p.inputs['Metallic'].default_value=.8 if metal else 0
    p.inputs['Roughness'].default_value=.25 if metal else .38
    return m


def accessor(j,binary,index):
    a=j['accessors'][index];v=j['bufferViews'][a['bufferView']]
    fmt={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']]
    width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    size=struct.calcsize(fmt)*width;stride=v.get('byteStride',size)
    off=v.get('byteOffset',0)+a.get('byteOffset',0)
    return [struct.unpack_from('<'+fmt*width,binary,off+i*stride)for i in range(a['count'])]


for part,probe,xshift in zip(M['parts'],R['probes'],[-.008,.008]):
    data=Path(probe['glb']).read_bytes();n=struct.unpack_from('<I',data,12)[0]
    j=json.loads(data[20:20+n]);binary=data[28+n:]
    cx=2.54 if 'Inline' in part['id'] else 0
    for mesh in j['meshes']:
        for primitive in mesh['primitives']:
            xyz=accessor(j,binary,primitive['attributes']['POSITION'])
            # Explicit GLB Y-up -> canonical Z-up, retaining native tessellation.
            xyz=[(x-cx*.001+xshift,-z,y)for x,y,z in xyz]
            idx=[v[0]for v in accessor(j,binary,primitive['indices'])]
            faces=[tuple(idx[i:i+3])for i in range(0,len(idx),3)]
            bm=bpy.data.meshes.new(part['id']);bm.from_pydata(xyz,[],faces);bm.update()
            o=bpy.data.objects.new(part['id'],bm);s.collection.objects.link(o)
            rgba=j['materials'][primitive['material']]['pbrMetallicRoughness']['baseColorFactor']
            o.data.materials.append(mat(part['id'],rgba,max(rgba[:3])>.2))
            bpy.context.view_layer.objects.active=o;o.select_set(True)
            bpy.ops.object.shade_smooth_by_angle(angle=.523598776);o.select_set(False)
    bpy.ops.object.text_add(location=(xshift,-.0053,-.00275),rotation=(0,0,0))
    o=bpy.context.object;o.data.body='Inline form: 21 parts' if 'Inline' in part['id'] else 'Asymmetric form: 3 parts'
    o.data.align_x='CENTER';o.data.size=.0009
    o.data.materials.append(mat('Caption',(.025,.03,.04,1)))

bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,-.0029))
bpy.context.object.data.materials.append(mat('Neutralstage',(.55,.58,.62,1)))
target=Vector((0,0,.0022))
for pos,energy in [((-.035,-.045,.065),.18),((.04,.025,.05),.14),((0,.04,.065),.12)]:
    bpy.ops.object.light_add(type='AREA',location=pos)
    o=bpy.context.object;o.data.energy=energy;o.data.size=.045
    o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();c=bpy.context.object;c.data.type='ORTHO';c.data.ortho_scale=.039
c.data.clip_start=.001;c.data.clip_end=10;s.camera=c
c.location=target+Vector((.023,-.052,.028))
c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler()
s.render.filepath=str(H/'Sanyo-NP2003A-native-review.png')
bpy.ops.render.render(write_still=True)
print('Native candidate preview saved',flush=True)
