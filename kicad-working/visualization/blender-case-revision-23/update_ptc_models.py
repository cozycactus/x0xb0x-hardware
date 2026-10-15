"""Replace only the14 existing PTC part meshes with native KiCad20 geometry."""
import hashlib,json,sys
from pathlib import Path
import bpy
H=Path(__file__).resolve().parent;W=H.parents[1];sys.path.insert(0,str(H/'verification'))
from scene_snapshot import sha,material_signature,mesh_signature,matrix
base=H.parent/'blender-case-revision-22/x0xb0x-populated-with-case.blend';out=H/'x0xb0x-populated-with-case.blend';review=W/'validation/models-review-20'
assert Path(bpy.data.filepath).resolve()==base.resolve() and not out.exists()
export=json.loads((review/'native-export-record.json').read_text())['boards']['mainboard'];source=review/export['glb'];assert sha(source)==export['glb_sha256']
row=next(a for a in json.loads((review/'combined-model-plan.json').read_text())['assignments'] if a['references']==['R100A0','R100B0'])
s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();objects=set(bpy.data.objects);old_materials={m.name:material_signature(m) for m in bpy.data.materials};old_sets={n:set(getattr(bpy.data,n)) for n in ['collections','meshes','materials','images','cameras','lights','actions']};baseline_hash=sha(base)
def colour(m):return tuple(m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)
def gap(a,b):return max(abs(v-w) for x,y in zip(a,b) for v,w in zip(x,y))
bpy.ops.import_scene.gltf(filepath=str(source));bpy.context.view_layer.update();imported=set(bpy.data.objects)-objects;changes={}
for ref in row['references']:
 root=bpy.data.objects['MAINBOARD/'+ref];incoming=next(o for o in imported if o.name==ref or o.name.startswith(ref+'.'));assert gap(root.matrix_world,incoming.matrix_world)<1e-7
 parts=[o for o in incoming.children_recursive if o.type=='MESH'];assert len(parts)==7
 def bounds(o):
  m=root.matrix_world.inverted()@o.matrix_world;pts=[m@v.co for v in o.data.vertices]
  return [min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]
 terms=[o for o in parts if bounds(o)[0][2]<0];assert len(terms)==1
 other=[o for o in parts if o not in terms];body=max(other,key=lambda o:bounds(o)[1][0]-bounds(o)[0][0]);bands=sorted([o for o in other if o!=body],key=lambda o:sum([bounds(o)[0][0],bounds(o)[1][0]]));assert len(bands)==5
 oldparts=[bpy.data.objects['MAINBOARD/'+ref+'/mesh'+('' if i==0 else '.'+str(i).zfill(3))] for i in range(7)]
 for target,part in zip(oldparts,bands+[body]+terms):
  assert len(target.data.materials)==len(part.data.materials)==1
  assert max(abs(a-b) for a,b in zip(colour(target.data.materials[0]),colour(part.data.materials[0])))<1e-6,(target.name,part.name)
  old_signature=mesh_signature(target.data);local=target.matrix_world.inverted()@part.matrix_world
  normals=[(local.to_3x3().inverted().transposed()@n.vector).normalized() for n in part.data.corner_normals]
  mesh=part.data.copy();mesh.name=target.name+'/revision20 native';mesh.transform(local);mesh.materials.clear();mesh.materials.append(target.data.materials[0]);mesh.normals_split_custom_set(normals)
  previous=target.data;target.data=mesh
  if previous.users==0:bpy.data.meshes.remove(previous)
  changes[target.name]=dict(old_mesh=old_signature,new_mesh=mesh_signature(mesh),native_part=part.name,canonical_transform=matrix(local))
 root['model_classification']=row['classification'];root['model_limitations']=' | '.join(row['limitations']);root['detailed_model_revision']=20;root['selected_native_source_glb_sha256']=sha(source);root['source_geometry_basis']='Native KiCad20 PTC model: original manufacturer3.7x1.9mm body and0.45mm leads; original PCB axes and placement retained'
for o in imported:bpy.data.objects.remove(o,do_unlink=True)
for n in old_sets:
 block=getattr(bpy.data,n)
 for item in set(block)-old_sets[n]:
  if item.users==0:block.remove(item)
assert set(bpy.data.objects)==objects
assert {m.name:material_signature(m) for m in bpy.data.materials}==old_materials
assert len(changes)==14
guide=bpy.data.texts.new('00 START HERE — revision23 assembly');guide.write('''x0xb0x Blender23 / KiCad20\nR100A0/R100B0 now use the original Micro-Ohm LPTC12 family dimensions:\nbody3.7mm long,1.9mm diameter, leads0.45mm diameter. The previous\n7.62x2.54mm bodies came from the footprint outline. Original10.16mm\nPCB pitch, footprints and model transforms remain unchanged.\nThe0.4mm body standoff, end taper, bands,0.75mm lead bends and trimmed\ntails are installation/presentation illustrations. No thermal contact,\nTCR/color-code, fitted tolerance or physical assembly claim is made.\nOnly14 existing PTC meshes and two roots' source fields change; all\nexisting objects, materials, LEDs/spacers, caps, case and poses remain.\nFrames1 assembled,80 exploded,120 control-side,160 wiring study.\n''')
s['visualization_revision']=23;s['opening_notes_text']=guide.name;s['revision_23_baseline_scene_sha256']=baseline_hash;s['revision_23_KiCad_revision']=20;s['revision_23_corrected_reference_count']=2
s.frame_set(1);bpy.context.view_layer.update();assert sha(base)==baseline_hash;bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True,check_existing=False)
record=dict(passed=True,visualization_revision=23,kicad_revision=20,baseline_sha256=baseline_hash,stable_scene_sha256=sha(out),stable_scene_bytes=out.stat().st_size,source_glb_sha256=sha(source),source_plan_sha256=sha(review/'combined-model-plan.json'),changes=changes,changed_source_roots=['MAINBOARD/'+r for r in row['references']],added_objects=[],added_materials=[],native_reference_count=491,stored_object_count=len(objects),opening_guide=guide.name,opening_guide_sha256=hashlib.sha256(guide.as_string().encode()).hexdigest(),physical_fit_qualified=False)
(H/'revision-23-change-record.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(passed=True,changed_meshes=len(changes),scene_sha256=sha(out)),indent=2),flush=True)
