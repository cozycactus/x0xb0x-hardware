"""Standalone visual inspection sheet; never opens or edits delivered scenes."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
base=Path(__file__).resolve().parent
m=json.loads((base/'rear-body-illustrations-manifest.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32
scene.cycles.device='CPU';scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=700;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-1
scene.world=bpy.data.worlds.new('Review studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.3,.3,.3,1)
positions={'sds50j':(-.06,0),'mj3536n':(-.028,0),'pj202ah':(.002,0),'nys216':(.035,0),'usb-typeb':(.069,0)}
labels={'sds50j':'SDS-50J\n20 × 15.8 × 21.1 mm','mj3536n':'MJ-3536N\n10 × 15.8 × 10 mm','pj202ah':'PJ-202AH\n9 × 14.4 × 11 mm','nys216':'NYS216\n20 × 33 × 16.5 mm','usb-typeb':'USB Type B\n12.04 × 16 × 10.62 mm'}
for part in m['parts']:
 family=next(k for k in positions if part['id'].startswith(k))
 bpy.ops.wm.stl_import(filepath=part['path'],global_scale=.001)
 o=bpy.context.object;o.name=part['id']
 x,y=positions[family];o.location=(x,y,0)
 if family=='pj202ah':o.rotation_euler.z=math.pi
 material=bpy.data.materials.new(part['id']);material.diffuse_color=part['color_srgb'];material.use_nodes=True
 p=material.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=part['color_srgb'];p.inputs['Roughness'].default_value=.38
 if part['role'] in ['bushing','center pin','metal shell']:p.inputs['Metallic'].default_value=.8
 o.data.materials.clear();o.data.materials.append(material)
 for poly in o.data.polygons:poly.use_smooth=False
ink=bpy.data.materials.new('Review ink');ink.diffuse_color=(.025,.025,.025,1);ink.use_nodes=True;ink.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.025,.025,.025,1)
for family,(x,y) in positions.items():
 curve=bpy.data.curves.new(family,'FONT');curve.body=labels[family];curve.size=.0023;curve.align_x='CENTER';curve.space_line=1.1
 o=bpy.data.objects.new(family+' caption',curve);scene.collection.objects.link(o);o.location=(x,-.021,.00001);curve.materials.append(ink)
bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,-.0004));floor=bpy.context.object
mat=bpy.data.materials.new('Review floor');mat.diffuse_color=(.42,.44,.46,1);mat.use_nodes=True;mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.42,.44,.46,1);floor.data.materials.append(mat)
for loc,energy,size in [((-.05,-.08,.12),20,.1),((.08,.06,.1),10,.08)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,.005,.005))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.025,-.19,.145));camera=bpy.context.object;camera.rotation_euler=(Vector((.006,.005,.005))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=.18;scene.camera=camera
scene.render.filepath=str(base/'rear-body-review.png');bpy.ops.render.render(write_still=True)
