import bpy,json,hashlib,struct
from mathutils import Matrix
from pathlib import Path
H=Path(__file__).resolve().parent;S=H.parent;old=S.parent/'blender-case-revision-6/x0xb0x-populated-with-case.blend';final=S/'x0xb0x-populated-with-case.blend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
start_sha=sha(final);checks=[]
removed_lenses={f'LED{i} / visible lens proxy' for i in range(1,41)}
cap_names={f'S{i} / switch cap proxy' for i in range(5,28)}
board_name='Mainboard — B.Cu outward in assembled view'
def check(n,v):checks.append({'check':n,'passed':bool(v)})
def capture():
 result={}
 for frame in [1,80,120,160]:
  bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();result[frame]={o.name:{'matrix':[list(r) for r in o.matrix_world],'type':o.type,'text':o.data.body if o.type=='FONT' else None,'hide_render':o.hide_render,'hide_viewport':o.hide_viewport} for o in bpy.data.objects if not o.get('source_board')}
  actual_caps={n:[] for n in cap_names}
  for ins in bpy.context.evaluated_depsgraph_get().object_instances:
   if ins.object.original.name in actual_caps:actual_caps[ins.object.original.name].append([list(r)for r in ins.matrix_world])
  for n,matrices in actual_caps.items():
   if n in result[frame]:
    result[frame][n]['evaluated_instance_matrices']=matrices
    obj=bpy.data.objects[n]
    result[frame][n]['stored_local_to_parent']=[list(r)for r in obj.matrix_parent_inverse @ obj.matrix_basis]
 return result
def curve_geometry():
 return {o.name:{'points':[[list(p.co) for p in spline.points] for spline in o.data.splines], 'bevel_depth':o.data.bevel_depth,'closed_caps':o.data.use_fill_caps} for o in bpy.data.objects if o.type=='CURVE'}
bpy.ops.wm.open_mainfile(filepath=str(old));before=capture();old_curves=curve_geometry();old_fonts={o.name:o.data.body for o in bpy.data.objects if o.type=='FONT'}
bpy.ops.wm.open_mainfile(filepath=str(final));after=capture();check('All existing cable and reference curve geometry preserved',curve_geometry()==old_curves)
for frame,rows in before.items():
 for n,r in rows.items():
  if n in removed_lenses:
   check('Redundant standalone LED lens removed: '+n,n not in after[frame])
   continue
  if n in cap_names:
   continue
  q=after[frame].get(n)
  check(f'Preserved original presentation pose/visibility at frame{frame}: '+n,q is not None and r['type']==q['type'] and r['text']==q['text'] and r['hide_render']==q['hide_render'] and r['hide_viewport']==q['hide_viewport'] and max(abs(a-b) for x,y in zip(r['matrix'],q['matrix']) for a,b in zip(x,y))<1e-7)
attachment=json.loads((H/'front-control-assembly-change.json').read_text())
for frame in [1,80,120,160]:
 for n in cap_names:
  baseline=before[1][n]['evaluated_instance_matrices']
  check('Exactly one original displayed cap at frame1: '+n,len(baseline)==1)
  expected=Matrix(after[frame][board_name]['matrix']) @ Matrix(before[1][board_name]['matrix']).inverted() @ Matrix(baseline[0])
  actual=Matrix(after[frame][n]['matrix'])
  wanted=attachment['cap_effective_visibility'][str(frame)][n]
  if not wanted['hide_viewport']:
   check(f'Cap follows PCB with original assembled seat at frame{frame}: '+n,max(abs(a-b) for x,y in zip(actual,expected) for a,b in zip(x,y))<1e-7)
  else:
   # Blender excludes hidden objects from viewport transform evaluation. Their
   # raw matrix_world can be a stale cache, so inspect the stored constant PCB
   # attachment instead; there is no displayed world pose in these frames.
   local=Matrix(before[1][board_name]['matrix']).inverted() @ Matrix(baseline[0])
   stored=Matrix(after[frame][n]['stored_local_to_parent'])
   check(f'Hidden cap retains original PCB-relative attachment at frame{frame}: '+n,max(abs(a-b)for x,y in zip(stored,local)for a,b in zip(x,y))<1e-7)
  check(f'Inspection cap visibility at frame{frame}: '+n,all(after[frame][n][key]==value for key,value in wanted.items()))
  displayed=after[frame][n]['evaluated_instance_matrices']
  if not wanted['hide_viewport']:
   check(f'Exactly one actual displayed PCB cap at frame{frame}: '+n,len(displayed)==1 and max(abs(a-b)for x,y in zip(Matrix(displayed[0]),expected)for a,b in zip(x,y))<1e-7)
  else:
   check(f'Hidden inspection cap has no visible instance at frame{frame}: '+n,not displayed)
