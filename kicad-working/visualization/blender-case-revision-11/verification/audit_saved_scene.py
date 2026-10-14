"""Fresh-file comparison allowing only eleven rear legend normal translations."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
BASELINE=HERE.parent.parent/'blender-case-revision-10/x0xb0x-populated-with-case.blend'
FINAL=HERE.parent/'x0xb0x-populated-with-case.blend'
sys.path.insert(0,str(HERE))
from scene_snapshot import capture,sha,write_snapshot
LABELS={r+' label'for r in ['POWER0','HEADPHONE0','MIXIN0','MIXOUT0','CV0','GATE0','USB0','DIN1','DIN2','DIN3','DIN4']}
BASELINE_SHA='9c75786aa2ea7a551ef68ed0715c6ac8ef12455213dd24192e5a07f4d00f1d07'
checks=[]
def check(name,passed,**details):checks.append(dict(check=name,passed=bool(passed),**details))
def without(d,keys):return{k:v for k,v in d.items()if k not in keys}
def source_normal_translation(old,new):
    return all(old[i][j]==new[i][j]for i in range(4)for j in range(4)if(i,j)!=(2,3))and new[2][3]<old[2][3]
def displayed_normal_translation(old,new,normal):
    delta=Vector([new[i][3]-old[i][3]for i in range(3)]);along=delta.dot(normal)
    return (all(old[i][j]==new[i][j]for i in range(4)for j in range(4)if j!=3)
            and along<0 and(delta-normal*along).length<1e-7)
baseline_sha,final_sha=sha(BASELINE),sha(FINAL)
bpy.ops.wm.open_mainfile(filepath=str(BASELINE));before=capture()
bpy.ops.wm.open_mainfile(filepath=str(FINAL));after=capture()
write_snapshot(HERE/'before-scene.json.gz',before);write_snapshot(HERE/'after-scene.json.gz',after)
check('Baseline 10 is the frozen saved scene',baseline_sha==BASELINE_SHA)
b,a=before['objects'],after['objects'];check('All existing object identities retained with none added',set(a)==set(b))
changed_data={name for name in a if a[name].get('data')!=b[name].get('data')}
changed_objects={name for name in a if a[name]!=b[name]}
check('No stored geometry, FONT data, shading or material assignments change',not changed_data,changed_geometry=sorted(changed_data))
check('Exactly the eleven rear legend objects change stored pose',changed_objects==LABELS,changed_objects=sorted(changed_objects))
for name,old in b.items():
    new=a.get(name)
    if name in LABELS:
        check('Legend retains every property except normal translation: '+name,
              new is not None and without(old,{'matrix_basis','matrix_world'})==without(new,{'matrix_basis','matrix_world'})
              and source_normal_translation(old['matrix_basis'],new['matrix_basis'])
              and source_normal_translation(old['matrix_world'],new['matrix_world']))
    else:check('Original object geometry, material, pose, hierarchy and provenance retained: '+name,new==old)
    check('Original mesh, editable FONT or curve data retained: '+name,
          new is not None and old.get('data')==new.get('data'))
old_refs={v['reference']:name for name,v in b.items()if v['props'].get('source_reference')}
new_refs={v['reference']:name for name,v in a.items()if v['props'].get('source_reference')}
check('All491 fitted native component identities retained',old_refs==new_refs and len(new_refs)==491)
check('Native split remains409 mainboard and82 IO',sum(k.startswith('mainboard/')for k in new_refs)==409 and sum(k.startswith('ioboard/')for k in new_refs)==82)
check('All native reference objects and meshes remain exact',all(a.get(name)==row for name,row in b.items()if row['reference']))
for frame in ('1','80','120','160'):
    old,new=before['frames'][frame],after['frames'][frame]
    panel=old['objects']['Rear panel — original DXF']['matrix_world'];normal=Vector([panel[i][2]for i in range(3)]).normalized()
    check('Stored/evaluated identity sets retained frame'+frame,set(old['objects'])==set(new['objects'])and set(old['displayed'])==set(new['displayed']))
    for name,original in old['objects'].items():
        current=new['objects'].get(name)
        if name in LABELS:
            ok=current is not None and without(original,{'matrix_world'})==without(current,{'matrix_world'})and source_normal_translation(original['matrix_world'],current['matrix_world'])
        else:ok=original==current
        check('Evaluated pose/visibility retained except authorized legend normal frame'+frame+': '+name,ok)
    for name,original in old['displayed'].items():
        current=new['displayed'].get(name)
        if name in LABELS:ok=current is not None and len(original)==len(current)and all(displayed_normal_translation(x,y,normal)for x,y in zip(original,current))
        else:ok=original==current
        check('Displayed instance matrices retained except authorized legend normal frame'+frame+': '+name,ok)
check('All materials and shader graphs unchanged',before['materials']==after['materials'])
check('All actions and animation curves unchanged',before['actions']==after['actions'])
check('All collection identities, links and visibility unchanged',before['collections']==after['collections'])
check('All existing embedded editable guides retained unchanged',all(after['texts'].get(n)==text for n,text in before['texts'].items()))
guide='00 START HERE — revision 11 assembly'
check('Exactly one new revision11 guide added',set(after['texts'])-set(before['texts'])=={guide}and'KiCad revision 11'in after['texts'].get(guide,''))
check('All cameras, timeline bindings and render settings retained',all(before[k]==after[k]for k in ('scene_camera','markers','render')))
allowed={'visualization_revision','opening_notes_text','revision_11_baseline_scene_sha256','revision_11_geometry_basis','revision_11_reseated_legend_count'}
check('Only declared revision11 metadata changes',without(before['scene_props'],allowed)==without(after['scene_props'],allowed))
check('Revision11 metadata declares actual baseline and11 translated legends',after['scene_props'].get('visualization_revision')==11 and after['scene_props'].get('opening_notes_text')==guide and after['scene_props'].get('revision_11_baseline_scene_sha256')==baseline_sha and after['scene_props'].get('revision_11_reseated_legend_count')==11)
check('All40 native LED assemblies retained without duplicate lenses',sum(k.startswith('mainboard/LED')for k in new_refs)==40 and not any(n.endswith(' / visible lens proxy')for n in a))
caps={f'S{i} / switch cap proxy'for i in range(5,28)}
check('All23 PCB-parented caps retained',caps<=set(a)and all(a[n]==b[n]and a[n]['parent']=='Mainboard — B.Cu outward in assembled view'for n in caps))
check('All6 audio hardware meshes, including refined nuts, are unchanged',all(a[n]==b[n]for n in a if n.endswith((' / black ABS washer proxy',' / black PA6 nut proxy'))))
check('Read-only inspection preserves both saved files',sha(BASELINE)==baseline_sha and sha(FINAL)==final_sha)
failures=[c for c in checks if not c['passed']]
out=dict(passed=not failures,check_count=len(checks),changed_objects=sorted(changed_objects),changed_geometry=sorted(changed_data),
         translated_rear_legend_count=len(LABELS),native_reference_count=len(new_refs),native_LED_count=40,button_cap_count=23,
         baseline_scene_sha256=baseline_sha,stable_scene_sha256=final_sha,stable_scene_bytes=FINAL.stat().st_size,
         read_only=True,physical_fit_qualified=False,failures=failures,checks=checks)
(HERE/'final-saved-scene-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items()if k!='checks'},indent=2));assert not failures,'Saved scene preservation audit failed'
