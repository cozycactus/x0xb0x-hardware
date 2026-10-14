"""Read-only LED/native-body and button/cap review, original panel coordinates."""
from pathlib import Path
import bpy,json,hashlib,math
from mathutils import Vector
H=Path(__file__).resolve().parent;W=H.parents[2]
path=W/'visualization/blender-case-revision-6/x0xb0x-populated-with-case.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(path)
bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene
panel=bpy.data.objects['Top panel — original DXF'];board=bpy.data.objects['Mainboard — B.Cu outward in assembled view'];front=bpy.data.objects['Front controls — presentation proxies']
source=json.loads((W/'visualization/blender-case-revision-6/panels/original-panels.json').read_text())['mainpanel']
circles={r['board_reference']:r for r in source['circles'] if r.get('board_reference')};rects={r['board_reference']:r for r in source['rectangular_cutouts']}
refs=['LED'+str(i) for i in range(1,41)]+['S'+str(i) for i in range(5,28)]
def anc(o):
 while o:
  if o.get('source_reference'):return o['source_reference']
  o=o.parent
native={r:[o for o in board.instance_collection.objects if o.type=='MESH' and anc(o)==r] for r in refs}
proxies={r:[o for o in front.instance_collection.objects if o.type=='MESH' and o.name.startswith(r+' / ')] for r in refs}
def bound(vv):
 return {'min_mm':[min(v[i] for v in vv) for i in range(3)],'max_mm':[max(v[i] for v in vv) for i in range(3)]} if vv else None
frames=[]
for f in [1,80,120]:
 scene.frame_set(f);bpy.context.view_layer.update();inv=panel.matrix_world.inverted();deps=bpy.context.evaluated_depsgraph_get()
 def pts(o,inst):
  e=o.evaluated_get(deps);me=e.to_mesh();matrix=inv@inst.matrix_world@o.matrix_world;vv=[matrix@v.co*1000 for v in me.vertices];e.to_mesh_clear();return vv
 rows=[]
 for r in refs:
  nv=[p for o in native[r] for p in pts(o,board)];pv=[p for o in proxies[r] for p in pts(o,front)];nb=bound(nv);pb=bound(pv)
  row={'reference':r,'native_objects':[o.name for o in native[r]],'native_bounds_panel_mm':nb,'proxy_objects':[o.name for o in proxies[r]],'proxy_bounds_panel_mm':pb}
  if r.startswith('LED'):
   c=circles[r];center=c['center_mm'];row['DXF_hole_center_mm']=center;row['DXF_hole_radius_mm']=c['radius_mm']
   row['proxy_center_alignment_error_mm']=math.dist([(pb['min_mm'][i]+pb['max_mm'][i])/2 for i in range(2)],center)
   row['native_AABB_center_alignment_error_mm']=math.dist([(nb['min_mm'][i]+nb['max_mm'][i])/2 for i in range(2)],center)
   root=native[r][0]
   while not root.get('source_reference'):root=root.parent
   native_origin=inv@board.matrix_world@root.matrix_world@Vector((0,0,0))
   row['native_reference_origin_panel_mm']=[v*1000 for v in native_origin]
   row['native_reference_origin_xy_alignment_error_mm']=math.dist([native_origin[i]*1000 for i in range(2)],center)
   lens_axis=inv@board.matrix_world@root.matrix_world@Vector((.00127,0,.003))
   row['native_lens_axis_at_lower_flange_panel_mm']=[v*1000 for v in lens_axis]
   row['native_lens_axis_xy_alignment_error_mm']=math.dist([lens_axis[i]*1000 for i in range(2)],center)
   row['reference_origin_note']='Native root includes the existing model transform; generic lens axis is sourceX1.27mm, not sourceX0.'
   row['AABB_center_note']='Generic LED has a polarity flat; AABB midpoint is not its lens axis.'
   row['native_tip_below_panel_underside_mm']=-nb['max_mm'][2]
   row['native_tip_to_proxy_bottom_normal_gap_mm']=pb['min_mm'][2]-nb['max_mm'][2]
   row['proxy_tip_above_panel_top_mm']=pb['max_mm'][2]-1.5748
  else:
   lo,hi=rects[r]['bounds_mm'];edge=[pb['min_mm'][0]-lo[0],hi[0]-pb['max_mm'][0],pb['min_mm'][1]-lo[1],hi[1]-pb['max_mm'][1]]
   row.update(DXF_cutout_bounds_mm=[lo,hi],full_cap_AABB_to_cutout_edges_mm=edge,minimum_cap_clearance_mm=min(edge),cap_height_mm=pb['max_mm'][2]-pb['min_mm'][2],cap_visible_above_panel_top_mm=pb['max_mm'][2]-1.5748,
              nominal_actuator_tip_into_cap_bottom_mm=nb['max_mm'][2]-pb['min_mm'][2])
  rows.append(row)
 frames.append({'frame':f,'panel_world_matrix':[list(r) for r in panel.matrix_world],'board_world_matrix':[list(r) for r in board.matrix_world],'front_proxies_world_matrix':[list(r) for r in front.matrix_world],
  'panel_hidden_render':panel.hide_render,'board_hidden_render':board.hide_render,'front_proxies_hidden_render':front.hide_render,'rows':rows})
