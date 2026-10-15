"""Install the banded DIN0207 resistor models per reference; preserve every PCB node and transform.

Each of the 212 fixed resistors gets the model of its own band variant. Only model
path strings change in the two PCB files; the shared 0207 footprint caches keep the
unbanded KiCad body (one cache serves many values), and every model transform is
checked identical.

Run from the repository root:
  python3 -I kicad-working/validation/models-review-22/install_resistor_models.py
"""
import copy
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
W = H.parents[1]
R = W.parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
sys.dont_write_bytecode = True
sys.path.insert(0, str(R / 'kicad-import/validation'))
from verify_native_projects import parse_sexpr  # noqa: E402

Q = H / 'resistor-quality'
audit = json.loads((Q / 'resistor-model-audit.json').read_text())
bands = json.loads((Q / 'sources/resistor-band-assignments.json').read_text())
assert audit['passed'] and bands['passed']
P = '${KIPRJMOD}/3dmodels/'
LOCAL = 'Revision22/resistor-quality/'
by_ref, new_files = {}, []
for name, m in audit['models'].items():
    assert sha(Q / m['output']) == m['output_sha256']
    boards = sorted({r.split(':')[0] for r in m['references']})
    for board in boards:
        dest = W / board / '3dmodels' / LOCAL / m['output']
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Q / m['output'], dest)
        new_files.append(f'{board}/3dmodels/{LOCAL}{m["output"]}')
    for item in m['references']:
        board, ref = item.split(':')
        by_ref[(board, ref)] = (P + m['source_model'], P + LOCAL + m['output'])
assert len(by_ref) == 212


def nonmodels(node):
    if not isinstance(node, list):
        return node
    return [nonmodels(x) for x in node if not (isinstance(x, list) and x and x[0] == 'model')]


def transforms(node):
    if not isinstance(node, list):
        return []
    if node and node[0] == 'model':
        return [node[2:]]
    return [t for x in node for t in transforms(x)]


files = []
for board in ('mainboard', 'ioboard'):
    relative = f'{board}/{board}.kicad_pcb'
    p = W / relative
    snapshot = H / 'input-snapshot' / relative
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    if not snapshot.exists():
        snapshot.write_bytes(p.read_bytes())
    before = snapshot.read_text()
    pieces, count = [], 0
    for piece in re.split(r'(?=\n\t\(footprint )', before):
        ref = re.search(r'\(property "Reference" "([^"]*)"', piece)
        key = (board, ref.group(1)) if ref else None
        if key in by_ref:
            old, new = by_ref[key]
            assert piece.count(f'(model "{old}"') == 1, key
            piece = piece.replace(f'(model "{old}"', f'(model "{new}"')
            count += 1
        pieces.append(piece)
    after = ''.join(pieces)
    expected = sum(1 for b, _ in by_ref if b == board)
    assert count == expected, (board, count)
    assert p.read_text() in (before, after)
    tb, ta = parse_sexpr(before), parse_sexpr(after)
    assert nonmodels(tb) == nonmodels(ta) and transforms(tb) == transforms(ta)
    p.write_text(after)
    files.append(dict(file=relative, before_sha256=sha(snapshot), after_sha256=sha(p), model_nodes_only=True,
                      replaced_model_path_count=count, non_model_nodes_identical=True, model_transforms_identical=True))

