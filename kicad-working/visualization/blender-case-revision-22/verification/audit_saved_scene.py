"""Fresh saved-file comparison: 40 spacer meshes and source metadata only."""
import ast,json,sys,hashlib
from pathlib import Path
import bpy
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
BASELINE=HERE.parents[1]/'blender-case-revision-21/x0xb0x-populated-with-case.blend'
FINAL=HERE.parent/'x0xb0x-populated-with-case.blend'
sys.path.insert(0,str(HERE))
from scene_snapshot import capture,sha,write_snapshot
record=json.loads((HERE.parent/'revision-22-change-record.json').read_text())
checks=[]
def check(name,passed,**details):checks.append(dict(check=name,passed=bool(passed),**details))
def diff(a,b,path=()):
    out=[]
    if isinstance(a,dict) and isinstance(b,dict):
        for k in sorted(set(a)|set(b)):
            if k not in a or k not in b:out.append(path+(k,))
            else:out+=diff(a[k],b[k],path+(k,))
    elif isinstance(a,list) and isinstance(b,list):
        if len(a)!=len(b):out.append(path)
        else:
            for i,(x,y) in enumerate(zip(a,b)):out+=diff(x,y,path+(i,))
    elif isinstance(a,float) and isinstance(b,float):
        if abs(a-b)>1e-7:out.append(path)
    elif a!=b:out.append(path)
    return out
source=REPO/'scripts/verify_rear_openings.py'
tree=ast.parse(source.read_text());nodes=[]
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='original_frame' for t in node.targets):break
    nodes.append(node)
ns={'__file__':str(source)};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),ns)
bhash,fhash=sha(BASELINE),sha(FINAL)
bpy.ops.wm.open_mainfile(filepath=str(BASELINE));before=json.loads(json.dumps(capture()));old_openings=ns['verify']()
bpy.ops.wm.open_mainfile(filepath=str(FINAL));after=json.loads(json.dumps(capture()));openings=ns['verify']()
write_snapshot(HERE/'before-scene.json.gz',before);write_snapshot(HERE/'after-scene.json.gz',after)
(HERE/'rear-openings-audit.json').write_text(json.dumps(openings,indent=2)+'\n')
guide=record['opening_guide'];black=record['added_materials'][0];added=set(record['added_objects']);roots=set(record['changed_source_roots'])
root_keys={'model_classification','model_limitations','detailed_model_revision','selected_native_source_glb_sha256','source_geometry_basis'}
check('All1681 existing object identities retained with exactly40 spacer additions',set(after['objects'])-set(before['objects'])==added and set(before['objects'])<=set(after['objects']) and len(after['objects'])==1721)
check('All added meshes match the recorded exact native spacers',all(after['objects'][p['object']]['data']==p['mesh'] and after['objects'][p['object']]['parent']=='MAINBOARD/'+p['reference'] for p in record['native_parts']))
# Strip only explicitly declared additions before exhaustive comparison.
import copy
clean=copy.deepcopy(after)
for name in added:del clean['objects'][name]
for collection in clean['collections'].values():collection['objects']=[n for n in collection['objects'] if n not in added]
for frame in clean['frames'].values():
 for category in ['objects','displayed','glyph_geometry']:
  frame[category]={n:v for n,v in frame[category].items() if n not in added}
for name in roots:
 for key in root_keys:
  if key in before['objects'][name]['props']:clean['objects'][name]['props'][key]=before['objects'][name]['props'][key]
  else:clean['objects'][name]['props'].pop(key,None)
del clean['materials'][black];del clean['texts'][guide]
for key in list(clean['scene_props']):
 if key.startswith('revision_22_'):del clean['scene_props'][key]
for key in ['visualization_revision','opening_notes_text']:clean['scene_props'][key]=before['scene_props'][key]
unexpected=diff(before,clean)
check('Every original mesh, shader, pose, collection, camera, glyph and animation retained',not unexpected,unexpected=[[str(v) for v in p] for p in unexpected[:30]])
check('Exactly one black thermoplastic material added',set(after['materials'])-set(before['materials'])=={black} and after['materials'][black]==record['material_signature'])
check('All491 native references,40 LEDs and23 caps retained',sum(bool(o['props'].get('source_reference')) for o in after['objects'].values())==491 and sum(o['props'].get('source_board')=='mainboard' and str(o['props'].get('source_reference','')).startswith('LED') for o in after['objects'].values())==40 and sum(n.endswith(' / switch cap proxy') for n in after['objects'])==23)
from mathutils import Matrix
pose_checks=[]
for f in ['1','80','120','160']:
 for p in record['native_parts']:
  root='MAINBOARD/'+p['reference'];name=p['object']
  body=root+'/mesh.002'
  frame=after['frames'][f]
  body_to_spacer=Matrix(frame['objects'][body]['matrix_world']).inverted()@Matrix(frame['objects'][root]['matrix_world'])@Matrix(p['matrix_local'])
  expected=[Matrix(m)@body_to_spacer for m in frame['displayed'].get(body,[])]
  actual=after['frames'][f]['displayed'].get(name,[])
  ok=len(expected)==len(actual) and all(any(max(abs(a-b) for r,t in zip(e,m) for a,b in zip(r,t))<1e-6 for m in actual) for e in expected)
  pose_checks.append(ok)
check('All40 spacers follow rendered LED bodies and visibility in all four poses',all(pose_checks),instance_pose_checks=len(pose_checks))
check('One current guide added without changing old guides',set(after['texts'])-set(before['texts'])=={guide} and hashlib.sha256(after['texts'][guide].encode()).hexdigest()==record['opening_guide_sha256'])
check('All rear passages remain clear',old_openings['passed'] and openings['passed'] and openings['check_count']==44 and openings['ray_count']==974)
check('Both frozen scenes match recorded hashes and remain unchanged',sha(BASELINE)==bhash==record['baseline_sha256'] and sha(FINAL)==fhash==record['stable_scene_sha256'])
failures=[c for c in checks if not c['passed']]
out=dict(passed=not failures,check_count=len(checks),checks=checks,failures=failures,stable_scene_sha256=fhash,baseline_sha256=bhash,frames=4,native_reference_count=491,stored_object_count=1721,added_geometry_objects=sorted(added),added_materials=[black],read_only=True,physical_fit_qualified=False)
(HERE/'final-saved-scene-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(passed=out['passed'],check_count=len(checks),failures=failures),indent=2),flush=True)
assert not failures,'Saved-scene audit failed'
