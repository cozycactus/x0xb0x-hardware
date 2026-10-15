"""Install the revision-16 Grayhill 25L model (rebuilt body) at S3 and S4, preserving layout.

Only embedded PCB model paths and the matching footprint-cache model paths change.
Every non-model S-expression node is verified identical and every model transform
is retained. Older STEP files remain in place.
"""
from pathlib import Path
import copy, hashlib, json, sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]; REPO = WORK.parent
Q = HERE / 'terminal-quality'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
audit = json.loads((Q / 'terminal-model-audit.json').read_text())
assert audit['passed']
sys.path.insert(0, str(Q))
from terminal_spec import CHANGED, MODELS  # noqa: E402
sys.path.insert(0, str(REPO / 'kicad-import/validation'))
from verify_native_projects import parse_sexpr, children, property_value  # noqa: E402

LIBRARY = {'NYS216': 'REAN_1_4STERO', 'SDS50J': 'CP-2350', 'MJ3536N': 'MJ-3536N', 'PJ202AH': 'PJ-202AH',
           'USB': 'PN61729', 'MC78M05': '78XXS', 'LPTC': 'R-7,5', 'CTS290': 'PEC11-S',
           'AlphaRV112': 'ALPHADUAL', 'PanasonicEVU': 'EVU', 'NKKB12AB': 'NKKTOGGLE', 'Grayhill25L': 'GH3074'}
PREFIX = '${KIPRJMOD}/3dmodels/'


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


previous = json.loads((HERE.parent / 'models-review-13/terminal-quality/terminal-model-audit.json').read_text())
for r in (14, 15):
    previous['models'].update(json.loads((HERE.parent / f'models-review-{r}/terminal-quality/terminal-model-audit.json').read_text())['models'])
swaps = {}
for key in CHANGED:
    spec = MODELS[key]
    row = audit['models'][key]
    asset = WORK / row['output']
    assert sha(asset) == row['output_sha256'], key
    old_local = previous['models'][key]['output'].split('/3dmodels/', 1)[1]
    new_local = row['output'].split('/3dmodels/', 1)[1]
    swaps[key] = dict(board=spec['board'], old=PREFIX + old_local, new=PREFIX + new_local,
                      old_local=old_local, new_local=new_local, asset=asset)

file_rows = []
targets = {}
for key, s in swaps.items():
    targets.setdefault(f"{s['board']}/{s['board']}.kicad_pcb", []).append(key)
    targets.setdefault(f"{s['board']}/{s['board']}-import-fps.pretty/{LIBRARY[key]}.kicad_mod", []).append(key)
for relative, keys in targets.items():
    path = WORK / relative; snapshot = HERE / 'input-snapshot' / relative
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    if not snapshot.exists():
        text = path.read_text()
        assert all(swaps[k]['new'] not in text for k in keys), (relative, 'Unexpected source assignment')
        snapshot.write_bytes(path.read_bytes())
    before = snapshot.read_text(); after = before
    counts = {}
    for k in keys:
        counts[k] = before.count(swaps[k]['old'])
        assert counts[k] >= 1
        after = after.replace(swaps[k]['old'], swaps[k]['new'])
    assert path.read_text() in [before, after], 'Unrelated edits detected before installation'
    parsed_before, parsed_after = parse_document(before), parse_document(after)
    assert without_models(parsed_before) == without_models(parsed_after)
    assert models_without_path(parsed_before, []) == models_without_path(parsed_after, [])
    restored = after
    for k in keys: restored = restored.replace(swaps[k]['new'], swaps[k]['old'])
    assert restored == before
    path.write_text(after)
    file_rows.append(dict(file=relative, before_sha256=sha(snapshot), after_sha256=sha(path),
                          model_nodes_only=True, replaced_model_path_count=sum(counts.values()),
                          replaced_models={k: counts[k] for k in keys},
                          non_model_nodes_identical=True, model_transforms_identical=True))

references = {}
for board in ('ioboard', 'mainboard'):
    tree = parse_sexpr((WORK / board / f'{board}.kicad_pcb').read_text())
    for fp in children(tree, 'footprint'):
        paths = [m[1] for m in children(fp, 'model')]
        for key, s in swaps.items():
            assert s['old'] not in paths
            if s['new'] in paths:
                references.setdefault(key, []).append(property_value(fp, 'Reference', 'reference'))
