"""Read only native saved scene surface screen of two isolated replacements."""
from pathlib import Path
import bpy,json,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
H=Path(__file__).resolve().parent;W=H.parents[2]
scene_path=W/'visualization/blender-case-revision-6/x0xb0x-populated-with-case.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(scene_path)
bpy.ops.wm.open_mainfile(filepath=str(scene_path));bpy.context.scene.frame_set(1)
io=bpy.data.objects['I/O board — rear mounting approximation']
manifest=json.loads((H/'bent-pair-manifest.json').read_text())
def bounds(vs):return [min(v[i] for v in vs) for i in range(3)]+[max(v[i] for v in vs) for i in range(3)]
def ref(obj):
 while obj:
  if obj.get('source_reference'):return obj.get('source_board'),obj['source_reference']
  obj=obj.parent
 return None
candidates=[]
for p in manifest['parts']:
 name=p['references'][0];root=next(o for o in io.instance_collection.objects if o.get('source_reference')==name)
 pose=io.matrix_world@root.matrix_world
 stl=Path(p['stl']);bpy.ops.wm.stl_import(filepath=str(stl),global_scale=.001)
 temp=bpy.context.object
 vv=[pose@(v.co*.001) for v in temp.data.vertices];tt=[tuple(poly.vertices) for poly in temp.data.polygons]
 candidates.append((name,p,pose,vv,tt,BVHTree.FromPolygons(vv,tt,all_triangles=True,epsilon=1e-9)))
 bpy.data.objects.remove(temp,do_unlink=True)
allowed={'Mainboard — B.Cu outward in assembled view','I/O board — rear mounting approximation','Case / bottom','Case / upper','Rear panel — original DXF','Top panel — original DXF','Spacers — original length, approximate seats'}
rows=[];scanned=0
for inst in bpy.context.evaluated_depsgraph_get().object_instances:
 o=inst.object
 if o.type!='MESH' or not inst.is_instance:continue
 parent=inst.parent.original.name if inst.parent else ''
 if parent not in allowed:continue
 r=ref(o.original)
 if r in [('ioboard','KK1'),('ioboard','IC20')]:continue
 scanned+=1;bb=bounds([inst.matrix_world@Vector(v) for v in o.bound_box])
 relevant=[]
 for name,p,pose,vv,tt,bvh in candidates:
  cb=bounds(vv);aabb=all(cb[i]<=bb[i+3] and bb[i]<=cb[i+3] for i in range(3))
  if aabb or parent.startswith('Case /'):relevant.append((name,p,pose,vv,tt,bvh,aabb))
 if not relevant:continue
 me=o.to_mesh();me.calc_loop_triangles();ov=[inst.matrix_world@v.co for v in me.vertices];ot=[tuple(t.vertices) for t in me.loop_triangles]
 obstacle=BVHTree.FromPolygons(ov,ot,all_triangles=True,epsilon=1e-9)
 for name,p,pose,vv,tt,bvh,aabb in relevant:
  pairs=bvh.overlap(obstacle);distance=min(obstacle.find_nearest(v)[3] for v in vv)
  rows.append({'candidate':name,'parent':parent,'object':o.original.name,'reference':list(r) if r else None,'AABB_overlaps':aabb,
   'possible_triangle_overlap_pairs':len(pairs),'minimum_candidate_vertex_to_surface_mm':distance*1000,'obstacle_world_bounds_mm':[v*1000 for v in bounds(ov)]})
 o.to_mesh_clear()
positives=[r for r in rows if r['possible_triangle_overlap_pairs']]
result={'passed_no_new_neighbor_or_case_surface_pairs':not positives,'saved_scene':str(scene_path),'saved_scene_sha256':before,'scene_hash_unchanged':before==sha(scene_path),
 'scanned_original_mesh_instances':scanned,'screened_candidate_obstacle_pairs':len(rows),'records':rows,'possible_surface_intersections':positives,
 'candidates':[{'reference':name,'STEP_sha256':p['source_sha256'],'STL_sha256':sha(Path(p['stl'])),'world_matrix_metres':[list(row) for row in pose],
 'world_bounds_mm':[v*1000 for v in bounds(vv)]} for name,p,pose,vv,tt,bvh in candidates],
 'scope':'Read-only stable revision 6 native PCB/package/case surface screen. Old IC20/KK1 are excluded because replaced by the isolated pair. Pair contact characterized separately by exact STEP.',
 'limitations':['BVH positives are possible triangle surface crossings, negatives exclude such crossings for screened geometry. This does not certify complete containment, elastic spring deformation, tolerance stack, lead fit or hardware fit.',
 'All scene source case/board seating assumptions remain. Chosen 90 degree angle and 2 mm installation height are illustrative.']}
(H/'bent-pair-native-scene-screen.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['passed_no_new_neighbor_or_case_surface_pairs','scene_hash_unchanged','scanned_original_mesh_instances','screened_candidate_obstacle_pairs','possible_surface_intersections','candidates']},indent=2))
