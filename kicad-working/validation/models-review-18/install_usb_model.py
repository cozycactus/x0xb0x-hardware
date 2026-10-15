"""Install one corrected USB STEP at USB0; preserve all non-model data."""
import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[1]; REPO=WORK.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
audit=json.loads((HERE/'usb-quality/usb-model-audit.json').read_text())
assert audit['passed']
source=HERE/'usb-quality'/audit['model']
assert sha(source)==audit['model_sha256']
local='Revision18/usb-quality/'+source.name
asset=WORK/'ioboard/3dmodels'/local
asset.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(source,asset)
old_local=audit['source'].split('/3dmodels/',1)[1]
old='${KIPRJMOD}/3dmodels/'+old_local
new='${KIPRJMOD}/3dmodels/'+local
sys.path.insert(0,str(REPO/'kicad-import/validation'))
from verify_native_projects import parse_sexpr
def nonmodels(node):
    if not isinstance(node,list):return node
    return [nonmodels(x) for x in node if not (isinstance(x,list) and x and x[0]=='model')]
def transforms(node):
    if not isinstance(node,list):return []
    if node and node[0]=='model':return [node[2:]]
    return [t for x in node for t in transforms(x)]
def parse(text):return parse_sexpr(text if text.lstrip().startswith('(kicad_pcb') else '(kicad_pcb '+text+')')
files=[]
for relative in ['ioboard/ioboard.kicad_pcb','ioboard/ioboard-import-fps.pretty/PN61729.kicad_mod']:
    target=WORK/relative;snapshot=HERE/'input-snapshot'/relative
    snapshot.parent.mkdir(parents=True,exist_ok=True)
    if not snapshot.exists():
        assert new not in target.read_text()
        snapshot.write_bytes(target.read_bytes())
    before=snapshot.read_text();assert before.count(old)==1
    after=before.replace(old,new);assert target.read_text() in (before,after)
    assert nonmodels(parse(before))==nonmodels(parse(after))
    assert transforms(parse(before))==transforms(parse(after))
    target.write_text(after)
    files.append(dict(file=relative,before_sha256=sha(snapshot),after_sha256=sha(target),model_nodes_only=True,replaced_model_path_count=1,non_model_nodes_identical=True,model_transforms_identical=True))
plan=json.loads((WORK/'validation/models-review-17/combined-model-plan.json').read_text())
row=next(r for r in plan['assignments'] if r['board']=='ioboard' and r['references']==['USB0'])
assert row['local_model']==old_local
row.update(previous_local_model=old_local,previous_source_sha256=row['source_sha256'],
 source_model=str(asset),source_sha256=sha(asset),local_model=local,
 source_kind='BOM Kobiconn2006 primary drawing; corrected body-to-PCB gap and terminal projections, insulated signal exits and illustrative mating strips',
 classification='Kobiconn154-2442-E drawing-derived connector illustration; physical fitted variant unverified',
 limitations=audit['limitations'],review_manifest='validation/models-review-18/usb-quality/usb-model-audit.json',
 part_ids=['Shell','Insulator','DrawingDerivedTerminals','MatingContacts'],solid_count=12,
 terminal_drawing=audit['drawing'],terminal_provenance=dict(positions='Existing printed10.28/12.99/14.99mm row positions retained',
 length='Kobiconn KC-301021: signal2.91mm, board locks3.72mm below PCB',body_gap='Printed0.38mm above PCB',
 section='Stock0.40mm square and board-lock dimensions remain illustrative; not derived from the standoff dimension.'))
new_files=['ioboard/3dmodels/'+local,'ioboard/3dmodels/REVISION-18-SOURCES.json']
plan.update(base_revision=17,updated_assignments=[copy.deepcopy(row)],new_assignments=[],updated_instance_count=1,new_instance_count=0,files=files,new_files=new_files,
 review_manifests=['validation/models-review-18/usb-quality/usb-model-audit.json'],scope='USB0 only; two model paths, all transforms and every other assignment retained.')
(HERE/'combined-model-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(WORK/'ioboard/3dmodels/REVISION-18-SOURCES.json').write_text(json.dumps(dict(revision=18,baseline_revision=17,model=local,model_sha256=sha(asset),previous_model=old_local,previous_model_sha256=audit['source_sha256'],references=['USB0'],drawing=audit['drawing'],change='BOM-specific standoff/projections and insulated signal exits; illustrative gold mating strips',limitations=audit['limitations'],native_assignment_transforms='unchanged',physical_fit_qualified=False),indent=2)+'\n')
prior=json.loads((WORK/'validation/working-validation-summary-revision-17.json').read_text())
changed=sorted(n for n,h in prior['outputs'].items() if sha(WORK/n)!=h)
assert changed==sorted(f['file'] for f in files)
report=dict(passed=True,files=files,previous_core_file_count=len(prior['outputs']),changed_previous_core_files=changed,new_core_files=new_files,component_references_updated=1,references={'USB':['USB0']},total_fitted_model_references=491,
 copper_pads_nets_footprint_poses_schematics_and_project_rules_unchanged=True,model_transforms_unchanged=True,source_Eagle_files_unchanged=True,old_STEP_preserved=True,physical_fit_qualified=False)
(HERE/'installation-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
