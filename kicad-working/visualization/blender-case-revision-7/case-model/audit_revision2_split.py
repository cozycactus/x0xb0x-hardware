"""Independent read-only split-union and visible-board sampling audit."""
import bpy,json,hashlib,collections
from pathlib import Path
from mathutils import Vector
base=Path(__file__).resolve().parent.parent
scene=bpy.context.scene;scene.frame_set(1)
loaded=Path(bpy.data.filepath)
report={'blend':str(loaded),'sha256':hashlib.sha256(loaded.read_bytes()).hexdigest(),
        'frame':1,'errors':[],'split_objects':[]}
checks=[]
def check(ok,name):
 checks.append({'check':name,'passed':bool(ok)})
 if not ok:report['errors'].append(name)
io=bpy.data.objects['I/O board — rear mounting approximation']
display=io.instance_collection
reference=bpy.data.collections['REFERENCE / Historical detached Dimension outline']
refinst=bpy.data.objects['Historical detached Dimension outline — hidden reference']
check(display.name.startswith('DISPLAY / I/O populated PCB'),'I/O instance uses populated display collection')
check(refinst.hide_render and refinst.hide_viewport,'Historical reference instance hidden in viewport and render')
check(refinst.parent==io,'Historical reference retains I/O-parent transform')
check(all(abs(refinst.matrix_basis[r][c]-(1 if r==c else 0))<1e-12 for r in range(4) for c in range(4)),'Historical reference local matrix is identity')
rows=json.loads((base/'source-review/io-detached-contour-native-meshes.json').read_text())['objects']
lookup={29:'IOBOARD/PCB layers/mesh.003',31:'IOBOARD/PCB layers/mesh.005',32:'IOBOARD/PCB layers/mesh.006',33:'IOBOARD/PCB layers/mesh.007'}
totalv=totalf=0
for row in rows:
 if not row['detached_polygon_indices']:continue
 index=int(row['object_name'].rsplit(':',1)[1].rstrip(']'))
 name=lookup[index];original=bpy.data.objects[name]
 parts=[o for coll in [display,reference] for o in coll.objects if o.get('original_native_mesh')==name]
 allv=[];allf=[];exact=True;materials=True;matrix=True
 for o in parts:
  va=o.data.attributes['original_vertex_index'];fa=o.data.attributes['original_polygon_index']
  vi=[d.value for d in va.data];fi=[d.value for d in fa.data]
  allv.extend(vi);allf.extend(fi)
  for new,old in enumerate(vi):
   if tuple(o.data.vertices[new].co)!=tuple(original.data.vertices[old].co):exact=False
  for new,old in enumerate(fi):
   if tuple(vi[v] for v in o.data.polygons[new].vertices)!=tuple(original.data.polygons[old].vertices):exact=False
   if o.data.polygons[new].material_index!=original.data.polygons[old].material_index or o.data.polygons[new].use_smooth!=original.data.polygons[old].use_smooth:materials=False
  if any(o.matrix_world[r][c]!=original.matrix_world[r][c] for r in range(4) for c in range(4)):matrix=False
  if o in reference.objects[:]:totalv+=len(o.data.vertices);totalf+=len(o.data.polygons)
 vertexunion=collections.Counter(allv)==collections.Counter(range(len(original.data.vertices)))
 faceunion=collections.Counter(allf)==collections.Counter(range(len(original.data.polygons)))
 selparts=[o for o in reference.objects if o.get('original_native_mesh')==name]
 selected=[d.value for o in selparts for d in o.data.attributes['original_polygon_index'].data]
 selectedexact=sorted(selected)==sorted(row['detached_polygon_indices'])
 record={'original':name,'original_vertices':len(original.data.vertices),'original_polygons':len(original.data.polygons),'subset_count':len(parts),'exact_vertex_union':vertexunion,'exact_polygon_union':faceunion,'coordinates_and_topology_equal':exact,'materials_and_smoothing_preserved':materials,'native_world_matrices_equal':matrix,'reference_indices_match_independent_source_selection':selectedexact}
 report['split_objects'].append(record)
 check(all([vertexunion,faceunion,exact,materials,matrix,selectedexact]),'Exact split union for '+name)
report['reference_vertices']=totalv;report['reference_polygons']=totalf
check(totalv==130 and totalf==92,'Reference consists of exactly130vertices and92polygons')
check(all(o not in display.objects[:] for o in reference.objects),'Historical reference meshes excluded from display collection')

# Sample only the two board instances visible in assembled frame1. Originals
# retained for provenance and the hidden reference are deliberately excluded.
samples=[]
for key,name in [('mainboard','Mainboard — B.Cu outward in assembled view'),('ioboard','I/O board — rear mounting approximation')]:
 inst=bpy.data.objects[name]
 for o in inst.instance_collection.objects:
  if o.type!='MESH':continue
  ref=o.parent.get('source_reference') if o.parent else None
  ref=ref or o.get('source_reference') or 'PCB'
  mat=inst.matrix_world@o.matrix_world
  budget=1500 if ref=='PCB' else 100
  step=max(1,len(o.data.vertices)//budget)
  verts=[list((mat@o.data.vertices[i].co)*1000) for i in range(0,len(o.data.vertices),step)]
  corners=[list((mat@Vector(v))*1000) for v in o.bound_box]
  samples.append({'board':key,'reference':ref,'object':o.name,'samples':verts,'bounds':[[min(v[j] for v in corners) for j in range(3)],[max(v[j] for v in corners) for j in range(3)]]})
(base/'case-model/scene-clearance-samples.json').write_text(json.dumps({'blend':str(loaded),'sha256':report['sha256'],'rows':samples}))
report['sampled_vertices']=sum(len(r['samples']) for r in samples)
report['sampled_board_meshes']=len(samples)
io_matrix=[list(row) for row in io.matrix_world]
base_input=json.loads((base/'revision-input.json').read_text());original_file=base.parent.parent.parent/Path(base_input['base_blend'])
# Resolve the pinned relative path from repository root, independent of CWD.
original_file=Path('/Users/ruslanmigirov/Downloads/hardware')/base_input['base_blend']
check(hashlib.sha256(original_file.read_bytes()).hexdigest()==base_input['base_sha256'],'First delivered Blender file hash still equals revision input')
bpy.ops.wm.open_mainfile(filepath=str(original_file));bpy.context.scene.frame_set(1)
old=bpy.data.objects['I/O board — rear mounting approximation']
unchanged=all(abs(io_matrix[r][c]-old.matrix_world[r][c])<1e-12 for r in range(4) for c in range(4))
check(unchanged,'I/O instance world matrix exactly unchanged from first delivered blend')
report['IO_world_matrix_unchanged']=unchanged
report['checks']=checks;report['passed']=not report['errors']
report['scope']='Saved revision2 reopened read-only. Exact preserved coordinate/topology union of split source meshes; visibility and I/O transform verified. Samples include visible native board instances only; hidden references and verification originals excluded. No source or scene saved.'
(base/'case-model/revision-2-independent-split-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
