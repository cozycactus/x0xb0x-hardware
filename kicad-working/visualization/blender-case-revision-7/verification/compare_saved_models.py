from pathlib import Path
import json,collections,hashlib
H=Path(__file__).resolve().parent;S=H.parent
before=json.loads((H/'before-scene-snapshot.json').read_text());after=json.loads((H/'after-models-scene-snapshot.json').read_text());p=json.loads((S/'board-meshes/source-model-plan.json').read_text())
updated={r['board']+'/'+ref for r in p['updated_assignments'] for ref in r['references']};expected={r['board']+'/'+ref for r in p['assignments'] for ref in r['references']}
checks=[]
caps={f'S{i} / switch cap proxy' for i in range(5,28)}
def check(n,v):checks.append({'check':n,'passed':bool(v)})
check('All491 fitted references retained',set(after['reference_poses'])==set(before['reference_poses'])==expected and len(expected)==491)
check('Both assembled board instance poses identical',before['instance_poses']==after['instance_poses'])
for ref in expected:
 check('Native component pose preserved '+ref,before['reference_poses'][ref]==after['reference_poses'][ref])
 check(('Reviewed geometry changed ' if ref in updated else 'Existing native geometry preserved ')+ref,(before['references'][ref]!=after['references'][ref]) if ref in updated else before['references'][ref]==after['references'][ref])
# Renamed exact PCB layer partitions can be matched by geometry+pose content.
check('All case/control/label mounting mesh geometry and PCB layers preserved',collections.Counter(json.dumps(v,sort_keys=True) for name,v in before['other_meshes'].items() if name not in caps and not (name.startswith('LED') and name.endswith(' / visible lens proxy')))==collections.Counter(json.dumps(v,sort_keys=True) for name,v in after['other_meshes'].items() if name not in caps))
baseline=json.loads((S.parents[1]/'validation/models-review-10/front-controls-review/front-control-native-measurements.json').read_text())
panel=next(f for f in baseline['frames']if f['frame']==1)['front_proxies_world_matrix']
def multiply(a,b):return [[sum(a[i][k]*b[k][j]for k in range(4))for j in range(4)]for i in range(4)]
for name in caps:
 old=before['other_meshes'].get(name);new=after['other_meshes'].get(name)
 check('Cap mesh topology and vertices preserved '+name,old is not None and new is not None and all(old[k]==new[k]for k in ['hash','vertices','polygons']))
 expected_cap=multiply(panel,old['matrix']) if old else None
 check('Cap original rendered assembled pose preserved '+name,new is not None and expected_cap is not None and max(abs(a-b)for x,y in zip(new['matrix'],expected_cap)for a,b in zip(x,y))<1e-7)
check('Forty old standalone LED lens proxies removed',sum(name.startswith('LED') and name.endswith(' / visible lens proxy') for name in before['other_meshes'])==40 and not any(name.startswith('LED') and name.endswith(' / visible lens proxy') for name in after['other_meshes']))
failed=[c for c in checks if not c['passed']];report={'passed':not failed,'check_count':len(checks),'failures':failed,'reference_count':len(expected),'reviewed_geometry_changes':len(updated),'unchanged_reference_geometry':len(expected-updated),'case_and_PCB_layers_preserved':next(c['passed']for c in checks if c['check']=='All case/control/label mounting mesh geometry and PCB layers preserved'),'checks':checks,'limits':['Mesh invariance and nominal CAD source checks do not certify actual installed fit.','Native model transforms are preserved, including all layer flips.','Cap mesh geometry is unchanged; caps are now ordinary PCB-parented scene objects with original rendered assembled poses.']}
(H/'saved-model-geometry-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['checks','limits']},indent=2));raise SystemExit(bool(failed))
