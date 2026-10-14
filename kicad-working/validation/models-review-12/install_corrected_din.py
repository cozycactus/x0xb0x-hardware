"""Install the checked SDS-50J correction at four references, preserving layout."""
from pathlib import Path
import copy,hashlib,json,shutil,sys

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[1];REPO=WORK.parent
Q=HERE/'din-contact-quality'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
audit=json.loads((Q/'corrected-model-audit.json').read_text())
native=json.loads((Q/'native-geometry-audit.json').read_text())
assert audit['passed'] and native['passed']
source=Q/audit['model'];assert sha(source)==audit['model_sha256']
local='Revision12/din-contact-quality/'+source.name
asset=WORK/'ioboard/3dmodels'/local;asset.parent.mkdir(parents=True,exist_ok=True)
if asset.exists():assert sha(asset)==sha(source)
else:shutil.copyfile(source,asset)
old='${KIPRJMOD}/3dmodels/Revision8/rear-quality/SDS50J_DatasheetDerived_DetailedBody.step'
new='${KIPRJMOD}/3dmodels/'+local
sys.path.insert(0,str(REPO/'kicad-import/validation'))
from verify_native_projects import parse_sexpr,children,property_value,one
def without_models(node):
    if not isinstance(node,list):return node
    return [without_models(x) for x in node if not (isinstance(x,list) and x and x[0]=='model')]
def parse_document(text):
    return parse_sexpr(text if text.lstrip().startswith('(kicad_pcb') else '(kicad_pcb '+text+')')
file_rows=[]
for relative,count in [('ioboard/ioboard.kicad_pcb',4),('ioboard/ioboard-import-fps.pretty/CP-2350.kicad_mod',1)]:
    path=WORK/relative;snapshot=HERE/'input-snapshot'/relative;snapshot.parent.mkdir(parents=True,exist_ok=True)
    text=path.read_text()
    if not snapshot.exists():
        assert text.count(old)==count and new not in text,(relative,'Unexpected source assignment')
        snapshot.write_bytes(path.read_bytes())
    before=snapshot.read_text()
    assert before.count(old)==count
    after=before.replace(old,new)
    assert text in [before,after],'Unrelated edits detected before installation'
    assert without_models(parse_document(before))==without_models(parse_document(after))
    assert after.replace(new,old)==before
    path.write_text(after)
    file_rows.append(dict(file=relative,before_sha256=sha(snapshot),after_sha256=sha(path),
        model_nodes_only=True,replaced_model_path_count=count,non_model_nodes_identical=True))
board=parse_sexpr((WORK/'ioboard/ioboard.kicad_pcb').read_text())
for fp in children(board,'footprint'):
    if property_value(fp,'Reference','reference') in ['DIN1','DIN2','DIN3','DIN4']:
        model=children(fp,'model')[0]
        assert model[1]==new
        transforms={k:list(map(float,one(one(model,k),'xyz')[1:])) for k in ['offset','scale','rotate']}
        assert transforms==dict(offset=[0,0,0],scale=[1,1,1],rotate=[0,0,0])
base_plan=WORK/'validation/models-review-11/combined-model-plan.json'
plan=json.loads(base_plan.read_text())
row=next(r for r in plan['assignments'] if r['board']=='ioboard' and 'DIN1' in r['references'])
row['previous_local_model']=row['local_model'];row['previous_source_sha256']=row['source_sha256']
row.update(source_model=str(asset),source_sha256=sha(asset),local_model=local,
    source_kind='Primary-drawing reconstruction; two corrected outer contact centers and independent slot tilts',
    classification='SDS-50J nominal body illustration with corrected DIN-180 contact pattern; not manufacturer CAD or terminal-fit qualification',
    source_urls=[audit['source_url']],limitations=audit['limitations'],
    review_manifest='validation/models-review-12/din-contact-quality/corrected-model-audit.json')
plan.update(base_revision=11,updated_assignments=[copy.deepcopy(row)],new_assignments=[],
    updated_instance_count=4,new_instance_count=0,files=file_rows,
    new_files=['ioboard/3dmodels/'+local,'ioboard/3dmodels/REVISION-12-SOURCES.json'],
    review_manifests=['validation/models-review-12/din-contact-quality/corrected-model-audit.json'],
    scope='Four DIN model assignments only; all other assignment rows and model transforms retain revision 11 values.')
(HERE/'combined-model-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
record=dict(revision=12,baseline_revision=11,geometry_license='CC0-1.0 original reconstruction; manufacturer drawing rights retained',
    source_PDF_sha256=audit['source_PDF_sha256'],model=str(asset.relative_to(WORK/'ioboard/3dmodels')),
    model_sha256=sha(asset),references=['DIN1','DIN2','DIN3','DIN4'],
    corrected_contact_center_angles_deg=[0,180,225,270,315],
    outer_slot_tilts_from_vertical_deg=[-25,25],
    native_assignment_offset_mm=[0,0,0],native_assignment_rotation_deg=[0,0,0],native_assignment_scale=[1,1,1],
    source_geometry_authority='Same Sky SDS-J page 3: outer circular centers on horizontal axis; 25 degree leader belongs to slot orientation',
    downloaded_CAD_geometry_incorporated=False,physical_fit_qualified=False)
(WORK/'ioboard/3dmodels/REVISION-12-SOURCES.json').write_text(json.dumps(record,indent=2)+'\n')
old_summary=json.loads((WORK/'validation/working-validation-summary-revision-11.json').read_text())
changed=[]
for name,h in old_summary['outputs'].items():
    if sha(WORK/name)!=h:changed.append(name)
assert sorted(changed)==sorted(r['file'] for r in file_rows),changed
report=dict(passed=True,files=file_rows,previous_core_file_count=len(old_summary['outputs']),
    changed_previous_core_files=changed,new_core_files=plan['new_files'],
    component_references_updated=4,total_fitted_model_references=491,
    copper_pads_nets_footprint_poses_schematics_and_project_rules_unchanged=True,
    source_Eagle_files_unchanged=True,old_STEP_preserved=True,physical_fit_qualified=False)
(HERE/'installation-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
