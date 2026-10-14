#!/usr/bin/env python3
"""Read-only model, path and full non-model design invariants."""
from pathlib import Path
import argparse,collections,hashlib,json,sys
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[1]
sys.path.insert(0,str(WORK.parent/'kicad-import/validation'))
from verify_native_projects import tokens,children,one,property_value
a=argparse.ArgumentParser();a.add_argument('--saved',action='store_true');args=a.parse_args()
def tree(text):
 roots=[];stack=[]
 for t,q in tokens(text):
  if t=='(' and not q:
   n=[];(stack[-1] if stack else roots).append(n);stack.append(n)
  elif t==')' and not q:stack.pop()
  else:stack[-1].append(t)
 assert len(roots)==1 and not stack;return roots[0]
def clean(n):return [clean(x) for x in n if not isinstance(x,list) or not x or x[0]!='model'] if isinstance(n,list) else n
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def values(n):
 return dict(path=n[1],offset=[float(v) for v in one(one(n,'offset'),'xyz')[1:]],scale=[float(v) for v in one(one(n,'scale'),'xyz')[1:]],rotation=[float(v) for v in one(one(n,'rotate'),'xyz')[1:]])
plan=json.loads((HERE/'combined-model-plan.json').read_text());manifest=json.loads((HERE/'input-manifest.json').read_text())['files'];TARGET=HERE/'candidate'
checks=[];failures=[]
def check(label,condition):
 item=dict(check=label,passed=bool(condition));checks.append(item)
 if not condition:failures.append(item)
for relative,h in manifest.items():
 old=HERE/'input-snapshot'/relative;new=TARGET/relative
 check('Input snapshot hash '+relative,digest(old)==h)
 if new.suffix in {'.kicad_pcb','.kicad_mod'}:check('All non-model AST identical '+relative,clean(tree(old.read_text()))==clean(tree(new.read_text())))
 elif relative.endswith('3dmodels/MODEL-PROVENANCE.json'):
  before=json.loads(old.read_text());after=json.loads(new.read_text())
  check('All earlier provenance entries preserved '+relative,all(after['models'].get(k)==v for k,v in before['models'].items()))
 elif relative.endswith('3dmodels/README.md'):check('Prior model README retained '+relative,new.read_text().startswith(old.read_text()))
 else:check('Existing other file byte identical '+relative,old.read_bytes()==new.read_bytes())
 if args.saved:check('Saved file equals reviewed candidate '+relative,(WORK/relative).read_bytes()==new.read_bytes())
for relative,h in plan['new_files'].items():
 check('New file within project model folder '+relative,len(Path(relative).parts)>2 and Path(relative).parts[1]=='3dmodels')
 check('New asset/provenance hash '+relative,digest(TARGET/relative)==h)
 if args.saved:check('Saved new file equals candidate '+relative,digest(WORK/relative)==h)
expected={(r['board'],ref):r for r in plan['assignments'] for ref in r['references']};counts={};unassigned=[];policies={(r['board'],r['footprint']):r for r in plan['cache_policies']}
oldreasons={(r['board'],r['footprint']):r['reasons'] for r in json.loads((HERE.parent/'models-review-9/saved-model-audit.json').read_text())['unassigned']}
overrides={}
for filename in plan['review_manifests']:
 doc=json.loads((HERE/filename).read_text())
 for key in ['unsupported','unresolved','unassigned']:
  for r in doc.get(key,[]):
   for ref in r.get('references',r.get('refs',[])):overrides[(r.get('board',r.get('project')),ref)]=r.get('reason','No supported model established in current review.')
