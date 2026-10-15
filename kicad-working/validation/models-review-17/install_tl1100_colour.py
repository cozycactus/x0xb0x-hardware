"""Install the recoloured TL1100F model at its 23 references, preserving layout.

Only the 23 embedded PCB model paths and the B3F-40XX footprint-cache model path
change; every non-model S-expression node and every model transform is verified
identical. The revision-8 STEP remains in place.
"""
from pathlib import Path
import copy, hashlib, json, sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]; REPO = WORK.parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
audit = json.loads((HERE / 'tl1100-colour/tl1100-colour-audit.json').read_text())
assert audit['passed'] and not audit['geometry_changed']
asset = WORK / audit['output']
assert sha(asset) == audit['output_sha256']
sys.path.insert(0, str(REPO / 'kicad-import/validation'))
from verify_native_projects import parse_sexpr, children, property_value  # noqa: E402
OLD_LOCAL = audit['source'].split('/3dmodels/', 1)[1]
NEW_LOCAL = audit['output'].split('/3dmodels/', 1)[1]
OLD, NEW = '${KIPRJMOD}/3dmodels/' + OLD_LOCAL, '${KIPRJMOD}/3dmodels/' + NEW_LOCAL


def without_models(node):
    if not isinstance(node, list): return node
    return [without_models(x) for x in node if not (isinstance(x, list) and x and x[0] == 'model')]


def models_without_path(node, out):
    if isinstance(node, list):
        if node and node[0] == 'model': out.append(node[2:])
        else:
            for x in node: models_without_path(x, out)
    return out


def parse_document(text):
    return parse_sexpr(text if text.lstrip().startswith('(kicad_pcb') else '(kicad_pcb ' + text + ')')


rows = []
for relative, count in (('mainboard/mainboard.kicad_pcb', 23), ('mainboard/mainboard-import-fps.pretty/B3F-40XX.kicad_mod', 1)):
    path = WORK / relative; snapshot = HERE / 'input-snapshot' / relative
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    if not snapshot.exists():
        assert NEW not in path.read_text()
        snapshot.write_bytes(path.read_bytes())
    before = snapshot.read_text()
    assert before.count(OLD) == count
    after = before.replace(OLD, NEW)
    assert path.read_text() in (before, after), 'Unrelated edits detected before installation'
    assert without_models(parse_document(before)) == without_models(parse_document(after))
    assert models_without_path(parse_document(before), []) == models_without_path(parse_document(after), [])
    assert after.replace(NEW, OLD) == before
    path.write_text(after)
    rows.append(dict(file=relative, before_sha256=sha(snapshot), after_sha256=sha(path), model_nodes_only=True,
                     replaced_model_path_count=count, non_model_nodes_identical=True, model_transforms_identical=True))
tree = parse_sexpr((WORK / 'mainboard/mainboard.kicad_pcb').read_text())
refs = sorted(property_value(fp, 'Reference', 'reference') for fp in children(tree, 'footprint')
              if NEW in [m[1] for m in children(fp, 'model')])
assert len(refs) == 23
plan = json.loads((WORK / 'validation/models-review-16/combined-model-plan.json').read_text())
match = [r for r in plan['assignments'] if r['board'] == 'mainboard' and r['local_model'] == OLD_LOCAL]
assert len(match) == 1 and sorted(match[0]['references']) == refs
row = match[0]
row['previous_local_model'] = row['local_model']; row['previous_source_sha256'] = row['source_sha256']
row.update(source_model=str(asset), source_sha256=sha(asset), local_model=NEW_LOCAL,
           source_kind=row.get('source_kind', '') + '; leg faces outside the housing recoloured as terminal metal (revision 17), geometry unchanged',
           review_manifest='validation/models-review-17/tl1100-colour/tl1100-colour-audit.json')
new_files = ['mainboard/3dmodels/' + NEW_LOCAL, 'mainboard/3dmodels/REVISION-17-SOURCES.json']
plan.update(base_revision=16, updated_assignments=[copy.deepcopy(row)], new_assignments=[], updated_instance_count=23,
            new_instance_count=0, files=rows, new_files=new_files,
            review_manifests=['validation/models-review-17/tl1100-colour/tl1100-colour-audit.json'],
            scope='One model assignment at 23 references (colour only); all other rows and every transform retain revision 16 values.')
(HERE / 'combined-model-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
(WORK / 'mainboard/3dmodels/REVISION-17-SOURCES.json').write_text(json.dumps(dict(
    revision=17, baseline_revision=16, model=NEW_LOCAL, model_sha256=sha(asset), previous_model=OLD_LOCAL,
    previous_model_sha256=audit['source_sha256'], references=refs, change='24 leg faces recoloured from housing to terminal metal; B-rep identical',
    native_assignment_transforms='unchanged from revision 16', physical_fit_qualified=False), indent=2) + '\n')
old_summary = json.loads((WORK / 'validation/working-validation-summary-revision-16.json').read_text())
changed = sorted(n for n, h in old_summary['outputs'].items() if sha(WORK / n) != h)
assert changed == sorted(r['file'] for r in rows), changed
report = dict(passed=True, files=rows, previous_core_file_count=len(old_summary['outputs']), changed_previous_core_files=changed,
              new_core_files=new_files, component_references_updated=23, references={'TL1100F': refs},
              total_fitted_model_references=491, copper_pads_nets_footprint_poses_schematics_and_project_rules_unchanged=True,
              model_transforms_unchanged=True, source_Eagle_files_unchanged=True, old_STEP_preserved=True,
              geometry_changed=False, physical_fit_qualified=False)
(HERE / 'installation-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('passed', 'changed_previous_core_files', 'component_references_updated')}, indent=2))
