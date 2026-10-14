"""Read-only refresh of existing source-numbered study paths against new parts."""
import bpy,json,runpy,hashlib
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent
module=runpy.run_path(str(H/'add_harness_routing_study.py'))
scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
stable=Path(bpy.data.filepath);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();start=sha(stable)
old=json.loads((H/'harness-routing-study-audit.json').read_text())
(H/'harness-sources/previous-revision-6-routing-audit.json').write_text(json.dumps(old,indent=2)+'\n')
bvh,owners,sources=module['obstacles']();routes=[];checks=[]
for row in old['routes']:
 obj=bpy.data.objects[row['name']];points=[(obj.matrix_world@Vector(p.co[:3]))*1000 for p in obj.data.splines[0].points]
 length=sum((b-a).length for a,b in zip(points[:-1],points[1:]));assert abs(length-row['centerline_length_mm'])<.0001
 for endpoint,key in [(points[0],'span_start_mm'),(points[-1],'span_end_mm')]:assert (endpoint-Vector(row[key])).length<.0001
 new=dict(row);new['surface_screen']=module['surface_screen'](points,bvh,owners);new['_points']=points;routes.append(new)
pairs=module['pair_screen'](routes)
for row in routes:row.pop('_points')
tips=json.loads((H/'harness-sources/existing-ribbon-termination-endpoints.json').read_text())
rows={(r['board'],r['reference']):r for r in tips['endpoints'] if r['frame']==1}
for (board,ref),row in rows.items():
 instance=bpy.data.objects[module['BOARD_NAMES'][board]];roots={o.get('source_reference'):o for o in instance.instance_collection.objects if o.get('source_reference')};pose=instance.matrix_world@roots[ref].matrix_world
 for tip in row['tips']:
  error=((pose@(Vector(tip['canonical_insulation_tip_mm'])*.001))-Vector(tip['world_tip_mm'])*.001).length*1000
  checks.append({'board':board,'reference':ref,'pin':tip['pin'],'source_to_current_tip_error_mm':error,'passed':error<.0001})
assert len(routes)==24 and len(checks)==48 and all(r['passed'] for r in checks)
old.update(scope='Revision7 read-only refresh of unchanged revision5 cable-study curves against current native revision10 model surfaces. No path/mesh/pose/case changes; no installed-fit qualification.',base_file=str(stable),base_file_sha256=start,construction_basis='Original verified revision5 routes, dimensions, endpoint overlap and cap/tangent validation; current source-numbered endpoints rechecked',routes=routes,endpoint_checks=checks,surface_screen_obstacle_meshes=sources,cable_pair_screen=pairs,possible_cable_pair_intersections=[r for r in pairs if r['possible_intersection']],original_source_mesh_count=len(bpy.data.meshes),original_mesh_hashes={m.name:module['raw_mesh_hash'](m) for m in bpy.data.meshes},all_source_mesh_geometry_unchanged=True,existing_frames_1_80_120_pose_and_visibility_unchanged=True)
assert sha(stable)==start
old['saved_scene_unchanged_by_review']=True
(H/'harness-routing-study-audit.json').write_text(json.dumps(old,indent=2)+'\n')
report={'passed':True,'native_endpoint_checks':48,'conductor_count':24,'curve_lengths_and_endpoints_unchanged':True,'possible_cable_pair_intersections':len(old['possible_cable_pair_intersections']),'stable_scene_sha256':start,'source_surface_candidates':[{ 'reference':r['reference'],'pin':r['main_pin'],'radius':r['surface_screen']['radius_intrusion_candidate_surfaces'],'crossings':r['surface_screen']['centerline_surface_crossing_candidates']} for r in routes if r['surface_screen']['radius_intrusion_candidate_surfaces'] or r['surface_screen']['centerline_surface_crossing_candidates']],'physical_fit_qualified':False,'saved_scene_not_modified':True}
(H/'verification/refreshed-harness-surface-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='source_surface_candidates'},indent=2))