assets={}
for name in ['mainboard','ioboard']:
 project=TARGET/name;br=tree((project/(name+'.kicad_pcb')).read_text());before=tree((HERE/'input-snapshot'/name/(name+'.kicad_pcb')).read_text())
 original={property_value(f,'Reference','reference'):f for f in children(before,'footprint')};missing=collections.defaultdict(list);seen=set()
 for fp in children(br,'footprint'):
  ref=property_value(fp,'Reference','reference');fpname=fp[1].split(':')[-1];key=(name,ref);models=children(fp,'model');check('Exactly planned model presence '+name+'/'+ref,len(models)==(1 if key in expected else 0))
  oldmodels=children(original[ref],'model')
  updated={(row['board'],ref) for row in plan['updated_assignments'] for ref in row['references']}
  if oldmodels and key not in updated:check('Existing model nodes unchanged '+name+'/'+ref,models==oldmodels)
  elif oldmodels:
   before_model=values(oldmodels[0]);after_model=values(models[0]);row=expected[key];exception=row.get('reviewed_model_only_seating_change',False);check('Model transform unchanged or explicit reviewed KK1offset '+name+'/'+ref,all(before_model[k]==after_model[k] for k in ['scale','rotation']) and (before_model['offset']==after_model['offset'] if not exception else name=='ioboard' and ref=='KK1' and before_model['offset']==row['previous_offset_mm'] and after_model['offset']==row['offset_mm']))
  if not models:
   pads=children(fp,'pad');missing[fpname].append(dict(reference=ref,value=property_value(fp,'Value','value'),mechanical_only=bool(pads) and all(p[2]=='np_thru_hole' for p in pads)));continue
  seen.add(ref);r=expected[key];m=values(models[0]);wanted=dict(path='${KIPRJMOD}/3dmodels/'+r['local_model'],offset=r['offset_mm'],scale=r['scale'],rotation=r['rotation_deg'])
  check('Placed model transform '+name+'/'+ref,m==wanted);check('Unity scale '+name+'/'+ref,m['scale']==[1,1,1]);check('Project relative model path '+name+'/'+ref,m['path'].startswith('${KIPRJMOD}/3dmodels/'))
  asset=project/'3dmodels'/r['local_model'];check('Resolved local asset hash '+name+'/'+ref,asset.is_file() and digest(asset)==r['source_sha256']);check('Source model hash '+name+'/'+ref,digest(Path(r['source_model']))==r['source_sha256']);check('Model path contained in project '+name+'/'+ref,asset.resolve().is_relative_to(project.resolve()));assets[(name,r['local_model'])]=r['source_sha256']
  lib=tree((project/(name+'-import-fps.pretty')/(fpname+'.kicad_mod')).read_text());cache=children(lib,'model');policy=policies.get((name,fpname))
  if policy and not policy['cache_model_added']:check('Heterogeneous shared cache left unassigned '+name+'/'+ref,not cache)
  else:check('Placed/cache transform agreement '+name+'/'+ref,len(cache)==1 and values(cache[0])==m)
 check('Planned reference set '+name,seen=={ref for b,ref in expected if b==name})
 for fp,items in sorted(missing.items()):unassigned.append(dict(board=name,footprint=fp,references=[x['reference'] for x in items],values={x['reference']:x['value'] for x in items},instance_count=len(items),mechanical_only=all(x['mechanical_only'] for x in items),reasons=list(dict.fromkeys([overrides[(name,x['reference'])] for x in items if (name,x['reference']) in overrides])) or oldreasons.get((name,fp),['No supported body assignment.'])))
 counts[name]=dict(total_footprints=len(original),assigned_models=len(seen),unassigned_footprints=sum(len(v) for v in missing.values()),mechanical_hole_footprints=sum(x['mechanical_only'] for v in missing.values() for x in v))
report=dict(passed=not failures,check_count=len(checks),failure_count=len(failures),failures=failures,saved_projects_checked=args.saved,assigned_instance_count=len(expected),new_instance_count=plan['new_instance_count'],updated_instance_count=plan['updated_instance_count'],asset_count=len(assets),board_counts=counts,unassigned=unassigned,checks=checks,design_invariants='Every non-model PCB/library node unchanged. All schematics, symbol libraries and project settings byte unchanged. All previous model assets preserved; only reviewed model paths change, with unchanged scales/rotations and only an explicitly reviewed KK1model-only offset exception permitted. Shared footprints with different part bodies use explicit instance overrides.')
(HERE/('saved-model-audit.json' if args.saved else 'candidate-model-audit.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in {'checks','unassigned','design_invariants'}},indent=2));raise SystemExit(0 if report['passed'] else 1)
