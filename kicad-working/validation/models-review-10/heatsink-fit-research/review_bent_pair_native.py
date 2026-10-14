"""Audit native KiCad colors/bounds and render isolated bent-pair study."""
from pathlib import Path
import bpy,json,hashlib
from mathutils import Matrix,Vector
H=Path(__file__).resolve().parent
m=json.loads((H/'bent-pair-manifest.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
glb=H/'native-probes/bent-pair.glb'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(glb))
roots={o.name.split('.')[0]:o for o in bpy.data.objects if o.name.split('.')[0] in ['IC20','KK1']}
assert set(roots)=={'IC20','KK1'}
def meshes(root):return [o for o in root.children_recursive if o.type=='MESH']
def bbox(vv):return [min(v[i] for v in vv) for i in range(3)]+[max(v[i] for v in vv) for i in range(3)]
checks=[]
for p in m['parts']:
 ref=p['references'][0];root=roots[ref];inv=root.matrix_world.inverted();vv=[(inv@o.matrix_world@v.co)*1000 for o in meshes(root) for v in o.data.vertices]
 bound=bbox(vv);error=max(abs(a-b) for a,b in zip(bound,p['geometry']['exact_bounds_mm']))
 colors=sorted({tuple(mat.diffuse_color) for o in meshes(root) for mat in o.data.materials});expected=2 if ref=='IC20' else 1
 checks.append({'reference':ref,'native_bounds_mm':bound,'STEP_bounds_mm':p['geometry']['exact_bounds_mm'],'maximum_bounds_error_mm':error,
  'colors':colors,'expected_color_count':expected,'source_hash_unchanged':sha(Path(p['step']))==p['source_sha256'],
  'passed':error<.01 and len(colors)==expected and sha(Path(p['step']))==p['source_sha256']})
delta=(roots['IC20'].matrix_world.translation-roots['KK1'].matrix_world.translation)*1000
result={'passed':all(r['passed'] for r in checks) and max(abs(a-b) for a,b in zip(delta,[0,-1.27,0]))<1e-5,'native_GLB_sha256':sha(glb),'records':checks,'native_IC20_minus_KK1_translation_mm':list(delta),'expected_translation_mm':[0,-1.27,0]}
(H/'native-probes/native-export-audit.json').write_text(json.dumps(result,indent=2)+'\n')
assert result['passed'],result
source_meshes={ref:list(meshes(root)) for ref,root in roots.items()}
scene=bpy.context.scene
# Copy only the two native model meshes into a standalone study at the shared KK1 datum.
for o in list(bpy.data.objects):
 if o.type=='MESH' and not any(o in meshes(root) for root in roots.values()):o.hide_render=True
for ref,root in roots.items():
 for o in source_meshes[ref]:
  world=roots['KK1'].matrix_world.inverted()@o.matrix_world
  o.parent=None;o.matrix_world=world
  if ref=='IC20':
   copy=o.copy();copy.data=o.data.copy();scene.collection.objects.link(copy);copy.location.x+=.022
  o.location.x-=.022
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.world=bpy.data.worlds.new('Review studio');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.25,.25,.25,1)
def material(name,color):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1);mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.38;return mat
# Small explicit source-outline patch only, stopping at source edge. Rendering datum is KK1: edge Y=-1.651 mm.
for x in [-.022,.022]:
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,-.006651,-.0008));board=bpy.context.object;board.name='Illustrative PCB edge datum';board.dimensions=(.031,.010,.0016);board.data.materials.append(material('PCB green',(.025,.20,.08)))
for loc,energy,size in [((-.025,.015,.07),.16,.05),((.05,-.02,.04),.10,.04)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,.009,.005))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(-.035,-.045,.060));camera=bpy.context.object;camera.rotation_euler=(Vector((0,.008,.004))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=.096;camera.data.clip_start=.0001;camera.data.clip_end=10;scene.camera=camera
scene.render.filepath=str(H/'bent-pair-native-review.png');bpy.ops.render.render(write_still=True)
print(json.dumps(result,indent=2))
