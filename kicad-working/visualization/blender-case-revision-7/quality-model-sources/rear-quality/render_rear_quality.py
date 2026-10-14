"""Standalone candidate inspection; never opens/saves delivered assembly scenes."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;m=json.loads((HERE/'rear-quality-manifest.json').read_text());bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=24;s.cycles.use_denoising=True;s.render.resolution_x=1600;s.render.resolution_y=850;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.view_settings.exposure=0;s.world=bpy.data.worlds.new('Review studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.3,.3,.3,1)
def material(name,rgba,metal=0,rough=.36):
 mat=bpy.data.materials.new(name);mat.diffuse_color=rgba;mat.use_nodes=True;p=mat.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=rgba;p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return mat
ink=material('Review ink',(.025,.025,.025,1));floor_mat=material('Review floor',(.42,.44,.46,1))
for i,part in enumerate(m['parts']):
 for j,angle in enumerate([0,math.pi]):
  pos=(-.06+i*.084+j*.035,0)
  for seg in part['mesh_parts']:
   bpy.ops.wm.stl_import(filepath=seg['stl'],global_scale=.001);o=bpy.context.object;o.name=part['id']+'/'+str(j)+'/'+seg['name'];o.rotation_euler.z=angle;o.location=(*pos,0);o.data.materials.clear();o.data.materials.append(material(o.name,seg['rgba'],.65 if seg['role']in ['contact','bronze']else 0))
  cu=bpy.data.curves.new(part['id']+' caption','FONT');cu.body=('SDS-50J'if i==0 else'NYS216')+('\nfront / mating side'if j==0 else'\nrear / contact windows');cu.align_x='CENTER';cu.size=.0022;o=bpy.data.objects.new(cu.name,cu);s.collection.objects.link(o);o.location=(pos[0],-.028,.00001);cu.materials.append(ink)
bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,-.0004));bpy.context.object.data.materials.append(floor_mat)
for loc,energy,size in [((-.06,-.08,.13),.24,.1),((.09,.07,.1),.12,.08)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,.005,.005))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.025,-.19,.16));o=bpy.context.object;o.rotation_euler=(Vector((0,0,.004))-o.location).to_track_quat('-Z','Y').to_euler();o.data.type='ORTHO';o.data.ortho_scale=.175;s.camera=o;s.render.filepath=str(HERE/'rear-quality-contact-sheet.png');bpy.ops.render.render(write_still=True)
