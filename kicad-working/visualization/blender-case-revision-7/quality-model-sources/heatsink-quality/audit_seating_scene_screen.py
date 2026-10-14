"""Read saved scene, screen a transient candidate pose, never save scene."""
from pathlib import Path
import bpy,json,hashlib
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
H=Path(__file__).resolve().parent;W=H.parents[2]
scene_path=W/'visualization/blender-case-revision-5/x0xb0x-populated-with-case.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(scene_path)
bpy.ops.wm.open_mainfile(filepath=str(scene_path));bpy.context.scene.frame_set(1)
io=bpy.data.objects['I/O board — rear mounting approximation']
root=next(o for o in io.instance_collection.objects if o.get('source_reference')=='KK1')
pose=io.matrix_world@root.matrix_world@Matrix.Translation(Vector((0,-.00878,.00390)))
mesh_path=H/'Aavid_574502B00000G_DrawingDerived_FoldedSpring.stl';mesh_sha=sha(mesh_path)
bpy.ops.wm.stl_import(filepath=str(mesh_path),global_scale=.001)
candidate=bpy.context.object
# STL stores millimetres in mesh coordinates; global_scale is on its imported
# object matrix. Apply that factor explicitly before the native metre pose.
vertices=[pose@(v.co*.001) for v in candidate.data.vertices];polys=[tuple(p.vertices) for p in candidate.data.polygons]
heat=BVHTree.FromPolygons(vertices,polys,all_triangles=True,epsilon=1e-9)
def bounds(vs):return [min(v[i] for v in vs) for i in range(3)]+[max(v[i] for v in vs) for i in range(3)]
hb=bounds(vertices)
def ref(obj):
 while obj:
  if obj.get('source_reference'):return obj.get('source_board'),obj['source_reference']
  obj=obj.parent
 return None
allowed={'Mainboard — B.Cu outward in assembled view','I/O board — rear mounting approximation','Case / bottom','Case / upper','Rear panel — original DXF','Top panel — original DXF','Spacers — original length, approximate seats'}
rows=[];scanned=0
for inst in bpy.context.evaluated_depsgraph_get().object_instances:
 o=inst.object
 if o.type!='MESH' or not inst.is_instance:continue
 parent=inst.parent.original.name if inst.parent else ''
 if parent not in allowed:continue
 r=ref(o.original)
 if r==('ioboard','KK1'):continue
 scanned+=1
 # Transform object bounding box first to avoid millions of irrelevant verts.
 bb=bounds([inst.matrix_world@Vector(v) for v in o.bound_box])
 aabb=all(hb[i]<=bb[i+3] and bb[i]<=hb[i+3] for i in range(3))
 if not aabb and not parent.startswith('Case /'):continue
 me=o.to_mesh();me.calc_loop_triangles();vv=[inst.matrix_world@v.co for v in me.vertices];tt=[tuple(t.vertices) for t in me.loop_triangles]
 obstacle=BVHTree.FromPolygons(vv,tt,all_triangles=True,epsilon=1e-9)
 overlaps=heat.overlap(obstacle)
 # This sampled distance is a vertex-to-surface measurement, not certified
 # complete solid clearance. Zero possible triangle pairs is the useful screen.
 closest=min((obstacle.find_nearest(v)[3] for v in vertices),default=None)
 rows.append({'parent':parent,'object':o.original.name,'reference':list(r) if r else None,
              'world_bounds_mm':[v*1000 for v in bounds(vv)],'AABB_overlaps':aabb,
              'possible_triangle_overlap_pairs':len(overlaps),'minimum_candidate_vertex_to_surface_mm':closest*1000 if closest is not None else None})
 o.to_mesh_clear()
out={'scope':'Read-only assembled saved-scene native/case triangle surface screen of transient newKK1 geometry at proposed offset. No scene saved; BVH overlap positives are possible intersections, negatives exclude triangle surface crossings.',
     'saved_scene':str(scene_path),'saved_scene_sha256':before,'candidate_stl_sha256':mesh_sha,
     'proposed_model_offset_mm':[0,-8.78,3.9],'candidate_world_matrix_metres':[list(r) for r in pose],
     'candidate_world_bounds_mm':[v*1000 for v in hb],'scanned_mesh_instances':scanned,'screened_AABB_or_case_meshes':len(rows),'records':rows,
     'possible_non_IC20_surface_intersections':[r for r in rows if r['possible_triangle_overlap_pairs'] and r['reference']!=['ioboard','IC20']],
     'scene_hash_unchanged':before==sha(scene_path),'candidate_mesh_hash_unchanged':mesh_sha==sha(mesh_path),
     'limitations':['Native scene is stable revision5/revision8 population. Source-derived scene enclosure and seating assumptions remain; this is not hardware fit.',
                    'This is a bounded mesh surface screen, not exact BRep minimum-distance/tolerance analysis or a universal complete-containment test.',
                    'Intentional nominal spring-finger intersection withIC20 is separately characterized by exact BRep; positive BVH pairs are not treated as springfit proof.']}
out['passed_no_new_neighbor_or_case_surface_pairs']=not out['possible_non_IC20_surface_intersections']
(H/'independent-seating-scene-screen.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['passed_no_new_neighbor_or_case_surface_pairs','candidate_world_bounds_mm','scanned_mesh_instances','screened_AABB_or_case_meshes','possible_non_IC20_surface_intersections','scene_hash_unchanged','candidate_mesh_hash_unchanged']},indent=2))