report={'scope':'Read-only current stable Blender6 front controls/LED relation and original DXF check. No source project or scene saved.',
 'scene':str(path),'scene_sha256':before,'scene_hash_unchanged':before==sha(path),'units':'mm','coordinate_frame':'Top-panel local XYZ; underside Z0, top surface Z1.5748. Frame80 flipped board means global panel-axis extents are not installation heights.',
 'native_LED_reference_count':sum(bool(native[r]) for r in refs if r.startswith('LED')),'LED_proxy_count':sum(len(proxies[r]) for r in refs if r.startswith('LED')),
 'native_button_reference_count':sum(bool(native[r]) for r in refs if r.startswith('S')),'cap_proxy_count':sum(len(proxies[r]) for r in refs if r.startswith('S')),
 'frames':frames}
(H/'front-control-native-measurements.json').write_text(json.dumps(report,indent=2)+'\n')
for frame in frames:
 led=[r for r in frame['rows'] if r['reference'].startswith('LED')];caps=[r for r in frame['rows'] if r['reference'].startswith('S')]
 print(json.dumps({'frame':frame['frame'],'visibility':[frame[k] for k in ['panel_hidden_render','board_hidden_render','front_proxies_hidden_render']],
 'LED_native_tip_Z_range_mm':[min(r['native_bounds_panel_mm']['max_mm'][2] for r in led),max(r['native_bounds_panel_mm']['max_mm'][2] for r in led)],
 'LED_proxy_min_Z_range_mm':[min(r['proxy_bounds_panel_mm']['min_mm'][2] for r in led),max(r['proxy_bounds_panel_mm']['min_mm'][2] for r in led)],
 'LED_proxy_max_Z_range_mm':[min(r['proxy_bounds_panel_mm']['max_mm'][2] for r in led),max(r['proxy_bounds_panel_mm']['max_mm'][2] for r in led)],
 'max_LED_proxy_xy_alignment_error_mm':max(r['proxy_center_alignment_error_mm'] for r in led),
 'cap_min_edge_clearance_mm':min(r['minimum_cap_clearance_mm'] for r in caps),'cap_visible_above_panel_mm':[min(r['cap_visible_above_panel_top_mm'] for r in caps),max(r['cap_visible_above_panel_top_mm'] for r in caps)],
 'cap_actuator_insertion_mm':[min(r['nominal_actuator_tip_into_cap_bottom_mm'] for r in caps),max(r['nominal_actuator_tip_into_cap_bottom_mm'] for r in caps)]},indent=2))