plan = json.loads((W / 'validation/models-review-21/combined-model-plan.json').read_text())
rows, updated = plan['assignments'], []
old_rows = [a for a in rows if a['footprint'].startswith('0207_')]
assert sum(len(a['references']) for a in old_rows) == 212
SOURCES = [bands['parts_page']['url'], bands['photos']['source']]
for old in old_rows:
    index = rows.index(old)
    rows.remove(old)
    groups = {}
    for ref in old['references']:
        groups.setdefault(by_ref[(old['board'], ref)][1], []).append(ref)
    for offset, (path, refs) in enumerate(sorted(groups.items())):
        local = path[len(P):]
        m = next(v for v in audit['models'].values() if v['output'] == Path(local).name)
        row = copy.deepcopy(old)
        row.update(references=sorted(refs), previous_local_model=old['local_model'], previous_source_sha256=old['source_sha256'],
                   source_model=str(W / old['board'] / '3dmodels' / local), source_sha256=sha(W / old['board'] / '3dmodels' / local),
                   local_model=local, classification='KiCad DIN0207 body and leads unchanged; original-kit colour bands',
                   source_kind='Installed KiCad DIN0207 STEP split into body, leads and flush band rings',
                   limitations=audit['limitations'], review_manifest='validation/models-review-22/resistor-quality/resistor-model-audit.json',
                   source_urls=SOURCES, bands=m['bands'], tolerance=m['tolerance'], part_count=m['part_count'],
                   values={r: bands['assignments'][r]['ohms'] for r in sorted(refs)})
        rows.insert(index + offset, row)
        updated.append(copy.deepcopy(row))
assert sum(len(a['references']) for a in rows) == plan['assigned_instance_count'] == 491
for board, footprint in sorted({(a['board'], a['footprint']) for a in old_rows}):
    plan['cache_policies'].append(dict(board=board, footprint=footprint,
                                       references=sorted(r for a in old_rows if a['board'] == board and a['footprint'] == footprint for r in a['references']),
                                       cache_model_added=False,
                                       reason='Footprint cache keeps the unbanded KiCad DIN0207 model; placed instances carry value-specific banded overrides.'))
sources_files = []
for board in ('mainboard', 'ioboard'):
    record = dict(revision=22, baseline_revision=21,
                  models={Path(f).name: dict(local_model=f.split('/3dmodels/')[1], sha256=sha(W / f)) for f in new_files if f.startswith(board)},
                  references={a['local_model'].split('/')[-1]: a['references'] for a in updated if a['board'] == board},
                  band_assignments='validation/models-review-22/resistor-quality/sources/resistor-band-assignments.json',
                  limitations=audit['limitations'], physical_fit_qualified=False)
    path = W / board / '3dmodels/REVISION-22-SOURCES.json'
    path.write_text(json.dumps(record, indent=2) + '\n')
    sources_files.append(f'{board}/3dmodels/REVISION-22-SOURCES.json')
new_files += sources_files
plan.update(base_revision=21, updated_assignments=updated, new_assignments=[], updated_instance_count=212, new_instance_count=0,
            files=files, new_files=new_files, model_transform_exceptions=[],
            review_manifests=['validation/models-review-22/resistor-quality/resistor-model-audit.json'],
            scope='212 fixed resistors keep the installed KiCad DIN0207 geometry with flush original-kit colour bands '
                  '(tan 5%, light-blue 1%). Footprint caches, PCB values and model transforms unchanged.')
(H / 'combined-model-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
prior = json.loads((W / 'validation/working-validation-summary-revision-21.json').read_text())
changed = sorted(n for n, h in prior['outputs'].items() if sha(W / n) != h)
assert changed == sorted(f['file'] for f in files), changed
report = dict(passed=True, files=files, previous_core_file_count=len(prior['outputs']), changed_previous_core_files=changed,
              new_core_files=new_files, component_references_updated=len(by_ref),
              references={a['board'] + ':' + a['local_model'].split('/')[-1]: a['references'] for a in updated},
              total_fitted_model_references=491, footprint_caches_unchanged=True,
              copper_pads_nets_footprint_poses_schematics_and_project_rules_unchanged=True, model_transforms_unchanged=True,
              source_Eagle_files_unchanged=True, old_STEP_preserved=True, physical_fit_qualified=False)
(H / 'installation-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': True, 'updated_references': len(by_ref), 'changed_files': changed, 'new_files': len(new_files)}, indent=2))
