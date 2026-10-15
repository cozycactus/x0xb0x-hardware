"""Fresh saved-file comparison: USB mesh, five root fields and one gold shader only."""
import ast,json,sys,hashlib
from pathlib import Path
import bpy
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
BASELINE=HERE.parents[1]/'blender-case-revision-20/x0xb0x-populated-with-case.blend'
FINAL=HERE.parent/'x0xb0x-populated-with-case.blend'
sys.path.insert(0,str(HERE))
from scene_snapshot import capture,sha,write_snapshot
record=json.loads((HERE.parent/'revision-21-change-record.json').read_text())
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
guide=record['opening_guide'];gold=record['added_materials'][0]
root_keys={'model_classification','model_limitations','detailed_model_revision','selected_native_source_glb_sha256','source_geometry_basis'}
unexpected=[];stale=0
for path in diff(before,after):
    if path[0]=='scene_props' and (path[1] in {'visualization_revision','opening_notes_text'} or str(path[1]).startswith('revision_21_')):continue
    if path[:2]==('texts',guide):continue
    if path[:2]==('materials',gold):continue
    if path[:3]==('objects','IOBOARD/USB0/mesh','data'):continue
    if path[:3]==('objects','IOBOARD/USB0','props') and path[3] in root_keys:continue
    hidden=False
    if path[0]=='frames' and len(path)>4 and path[2]=='objects' and path[4]=='matrix_world':
        hidden=all(s['frames'][path[1]]['objects'][path[3]]['hide_viewport'] for s in [before,after])
    if path[0]=='objects' and len(path)>2 and path[2]=='matrix_world':
        hidden=all(s['frames']['1']['objects'][path[1]]['hide_viewport'] for s in [before,after])
    if hidden:stale+=1;continue
    unexpected.append([str(p) for p in path])
check('Saved files match pinned baseline and final hashes',bhash==record['baseline_sha256'] and fhash==record['stable_scene_sha256'])
check('All1681 object identities retained with none added',set(before['objects'])==set(after['objects']) and len(after['objects'])==1681)
check('No undeclared data, pose, collection, shader, guide or animation differences',not unexpected,unexpected=unexpected[:30],ignored_hidden_stale_world_matrices=stale)
check('Only USB mesh receives the exact recorded native aggregate',after['objects']['IOBOARD/USB0/mesh']['data']==record['new_mesh'] and before['objects']['IOBOARD/USB0/mesh']['data']==record['old_mesh'])
check('Only one new gold shader; every old shader retained exactly',set(after['materials'])-set(before['materials'])=={gold}
 and all(after['materials'][n]==v for n,v in before['materials'].items()) and after['materials'][gold]==record['gold_material_signature'])
check('All491 native identities retained with40 LEDs and23 caps',sum(bool(o['props'].get('source_reference')) for o in after['objects'].values())==491
 and sum(o['props'].get('source_board')=='mainboard' and str(o['props'].get('source_reference','')).startswith('LED') for o in after['objects'].values())==40
 and sum(n.endswith(' / switch cap proxy') for n in after['objects'])==23)
check('Four actual displayed instance poses and legend glyphs retained',all(before['frames'][f]['displayed']==after['frames'][f]['displayed'] and before['frames'][f]['glyph_geometry']==after['frames'][f]['glyph_geometry'] for f in ['1','80','120','160']))
check('Only one current opening guide added',set(after['texts'])-set(before['texts'])=={guide} and hashlib.sha256(after['texts'][guide].encode()).hexdigest()==record['opening_guide_sha256'])
check('Old and corrected complete assemblies retain all rear passages',old_openings['passed'] and openings['passed'] and openings['check_count']==44 and openings['ray_count']==974)
check('Both frozen saved files remain byte-identical after read-only audit',sha(BASELINE)==bhash and sha(FINAL)==fhash)
failures=[c for c in checks if not c['passed']]
out=dict(passed=not failures,check_count=len(checks),checks=checks,failures=failures,stable_scene_sha256=fhash,baseline_sha256=bhash,frames=4,native_reference_count=491,stored_object_count=1681,changed_geometry_objects=['IOBOARD/USB0/mesh'],added_materials=[gold],read_only=True,physical_fit_qualified=False)
(HERE/'final-saved-scene-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='checks'},indent=2),flush=True)
assert not failures,'Saved-scene audit failed'