check('Exactly40 standalone LED lens doubles removed',len(attachment['removed_duplicate_LED_lenses'])==40 and set(attachment['removed_duplicate_LED_lenses'])==removed_lenses)
for n,body in old_fonts.items():check('Original editable label retained '+n,n in bpy.data.objects and bpy.data.objects[n].data.body==body)
s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();refs={(o.get('source_board'),o['source_reference']) for o in bpy.data.objects if o.get('source_reference')}
check('491 saved model references',len(refs)==491)
check('Exactly40 native LED references and23 physical caps',sum(b=='mainboard' and r.startswith('LED') for b,r in refs)==40 and all(n in bpy.data.objects for n in cap_names) and not any(n in bpy.data.objects for n in removed_lenses))
check('Every cap is attached to mainboard',all(bpy.data.objects[n].parent==bpy.data.objects[board_name] for n in cap_names))
front=bpy.data.objects['Front controls — presentation proxies']
check('Caps no longer belong to old front-panel instance source',all(bpy.data.objects[n].name not in front.instance_collection.all_objects for n in cap_names))
display=bpy.data.collections.get(attachment['cap_display_collection'])
check('23 caps belong to one ordinary scene collection',display is not None and display.name in bpy.context.scene.collection.children and {o.name for o in display.objects}==cap_names)
check('Cap collection is not instanced anywhere',display is not None and not any(o.instance_collection==display for o in bpy.data.objects))
check('Caps explicitly hidden in control-side frame120',all(after[120][n]['hide_render']and after[120][n]['hide_viewport'] for n in cap_names))
check('409mainboard82IO',(sum(b=='mainboard' for b,r in refs),sum(b=='ioboard' for b,r in refs))==(409,82))
source=[c for c in bpy.data.collections if 'immutable native KiCad GLB' in c.name];check('Both full native source collections survive reopen',len(source)==2 and all(c.use_fake_user for c in source))
curves=[o for o in bpy.data.objects if o.type=='CURVE' and o.get('pin') is not None]
# Builder records its own exact identities; do not classify auxiliary outline curves as cables.
h=json.loads((S/'harness-routing-study-audit.json').read_text());check('24 cable study conductors',h['conductor_count']==24)
check('Original native geometry unchanged by wiring study',h['all_source_mesh_geometry_unchanged'])
check('Existing views unchanged by wiring study',h['existing_frames_1_80_120_pose_and_visibility_unchanged'])
check('All cable native endpoint checks',all(x['passed'] for x in h['endpoint_checks']))
check('All study connection checks',all(x['passed'] for x in h['connection_endpoint_checks']))
check('Saved scene remains byte unchanged by inspection',sha(final)==start_sha)
failed=[c for c in checks if not c['passed']]
r={'passed':not failed,'check_count':len(checks),'failures':failed,'reference_count':491,'original_editable_label_count':len(old_fonts),'native_source_meshes':{c.name:sum(o.type=='MESH' for o in c.objects) for c in source},'stable_scene_sha256':start_sha,'stable_scene_bytes':final.stat().st_size,'harness_study_only':True,'cap_visibility_contract':'Actual rendered/evaluated instance matrices verified at visible frames1/80. Frames120/160 intentionally hide caps in both viewport and render, matching original views; stored PCB-relative matrices are verified instead of stale hidden matrix_world caches.','checks':checks}
(H/'final-saved-scene-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='checks'},indent=2))