assert sum(map(len, references.values())) == 2, references

plan = json.loads((WORK / 'validation/models-review-15/combined-model-plan.json').read_text())
updated = []
for key, s in swaps.items():
    rows = [r for r in plan['assignments'] if r['board'] == s['board'] and r['local_model'] == s['old_local']]
    assert len(rows) == 1 and sorted(rows[0]['references']) == sorted(references[key]), key
    row = rows[0]; spec = MODELS[key]
    row['previous_local_model'] = row['local_model']; row['previous_source_sha256'] = row['source_sha256']
    row.update(source_model=str(s['asset']), source_sha256=sha(s['asset']), local_model=s['new_local'],
               source_kind='Body rebuilt from the Series 25L drawing and a product photograph; printed dimensions and pins kept',
               classification='Grayhill 25LB22-H drawing-and-photo reconstruction: round drum top, lock lugs, 8-4-2-1-C label band, green output board with solder joints; not manufacturer CAD, not fit qualified',
               terminal_provenance=spec['provenance'], terminal_drawing=spec['drawing'],
               review_manifest='validation/models-review-16/grayhill-quality/grayhill-model-audit.json')
    updated.append(copy.deepcopy(row))
new_files = sorted(f"{s['board']}/3dmodels/{s['new_local']}" for s in swaps.values()) + [
    'mainboard/3dmodels/REVISION-16-SOURCES.json']
plan.update(base_revision=15, updated_assignments=updated, new_assignments=[], updated_instance_count=2,
            new_instance_count=0, files=file_rows, new_files=new_files,
            review_manifests=['validation/models-review-16/grayhill-quality/grayhill-model-audit.json',
                              'validation/models-review-16/terminal-quality/terminal-model-audit.json',
                              'validation/models-review-16/terminal-quality/terminal-join-audit.json'],
            scope='One model assignment at 2 references; all other assignment rows and every model transform '
                  'retain revision 15 values.')
(HERE / 'combined-model-plan.json').write_text(json.dumps(plan, indent=2) + '\n')

for board in ('mainboard',):
    rows = []
    for key, s in swaps.items():
        if s['board'] != board: continue
        m = audit['models'][key]
        rows.append(dict(key=key, references=sorted(references[key]), previous_model=s['old_local'],
                         previous_model_sha256=previous['models'][key]['output_sha256'], model=s['new_local'], model_sha256=m['output_sha256'],
                         original_solids_retained=m['original_solids'], terminal_solids=m['terminal_solids'],
                         drawing=MODELS[key]['drawing'], provenance=MODELS[key]['provenance']))
    record = dict(revision=16, baseline_revision=15,
                  geometry_license='CC0-1.0 original reconstruction; manufacturer drawing rights retained',
                  models=rows, native_assignment_transforms='unchanged from revision 15',
                  terminal_positions='Drawing dimensions in each model frame; never moved to PCB pads',
                  downloaded_CAD_geometry_incorporated=False, physical_fit_qualified=False)
    (WORK / board / '3dmodels/REVISION-16-SOURCES.json').write_text(json.dumps(record, indent=2) + '\n')

old_summary = json.loads((WORK / 'validation/working-validation-summary-revision-15.json').read_text())
changed = sorted(n for n, h in old_summary['outputs'].items() if sha(WORK / n) != h)
assert changed == sorted(r['file'] for r in file_rows), changed
report = dict(passed=True, files=file_rows, previous_core_file_count=len(old_summary['outputs']),
              changed_previous_core_files=changed, new_core_files=new_files,
              component_references_updated=2, references={k: sorted(v) for k, v in references.items()},
              total_fitted_model_references=491,
              copper_pads_nets_footprint_poses_schematics_and_project_rules_unchanged=True,
              model_transforms_unchanged=True, source_Eagle_files_unchanged=True, old_STEP_preserved=True,
              physical_fit_qualified=False)
(HERE / 'installation-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('passed', 'changed_previous_core_files', 'component_references_updated')},
                 indent=2))
