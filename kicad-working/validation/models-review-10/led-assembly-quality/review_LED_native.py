"""Native source-frame audit and installed generic LED/panel sectional preview."""
from pathlib import Path
import bpy,json,hashlib
from mathutils import Vector
H=Path(__file__).resolve().parent;m=json.loads((H/'led-assembly-manifest.json').read_text());p=m['parts'][0]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
glb=H/'native-probes/LED-installed.glb';bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(glb))
root=next(o for o in bpy.data.objects if o.name=='LEDprobe');meshes=[o for o in root.children_recursive if o.type=='MESH'];inv=root.matrix_world.inverted()
vv=[(inv@o.matrix_world@v.co)*1000 for o in meshes for v in o.data.vertices];bounds=[min(v[i] for v in vv) for i in range(3)]+[max(v[i] for v in vv) for i in range(3)]
error=max(abs(a-b) for a,b in zip(bounds,p['geometry']['exact_bounds_mm']));colors=sorted({tuple(mat.diffuse_color) for o in meshes for mat in o.data.materials})
r={'passed':error<.001 and len(colors)==2 and sha(Path(p['step']))==p['source_sha256'],'native_source_bounds_mm':bounds,'STEP_source_bounds_mm':p['geometry']['exact_bounds_mm'],'maximum_bounds_error_mm':error,
 'native_color_count':len(colors),'native_colors':colors,'mesh_objects':[o.name for o in meshes],'native_GLB_sha256':sha(glb),'source_STEP_sha256':sha(Path(p['step'])),
 'native_root_world_matrix':[list(v) for v in root.matrix_world],'probe_native_transform':'Original B.Cu source placement with offset[1.27,0,0], rotation[0,0,180], unity scale.'}
(H/'native-probes/native-export-audit.json').write_text(json.dumps(r,indent=2)+'\n');assert r['passed'],r
scene=bpy.context.scene
for o in list(bpy.data.objects):
 if o.type=='MESH' and o not in meshes:o.hide_render=True
for o in meshes:
 world=inv@o.matrix_world;o.parent=None;o.matrix_world=world
 for mat in o.data.materials:
  mat.use_nodes=True;shader=mat.node_tree.nodes.get('Principled BSDF')
  if 'ClearLens' in o.name:
   shader.inputs['Base Color'].default_value=(.85,.93,.96,1);shader.inputs['Transmission Weight'].default_value=.82;shader.inputs['IOR'].default_value=1.5;shader.inputs['Roughness'].default_value=.10
  else:shader.inputs['Metallic'].default_value=.85;shader.inputs['Roughness'].default_value=.25
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=64;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=1500;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.world=bpy.data.worlds.new('Review world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.26,.26,.26,1)
def mat(name,color,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;s=m.node_tree.nodes['Principled BSDF'];s.inputs['Base Color'].default_value=(*color,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=.28;return m
def patch(name,z,thickness,w,d,hole_r,color):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(.00127,0,(z+thickness/2)*.001));o=bpy.context.object;o.name=name;o.dimensions=(w*.001,d*.001,thickness*.001);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(color)
 for x in ([0,2.54] if name.startswith('PCB') else [1.27]):
  bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=hole_r*.001,depth=(thickness+2)*.001,location=(x*.001,0,(z+thickness/2)*.001));c=bpy.context.object
  mod=o.modifiers.new('Source hole','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=c;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(c,do_unlink=True)
 return o
# A narrow illustrative native seat patch, not a fabricated PCB/panel artifact.
patch('PCB nominal source-seat patch',-1.6,1.6,10,7,.5,mat('PCB',(.02,.22,.09)))
patch('Front panel original hole and current seat patch',11.82125,1.5748,11,6,2.54,mat('Panel',(.56,.59,.62),.5))
for loc,energy,size in [((-.02,-.022,.045),.13,.04),((.025,.018,.025),.10,.03)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((.00127,0,.007))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.023,-.035,.025));cam=bpy.context.object;cam.rotation_euler=(Vector((.00127,0,.006))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.023;cam.data.clip_start=.0001;cam.data.clip_end=10;scene.camera=cam
scene.render.filepath=str(H/'LED-native-panel-mount-review.png');bpy.ops.render.render(write_still=True);print(json.dumps(r,indent=2))
