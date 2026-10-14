"""Standalone manufacturer CAD inspection, no saved assembly scene edits."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;m=json.loads((HERE/'control-quality-manifest.json').read_text());bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=24;s.cycles.use_denoising=True;s.render.resolution_x=1400;s.render.resolution_y=900;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.world=bpy.data.worlds.new('Review studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.3,.3,.3,1)
def mat(name,rgba,metal=0):
 a=bpy.data.materials.new(name);a.diffuse_color=rgba;a.use_nodes=True;p=a.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=rgba;p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.32;return a
for i,part in enumerate(m['parts']):
 x=-.014+i*.028
 for seg in part['mesh_parts']:
  bpy.ops.wm.stl_import(filepath=seg['stl'],global_scale=.001);o=bpy.context.object;o.name=part['id']+'/'+seg['role'];o.location.x=x;o.data.materials.clear();o.data.materials.append(mat(o.name,seg['rgba'],.75 if seg['role']in ['cover','terminals']else 0))
 curve=bpy.data.curves.new(part['variant']+' caption','FONT');curve.body='TL1100F publisher CAD\n'+('full nominal / free state'if i==0 else'body above seat Z=0');curve.size=.00145;curve.align_x='CENTER';o=bpy.data.objects.new(curve.name,curve);s.collection.objects.link(o);o.location=(x,-.014,-.0037);curve.materials.append(mat(o.name,(.025,.025,.025,1)))
bpy.ops.mesh.primitive_plane_add(size=1,location=(0,0,-.0038));bpy.context.object.data.materials.append(mat('Floor',(.42,.44,.46,1)))
for loc,energy,size in [((-.04,-.06,.09),.14,.065),((.05,.05,.08),.08,.06)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,.002))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.018,-.075,.06));o=bpy.context.object;o.rotation_euler=(Vector((0,0,.001))-o.location).to_track_quat('-Z','Y').to_euler();o.data.type='ORTHO';o.data.ortho_scale=.075;o.data.clip_start=.0001;o.data.clip_end=10;s.camera=o;s.render.filepath=str(HERE/'tl1100-manufacturer-cad-review.png');bpy.ops.render.render(write_still=True)
