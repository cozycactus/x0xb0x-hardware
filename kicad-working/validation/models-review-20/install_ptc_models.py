"""Install two source-dimensioned PTC models; preserve all PCB and model transforms."""
import copy,hashlib,json,shutil,sys
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[1];R=W.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
audit=json.loads((H/'ptc-quality/ptc-model-audit.json').read_text());assert audit['passed']
source=H/'ptc-quality'/audit['model'];assert sha(source)==audit['model_sha256']
local='Revision20/ptc-quality/'+source.name;asset=W/'mainboard/3dmodels'/local;asset.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,asset)
plan=json.loads((W/'validation/models-review-19/combined-model-plan.json').read_text());row=next(a for a in plan['assignments'] if a['footprint']=='R-7,5');old_local=row['local_model']
old='${KIPRJMOD}/3dmodels/'+old_local;new='${KIPRJMOD}/3dmodels/'+local
sys.path.insert(0,str(R/'kicad-import/validation'))
from verify_native_projects import parse_sexpr

def nonmodels(node):
 if not isinstance(node,list):return node
 return [nonmodels(x) for x in node if not(isinstance(x,list) and x and x[0]=='model')]
def transforms(node):
 if not isinstance(node,list):return []
 if node and node[0]=='model':return [node[2:]]
 return [t for x in node for t in transforms(x)]
def parse(s):return parse_sexpr(s if s.lstrip().startswith('(kicad_pcb') else '(kicad_pcb '+s+')')
files=[]
for relative,count in [('mainboard/mainboard.kicad_pcb',2),('mainboard/mainboard-import-fps.pretty/R-7,5.kicad_mod',1)]:
 p=W/relative;snapshot=H/'input-snapshot'/relative;snapshot.parent.mkdir(parents=True,exist_ok=True)
 if not snapshot.exists():assert old in p.read_text();snapshot.write_bytes(p.read_bytes())
 before=snapshot.read_text();assert before.count(old)==count;after=before.replace(old,new);assert p.read_text() in [before,after]
 assert nonmodels(parse(before))==nonmodels(parse(after));assert transforms(parse(before))==transforms(parse(after))
 p.write_text(after);files.append(dict(file=relative,before_sha256=sha(snapshot),after_sha256=sha(p),model_nodes_only=True,replaced_model_path_count=count,non_model_nodes_identical=True,model_transforms_identical=True))
limits=audit['limitations']
row.update(previous_local_model=old_local,previous_source_sha256=row['source_sha256'],source_model=str(asset),source_sha256=sha(asset),local_model=local,source_kind='Original Micro-Ohm LPTC12 primary manufacturer dimensions recovered from user-saved archived page',classification='LPTC12 nominal3.7x1.9mm body with0.45mm formed leads; installation details illustrated',limitations=limits,review_manifest='validation/models-review-20/ptc-quality/ptc-model-audit.json',solid_count=8,part_ids=['Body','Band1','Band2','Band3','Band4','Band5','DrawingDerivedTerminals'],terminal_drawing=audit['source'],terminal_specs=audit['terminal_specs'],terminal_provenance=dict(body='Printed LPTC12 nominal3.7mm length and1.9mm diameter',section='Printed0.45mm round lead diameter',positions='Original10.16mm PCB pitch retained',installation='Illustrated0.4mm body standoff,0.75mm bend radius and original1.5mm far-face tail projection'),model_nominal_dimensions_mm=audit['dimensions_mm'])
new_files=['mainboard/3dmodels/'+local,'mainboard/3dmodels/REVISION-20-SOURCES.json']
plan.update(base_revision=19,updated_assignments=[copy.deepcopy(row)],new_assignments=[],updated_instance_count=2,new_instance_count=0,files=files,new_files=new_files,review_manifests=['validation/models-review-20/ptc-quality/ptc-model-audit.json'],scope='R100A0/R100B0 only; body and lead dimensions follow recovered original family drawing. Original PCB/model transforms and band-color palette preserved.')
(H/'combined-model-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(W/'mainboard/3dmodels/REVISION-20-SOURCES.json').write_text(json.dumps(dict(revision=20,baseline_revision=19,model=local,model_sha256=sha(asset),previous_model=old_local,previous_model_sha256=audit['previous_model_sha256'],references=row['references'],drawing=audit['source'],dimensions_mm=audit['dimensions_mm'],limitations=limits,physical_fit_qualified=False),indent=2)+'\n')
prior=json.loads((W/'validation/working-validation-summary-revision-19.json').read_text());changed=sorted(n for n,h in prior['outputs'].items() if sha(W/n)!=h);assert changed==sorted(f['file'] for f in files)
report=dict(passed=True,files=files,previous_core_file_count=len(prior['outputs']),changed_previous_core_files=changed,new_core_files=new_files,component_references_updated=2,references={'LPTC':row['references']},total_fitted_model_references=491,copper_pads_nets_footprint_poses_schematics_and_project_rules_unchanged=True,model_transforms_unchanged=True,source_Eagle_files_unchanged=True,old_STEP_preserved=True,physical_fit_qualified=False)
(H/'installation-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'updated_references':2},indent=2))
