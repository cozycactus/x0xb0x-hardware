"""Add40 native spacer meshes; retain every existing object and optical shader."""
import hashlib,json,sys
from pathlib import Path
import bpy
H=Path(__file__).resolve().parent;W=H.parents[1];V=H/'verification';sys.path.insert(0,str(V))
from scene_snapshot import sha,material_signature,matrix,mesh_signature
base=H.parent/'blender-case-revision-21/x0xb0x-populated-with-case.blend';out=H/'x0xb0x-populated-with-case.blend'
assert Path(bpy.data.filepath).resolve()==base.resolve() and not out.exists()
review=W/'validation/models-review-19';export=json.loads((review/'native-export-record.json').read_text())['boards']['mainboard'];source=review/export['glb'];assert sha(source)==export['glb_sha256']
row=next(a for a in json.loads((review/'combined-model-plan.json').read_text())['assignments'] if a['footprint']=='LED5MM')
s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();old_objects=set(bpy.data.objects);old_materials={m.name:material_signature(m) for m in bpy.data.materials};old_sets={n:set(getattr(bpy.data,n)) for n in ['collections','meshes','materials','images','cameras','lights','actions']}
old_names=set(o.name for o in old_objects);bpy.ops.import_scene.gltf(filepath=str(source));bpy.context.view_layer.update();imported=set(bpy.data.objects)-old_objects
added=[];parts=[];black=None
for ref in row['references']:
 root=bpy.data.objects['MAINBOARD/'+ref];incoming=next(o for o in imported if o.name==ref or o.name.startswith(ref+'.'))
 meshes=[o for o in incoming.children_recursive if o.type=='MESH']
 candidates=[o for o in meshes if max(v.co.z for v in o.data.vertices)<.0061 and len(o.data.vertices)>24]
 assert len(candidates)==1,(ref,[(o.name,len(o.data.vertices)) for o in meshes])
 part=candidates[0];assert len(part.data.materials)==1
 if black is None:
  black=part.data.materials[0].copy();black.name='VCC STD240B black thermoplastic — revision19'
  shader=black.node_tree.nodes['Principled BSDF'];shader.inputs['Roughness'].default_value=.42
  black['source_basis']='VCC STDxxxBLK_A rev001: VALOX310SEO black, UL94V0; roughness illustrative'
 mesh=part.data.copy();mesh.materials.clear();mesh.materials.append(black);o=bpy.data.objects.new('MAINBOARD/'+ref+'/STD240B spacer',mesh)
 root.users_collection[0].objects.link(o);o.parent=root;o.matrix_local=root.matrix_world.inverted()@part.matrix_world
 o['source_geometry']='Exact native KiCad19 spacer mesh';o['drawing']='VCC STDxxxBLK_A rev001';o['physical_fit_qualified']=False
 bpy.context.view_layer.update()
 assert max(abs(a-b) for x,y in zip(o.matrix_world,part.matrix_world) for a,b in zip(x,y))<1e-7
 added.append(o.name);parts.append(dict(reference=ref,object=o.name,mesh=mesh_signature(mesh),matrix_local=matrix(o.matrix_local)))
 root['model_classification']=row['classification'];root['model_limitations']=' | '.join(row['limitations']);root['detailed_model_revision']=19;root['selected_native_source_glb_sha256']=sha(source);root['source_geometry_basis']='Existing LED body and full leads preserved exactly; drawing-derived STD240B spacer added at unchanged6.096mm seat'
for o in imported:bpy.data.objects.remove(o,do_unlink=True)
for n in old_sets:
 block=getattr(bpy.data,n)
 for x in set(block)-old_sets[n]:
  if x.users==0:block.remove(x)
assert set(o.name for o in bpy.data.objects)==old_names|set(added)
assert all(material_signature(bpy.data.materials[n])==v for n,v in old_materials.items())
assert set(m.name for m in bpy.data.materials)-set(old_materials)=={black.name}
guide=bpy.data.texts.new('00 START HERE — revision22 assembly');guide.write('''x0xb0x Blender22 / KiCad19\n40 black VCC STD240B spacer meshes added from STDxxxBLK_A rev001.\nDetailed section A-A includes the0.010-inch end lands in lengthXXX.\nThe0.240-inch total is6.096mm; original LED height and optics remain.\nAll existing objects, materials, poses, cameras and animation are retained.\nCentral third-lead bore diameter/end-land outer radii are illustrative;\ncompliant retention tabs omitted. Historical0.22-versus0.24-inch BOM conflict\nand all existing physical-fit limitations remain.\nFrames1 assembled,80 exploded,120 control-side,160 wiring study.\n''')
s['visualization_revision']=22;s['opening_notes_text']=guide.name;s['revision_22_baseline_scene_sha256']=sha(base);s['revision_22_KiCad_revision']=19;s['revision_22_added_spacer_count']=40
s.frame_set(1);bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True,check_existing=False)
record=dict(passed=True,visualization_revision=22,kicad_revision=19,baseline_sha256=sha(base),stable_scene_sha256=sha(out),stable_scene_bytes=out.stat().st_size,source_glb_sha256=sha(source),source_plan_sha256=sha(review/'combined-model-plan.json'),added_objects=added,added_materials=[black.name],material_signature=material_signature(black),native_parts=parts,changed_source_roots=['MAINBOARD/'+r for r in row['references']],native_reference_count=491,stored_object_count=len(bpy.data.objects),opening_guide=guide.name,opening_guide_sha256=hashlib.sha256(guide.as_string().encode()).hexdigest(),physical_fit_qualified=False)
(H/'revision-22-change-record.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'passed':True,'added_spacers':len(added),'scene_sha256':sha(out)},indent=2),flush=True)
