"""Install STD240B spacer compound models while preserving original LED poses."""
import copy,hashlib,json,shutil,sys
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[1];R=W.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
audit=json.loads((H/'led-spacer-quality/installed-spacer-audit.json').read_text());assert audit['passed']
source=H/'led-spacer-quality'/audit['model'];assert sha(source)==audit['model_sha256']
local='Revision19/led-spacer-quality/'+source.name;asset=W/'mainboard/3dmodels'/local;asset.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,asset)
plan=json.loads((W/'validation/models-review-18/combined-model-plan.json').read_text());row=next(a for a in plan['assignments'] if a['footprint']=='LED5MM');old_local=row['local_model']
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
for relative,count in [('mainboard/mainboard.kicad_pcb',40),('mainboard/mainboard-import-fps.pretty/LED5MM.kicad_mod',1)]:
 p=W/relative;snapshot=H/'input-snapshot'/relative;snapshot.parent.mkdir(parents=True,exist_ok=True)
 if not snapshot.exists():assert old in p.read_text();snapshot.write_bytes(p.read_bytes())
 before=snapshot.read_text();assert before.count(old)==count;after=before.replace(old,new);assert p.read_text() in [before,after]
 assert nonmodels(parse(before))==nonmodels(parse(after));assert transforms(parse(before))==transforms(parse(after))
 p.write_text(after);files.append(dict(file=relative,before_sha256=sha(snapshot),after_sha256=sha(p),model_nodes_only=True,replaced_model_path_count=count,non_model_nodes_identical=True,model_transforms_identical=True))
limits=audit['limitations']+['Original lens, two leads, optical appearance roles and model transforms retained exactly; added black spacer occupies the existing6.096mm seating gap.']
row.update(previous_local_model=old_local,previous_source_sha256=row['source_sha256'],source_model=str(asset),source_sha256=sha(asset),local_model=local,source_kind='Retained generic KiCad LED plus VCC STDxxxBLK_A rev001 drawing-derived spacer',classification='Installed generic LED with STD240B spacer; detailed retention features illustrative',limitations=limits,review_manifest='validation/models-review-19/led-spacer-quality/installed-spacer-audit.json',solid_count=4,part_ids=['ClearLensBody','CathodeFullWidthLead','AnodeFullWidthLead','BlackSTD240BSpacer'])
new_files=['mainboard/3dmodels/'+local,'mainboard/3dmodels/REVISION-19-SOURCES.json']
plan.update(base_revision=18,updated_assignments=[copy.deepcopy(row)],new_assignments=[],updated_instance_count=40,new_instance_count=0,files=files,new_files=new_files,review_manifests=['validation/models-review-19/led-spacer-quality/installed-spacer-audit.json'],scope='40 LED compound models add spacer solids; original LED geometry and every model transform preserved.')
(H/'combined-model-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(W/'mainboard/3dmodels/REVISION-19-SOURCES.json').write_text(json.dumps(dict(revision=19,baseline_revision=18,model=local,model_sha256=sha(asset),previous_model=old_local,previous_model_sha256=audit['previous_model_sha256'],references=row['references'],drawing=audit['source'],catalog=audit['catalog'],datum_resolution=audit['datum_resolution'],limitations=limits,physical_fit_qualified=False),indent=2)+'\n')
prior=json.loads((W/'validation/working-validation-summary-revision-18.json').read_text());changed=sorted(n for n,h in prior['outputs'].items() if sha(W/n)!=h);assert changed==sorted(f['file'] for f in files)
report=dict(passed=True,files=files,previous_core_file_count=len(prior['outputs']),changed_previous_core_files=changed,new_core_files=new_files,component_references_updated=40,references={'LED':row['references']},total_fitted_model_references=491,copper_pads_nets_footprint_poses_schematics_and_project_rules_unchanged=True,model_transforms_unchanged=True,source_Eagle_files_unchanged=True,old_STEP_preserved=True,physical_fit_qualified=False)
(H/'installation-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'updated_references':40},indent=2))
