"""Fresh saved-file comparison: 14 PTC meshes and source metadata only."""
import ast,json,sys,hashlib
from pathlib import Path
import bpy
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
BASELINE=HERE.parents[1]/'blender-case-revision-22/x0xb0x-populated-with-case.blend'
FINAL=HERE.parent/'x0xb0x-populated-with-case.blend'
sys.path.insert(0,str(HERE))
from scene_snapshot import capture,sha,write_snapshot
record=json.loads((HERE.parent/'revision-23-change-record.json').read_text())
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
guide=record['opening_guide'];changes=record['changes'];roots=set(record['changed_source_roots'])
root_keys={'model_classification','model_limitations','detailed_model_revision','selected_native_source_glb_sha256','source_geometry_basis'}
unexpected=[]
for path in diff(before,after):
 if path[0]=='scene_props' and (path[1] in {'visualization_revision','opening_notes_text'} or str(path[1]).startswith('revision_23_')):continue
 if path[:2]==('texts',guide):continue
 if path[0]=='objects' and path[1] in changes and path[2]=='data':continue
 if path[0]=='objects' and path[1] in roots and path[2]=='props' and path[3] in root_keys:continue
 unexpected.append([str(p) for p in path])
check('Both frozen files match recorded hashes',bhash==record['baseline_sha256'] and fhash==record['stable_scene_sha256'])
check('All1721 object identities retained with none added',set(before['objects'])==set(after['objects']) and len(after['objects'])==1721)
check('Only declared PTC mesh data and source/guide metadata change',not unexpected,unexpected=unexpected[:30])
check('All14 PTC meshes match recorded old and new exact native geometry',len(changes)==14 and all(before['objects'][n]['data']==v['old_mesh'] and after['objects'][n]['data']==v['new_mesh'] for n,v in changes.items()))
check('All materials are retained exactly with none added',before['materials']==after['materials'])
check('491 references,40 LEDs,40 spacers and23 caps retained',sum(bool(o['props'].get('source_reference')) for o in after['objects'].values())==491 and sum(o['props'].get('source_board')=='mainboard' and str(o['props'].get('source_reference','')).startswith('LED') for o in after['objects'].values())==40 and sum(n.endswith('/STD240B spacer') for n in after['objects'])==40 and sum(n.endswith(' / switch cap proxy') for n in after['objects'])==23)
check('Every displayed instance pose and legend glyph retained in four frames',all(before['frames'][f]['displayed']==after['frames'][f]['displayed'] and before['frames'][f]['glyph_geometry']==after['frames'][f]['glyph_geometry'] for f in ['1','80','120','160']))
check('Only one current opening guide added',set(after['texts'])-set(before['texts'])=={guide} and hashlib.sha256(after['texts'][guide].encode()).hexdigest()==record['opening_guide_sha256'])
check('All rear passages remain clear',old_openings['passed'] and openings['passed'] and openings['check_count']==44 and openings['ray_count']==974)
check('Frozen scene files remain byte-identical after audit',sha(BASELINE)==bhash and sha(FINAL)==fhash)
failures=[c for c in checks if not c['passed']]
out=dict(passed=not failures,check_count=len(checks),checks=checks,failures=failures,stable_scene_sha256=fhash,baseline_sha256=bhash,frames=4,native_reference_count=491,stored_object_count=1721,changed_geometry_objects=sorted(changes),added_materials=[],read_only=True,physical_fit_qualified=False)
(HERE/'final-saved-scene-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(passed=out['passed'],check_count=len(checks),failures=failures),indent=2),flush=True);assert not failures
