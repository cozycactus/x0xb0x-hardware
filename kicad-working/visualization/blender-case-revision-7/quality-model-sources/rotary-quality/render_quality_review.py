"""Standalone candidate views; delivered scenes are never opened or saved."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
rot=json.loads((HERE/'rotary-quality-manifest.json').read_text());ct=json.loads((HERE.parent/'misc-quality/misc-quality-manifest.json').read_text())['parts'][0]
models=[{'id':p['id'],'segments':p['segments']} for p in rot['parts']]+[{'id':'CT6EP_DatasheetDetailed','segments':[{'name':v['name'],'stl':v['stl'],'color_srgb':v['color_rgb']} for v in ct['segments']]}]
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def mat(name,color,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*[linear(v) for v in color],1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.31;return m
for item in models:
 bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=20;s.cycles.use_denoising=True;s.render.resolution_x=720;s.render.resolution_y=720;s.render.resolution_percentage=100;s.world=bpy.data.worlds.new('Studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.65,.65,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.45;s.view_settings.view_transform='AgX';s.view_settings.exposure=0
 objs=[]
 for seg in item['segments']:
  bpy.ops.wm.stl_import(filepath=seg['stl'],global_scale=.001);o=bpy.context.object;o.name=seg['name'];o.data.materials.clear();metal=.7 if any(q in seg['name'] for q in ['Metal','Bracket','BushingA','ExactA','Lever','Plating','Leads']) else 0;o.data.materials.append(mat(seg['name'],seg['color_srgb'],metal));objs.append(o)
 points=[o.matrix_world@Vector(c) for o in objs for c in o.bound_box];mins=Vector([min(p[k] for p in points) for k in range(3)]);maxs=Vector([max(p[k] for p in points) for k in range(3)]);center=(mins+maxs)/2;size=max(maxs-mins)
 bpy.ops.mesh.primitive_plane_add(size=2,location=(center.x,center.y,mins.z-.0002));o=bpy.context.object;o.data.materials.append(mat('Neutral stage',(.55,.57,.60)))
 for delta,energy in [((-.045,-.06,.08),.16),((.055,.02,.055),.11)]:
  bpy.ops.object.light_add(type='AREA',location=center+Vector(delta));o=bpy.context.object;o.data.energy=energy;o.data.size=.055;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add(location=center+Vector((.055,-.09,.063)));cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=size*1.35;s.camera=cam;s.render.filepath=str(HERE/(item['id']+'_review.png'));bpy.ops.render.render(write_still=True)
 print(item['id'],'rendered',flush=True)
